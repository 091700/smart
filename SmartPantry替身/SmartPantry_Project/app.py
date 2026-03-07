from fastapi import FastAPI
from pydantic import BaseModel
import torch
import torch.nn as nn
# cd C:\Users\10200\Desktop\SmartPantry\SmartPantry_Project\ai_engine
# C:\Users\10200\AppData\Local\Programs\Python\Python311\python.exe app.py
# 1. 把刚才的模型结构抄过来（部署时只需要结构，不需要训练代码）
class FreshnessNet(nn.Module):
    def __init__(self, num_ingredients=10):
        super(FreshnessNet, self).__init__()
        self.embedding = nn.Embedding(num_ingredients, 8) 
        self.fc_layers = nn.Sequential(
            nn.Linear(8 + 3, 64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1)
        )
    def forward(self, x):
        ing_ids = x[:, 0].long()
        other_features = x[:, 1:] 
        embedded = self.embedding(ing_ids)
        combined = torch.cat((embedded, other_features), dim=1)
        return self.fc_layers(combined)

class RecipeHarmonyNet(nn.Module):
    def __init__(self, vocab_size=10, embedding_dim=16):
        super(RecipeHarmonyNet, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.fc = nn.Sequential(
            nn.Linear(3 * embedding_dim, 64), nn.ReLU(),
            nn.Linear(64, 1), nn.Sigmoid()
        )
    def forward(self, x):
        embedded = self.embedding(x)
        flattened = embedded.view(x.size(0), -1) 
        return self.fc(flattened)

# 2. 实例化并加载训练好的权重
print("正在加载 AI 模型...")
model1 = FreshnessNet()
model1.load_state_dict(torch.load("ai1_freshness.pth"))
model1.eval() # 切换到推理模式

model2 = RecipeHarmonyNet()
model2.load_state_dict(torch.load("ai2_harmony.pth"))
model2.eval()

# 3. 初始化 FastAPI
app = FastAPI(title="SmartPantry AI Engine")

# 定义接口接收的数据格式
class FreshnessRequest(BaseModel):
    ing_id: int
    storage_type: int
    temp: float
    initial_status: int

class HarmonyRequest(BaseModel):
    ing_ids: list[int] # 必须传包含3个整数的列表

@app.post("/api/ai/predict_freshness")
def predict_freshness(req: FreshnessRequest):
    # 将输入转为 PyTorch 张量
    input_tensor = torch.tensor([[req.ing_id, req.storage_type, req.temp, req.initial_status]], dtype=torch.float32)
    with torch.no_grad(): # 推理时不需要计算梯度，省内存
        result = model1(input_tensor)
    
    predicted_days = result.item()
    return {"status": "success", "predicted_days": round(predicted_days, 1)}

@app.post("/api/ai/predict_harmony")
def predict_harmony(req: HarmonyRequest):
    # 保证输入正好是3个食材，不够补0
    ids = req.ing_ids[:3]
    while len(ids) < 3:
        ids.append(0)
        
    input_tensor = torch.tensor([ids], dtype=torch.long)
    with torch.no_grad():
        score = model2(input_tensor)
    
    harmony_score = score.item() * 100 # 转为百分制
    return {"status": "success", "harmony_score": round(harmony_score, 1)}

# 启动命令提示
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)