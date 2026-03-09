from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
import torch.nn as nn
from typing import List, Optional
import json
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer

print("PyTorch版本：", torch.__version__)

# 3. 查看CUDA是否可用（验证GPU是否能正常使用）
print("CUDA是否可用：", torch.cuda.is_available())

# 4. 查看当前显卡名称（如果CUDA可用）
if torch.cuda.is_available():
    print("当前显卡：", torch.cuda.get_device_name(0))
    print("CUDA版本（PyTorch内置）：", torch.version.cuda)
else:
    print("当前使用CPU版本PyTorch")

# ==========================================
# 0. 系统配置与日志
# ==========================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

device = torch.device("cpu")
logger.info("⚠️ 检测到超前架构显卡，已强制降级为 CPU 稳定模式")
logger.info(f"🚀 核心引擎启动！当前设备: {device}")

# ==========================================
# 1. 挂载本地 LLM (零样本认知提取器)
# ==========================================
# 保持你原来的 Qwen 加载逻辑
logger.info("⏳ 正在加载本地 LLM (Qwen2.5-1.5B)...")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
llm_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-1.5B-Instruct", 
    torch_dtype=torch.float16, 
    device_map="auto"
)
logger.info("✅ 本地 LLM 加载完毕！")

# ==========================================
# 2. AI-1 架构：保鲜期预测 (ZeroShot)
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
        # 拼接 Embedding 和 数值特征
        return self.fc(torch.cat((self.cat_embedding(cat_ids), num_features), dim=1))

# ==========================================
# 3. AI-2 架构：Nexus Transformer (终极厨艺大脑)
# ==========================================
# 
class NexusTransformerNet(nn.Module):
    def __init__(self, vocab_size=200, embedding_dim=64, num_heads=4, max_seq_len=5):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        # 位置编码：让模型理解食材的组合顺序空间
        self.position_encoding = nn.Parameter(torch.randn(1, max_seq_len, embedding_dim))
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embedding_dim, nhead=num_heads, 
            dim_feedforward=256, dropout=0.3, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=2)
        
        self.fc1 = nn.Linear(embedding_dim, 128)
        self.bn1 = nn.BatchNorm1d(128)
        self.fc2 = nn.Linear(128, 64)
        self.bn2 = nn.BatchNorm1d(64)
        self.out = nn.Linear(64, 1)
        self.gelu = nn.GELU()
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # 1. 词嵌入 + 位置编码
        embedded = self.embedding(x) + self.position_encoding
        src_key_padding_mask = (x == 0)
        
        # 2. Transformer 自注意力交互 (化学反应)
        attended = self.transformer(embedded, src_key_padding_mask=src_key_padding_mask)
        
        # 3. 掩码池化
        valid_mask = (~src_key_padding_mask).float().unsqueeze(-1)
        pooled = (attended * valid_mask).sum(dim=1) / valid_mask.sum(dim=1).clamp(min=1e-6)
        
        # 4. 残差 MLP 推理
        x1 = self.gelu(self.bn1(self.fc1(pooled)))
        x1 = x1 + pooled[:, :128] if pooled.shape[1] >= 128 else x1 # 残差连接
        x2 = self.gelu(self.bn2(self.fc2(x1)))
        x2 = x2 + x1[:, :64] # 残差连接
        return self.sigmoid(self.out(x2))

# ==========================================
# 4. 初始化模型并加载权重
# ==========================================
model1 = ZeroShotFreshnessNet().to(device)
try:
    model1.load_state_dict(torch.load("ai1_zeroshot_freshness.pth", map_location=device))
    model1.eval()
    logger.info("✅ AI-1 权重加载成功")
except:
    logger.warning("⚠️ AI-1 权重未找到，请确保已运行训练脚本")

model2 = NexusTransformerNet(vocab_size=200, max_seq_len=5).to(device)
try:
    # 加载你刚才跑出的那个最优模型
    checkpoint = torch.load("ai2_nexus_harmony_best.pth", map_location=device, weights_only=True)
    # 兼容两种保存格式（完整checkpoint / 纯权重）
    if "model_state_dict" in checkpoint:
        model2.load_state_dict(checkpoint["model_state_dict"])
    else:
        model2.load_state_dict(checkpoint)
    model2.eval()
    logger.info("✅ AI-2 Nexus Transformer 权重加载成功")
except Exception as e:
    logger.warning(f"⚠️ AI-2 加载失败: {e}")

app = FastAPI(title="SmartPantry NEXUS Engine")

# ==========================================
# 5. API 数据模型 (解决 422 报错的关键)
# ==========================================
class ExtractRequest(BaseModel):
    ingredient_name: str

class FreshnessRequest(BaseModel):
    # 与 Java AiIntegrationService.java 的 Map 字段严格对应
    cat_id: int = 8                    
    base_shelf_life: float = 3.0       
    storage_type: int
    temp: float
    initial_status: int

class HarmonyRequest(BaseModel):
    ing_ids: List[int]

# ==========================================
# 6. API 路由实现
# ==========================================

@app.post("/api/ai/extract_features")
def extract_features(req: ExtractRequest):
    """LLM 零样本特征提取"""
    prompt = f"提取食材【{req.ingredient_name}】的类别和常温保鲜天数。类别必选其一:(蔬菜,肉禽,水果,海鲜,豆制品,加工食品,调料,其他)。只输出JSON：{{\"category\": \"类别\", \"base_shelf_life\": 天数}}。"
    messages = [{"role": "system", "content": "你是一个JSON输出机器人。"}, {"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer([text], return_tensors="pt").to(device)
    
    with torch.no_grad():
        generated_ids = llm_model.generate(model_inputs.input_ids, max_new_tokens=50)
        generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)]
    
    response_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    try:
        start, end = response_text.find('{'), response_text.rfind('}') + 1
        return {"status": "success", "data": json.loads(response_text[start:end])}
    except:
        return {"status": "success", "data": {"category": "其他", "base_shelf_life": 3}}

@app.post("/api/ai/predict_freshness")
def predict_freshness(req: FreshnessRequest):
    """
    AI-1 预测。
    注意：这里假设 cat_id 由 Java 从数据库取出并传给 Python。
    """
    # 构造 Tensor: [cat_id, base_shelf_life, storage_type, temp, initial_status]
    # 如果 Java 只传了 ing_id，这里建议先调用 LLM 或查表获取类别特征
    input_data = [[float(req.cat_id), float(req.base_shelf_life), float(req.storage_type), float(req.temp), float(req.initial_status)]]
    input_tensor = torch.tensor(input_data, dtype=torch.float32).to(device)
    
    with torch.no_grad():
        predicted_days = model1(input_tensor).item()
    return {"status": "success", "predicted_days": round(predicted_days, 1)}

@app.post("/api/ai/predict_harmony")
def predict_harmony(req: HarmonyRequest):
    """AI-2 厨艺逻辑推理"""
    print(f"DEBUG: AI-2 收到食材 IDs: {request.ing_ids}")
    # 1. 截断与补齐 (最大支持 5 种食材)
    ids = req.ing_ids[:5]
    padded_ids = ids + [0] * (5 - len(ids))
    
    input_tensor = torch.tensor([padded_ids], dtype=torch.long).to(device)
    
    with torch.no_grad():
        score = model2(input_tensor).item()
    
    # 2. 更加实用的反馈话术
    if score > 0.85: msg = "简直是米其林级别的黄金搭配！"
    elif score > 0.7: msg = "味道很均衡，是家常菜的高水准。"
    elif score > 0.5: msg = "中规中矩，填饱肚子没问题。"
    elif score > 0.3: msg = "味道可能有点奇怪，建议少放点盐..."
    else: msg = "暗黑料理预警！为了肠胃着想，请务必三思！"
    
    return {
        "status": "success", 
        "harmony_score": round(score * 100, 1), 
        "message": msg
    }

if __name__ == "__main__":
    import uvicorn
    # 使用 8000 端口，请确保 Java 端的 ai.engine.url 指向这里
    uvicorn.run(app, host="0.0.0.0", port=8000)