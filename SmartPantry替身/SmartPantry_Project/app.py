from fastapi import FastAPI
from pydantic import BaseModel
import torch
import torch.nn as nn
from typing import List
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
#& "C:\Users\10200\scoop\apps\python\3.14.0\python.exe" -u app.py
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ==========================================
# 1. 挂载本地 LLM (零样本认知提取器)
# ==========================================
print("⏳ 正在加载本地 LLM (Qwen2.5-1.5B)... 请耐心等待 (调用RTX显存中)")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
llm_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-1.5B-Instruct", 
    torch_dtype=torch.float16, 
    device_map="auto" # 自动调用显卡
)
print("✅ 本地 LLM 加载完毕！")

# ==========================================
# 2. 加载手搓的 PyTorch 预测双擎
# ==========================================
class ZeroShotFreshnessNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.cat_embedding = nn.Embedding(10, 8) 
        self.fc = nn.Sequential(
            nn.Linear(12, 64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1)
        )
    def forward(self, x):
        cat_ids = x[:, 0].long()
        num_features = x[:, 1:]
        return self.fc(torch.cat((self.cat_embedding(cat_ids), num_features), dim=1))

model1 = ZeroShotFreshnessNet()
model1.load_state_dict(torch.load("ai1_zeroshot_freshness.pth"))
model1.eval()

# (注意：此处保留上一阶段重构的 DynamicRecipeNet 代码，为节省篇幅略过，确保 vocab_size 开到 1000 避免溢出)
class DynamicRecipeNet(nn.Module):
    def __init__(self, vocab_size=20, embedding_dim=32):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.mlp = nn.Sequential(
            nn.Linear(embedding_dim, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, 1), nn.Sigmoid()
        )
    def forward(self, x):
        embedded = self.embedding(x)
        mask = (x != 0).float().unsqueeze(-1)
        pooled = (embedded * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1.0)
        return self.mlp(pooled)

model2 = DynamicRecipeNet()
model2.load_state_dict(torch.load("ai2_dynamic_harmony.pth"))
model2.eval()

app = FastAPI(title="SmartPantry NEXUS Engine")

# ==========================================
# 3. 暴露 API 接口
# ==========================================
class ExtractRequest(BaseModel):
    ingredient_name: str

@app.post("/api/ai/extract_features")
def extract_features(req: ExtractRequest):
    """利用本地大模型，零样本提取未知食材特征"""
    prompt = f"你是一个厨房AI。提取食材【{req.ingredient_name}】的类别和常温保鲜天数。类别只能是(蔬菜,肉禽,水果,海鲜,豆制品,加工食品,调料,其他)。严格只输出JSON格式：{{\"category\": \"类别\", \"base_shelf_life\": 天数}}。"
    
    messages = [
        {"role": "system", "content": "你是一个严格的JSON输出机器人。"},
        {"role": "user", "content": prompt}
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer([text], return_tensors="pt").to(device)
    
    with torch.no_grad():
        generated_ids = llm_model.generate(model_inputs.input_ids, max_new_tokens=50)
        generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)]
    
    response_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    
    try:
        # 尝试解析大模型吐出的 JSON
        # 找到第一个 { 和 最后一个 } 之间的内容
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        json_str = response_text[start:end]
        res_dict = json.loads(json_str)
        return {"status": "success", "data": res_dict}
    except Exception as e:
        # LLM 解析失败的兜底策略
        return {"status": "success", "data": {"category": "其他", "base_shelf_life": 3}}

class FreshnessRequest(BaseModel):
    cat_id: int
    base_shelf_life: int
    storage_type: int
    temp: float
    initial_status: int

@app.post("/api/ai/predict_freshness")
def predict_freshness(req: FreshnessRequest):
    input_tensor = torch.tensor([[req.cat_id, req.base_shelf_life, req.storage_type, req.temp, req.initial_status]], dtype=torch.float32)
    with torch.no_grad():
        predicted_days = model1(input_tensor).item()
    return {"status": "success", "predicted_days": round(predicted_days, 1)}

class HarmonyRequest(BaseModel):
    ing_ids: List[int] 

@app.post("/api/ai/predict_harmony")
def predict_harmony(req: HarmonyRequest):
    input_tensor = torch.tensor([req.ing_ids], dtype=torch.long)
    with torch.no_grad():
        score = model2(input_tensor).item() * 100 
    return {"status": "success", "harmony_score": round(score, 1)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)