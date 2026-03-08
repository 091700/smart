import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ==========================================
# 1. 生成基于【类别特征】的训练数据 (彻底抛弃食材ID)
# 类别映射: 1蔬菜, 2肉禽, 3水果, 4海鲜, 5豆制品, 6加工食品, 7调料, 8其他
# ==========================================
num_samples = 15000
# 特征维度: [类别ID(1-8), 基础保质期(天), 存储方式(0冷冻/1冷藏/2常温), 温度, 初始状态(1-5)]
X_data = np.zeros((num_samples, 5), dtype=np.float32)
y_data = np.zeros((num_samples, 1), dtype=np.float32)

for i in range(num_samples):
    cat_id = np.random.randint(1, 9)
    base_days = np.random.uniform(1.0, 365.0) # 从1天到一年的都有
    storage = np.random.randint(0, 3)
    temp = np.random.uniform(-18, 30) if storage == 0 else (np.random.uniform(0, 10) if storage == 1 else np.random.uniform(15, 30))
    status = np.random.randint(1, 6)
    
    # 物理常识衰减模拟
    temp_factor = max(0.1, (30 - temp) / 20.0)
    status_factor = status / 5.0
    remain_days = base_days * temp_factor * status_factor + np.random.normal(0, 0.5)
    
    X_data[i] = [cat_id, base_days, storage, temp, status]
    y_data[i] = [max(0.1, remain_days)]

X_tensor = torch.tensor(X_data, dtype=torch.float32).to(device)
y_tensor = torch.tensor(y_data, dtype=torch.float32).to(device)

# ==========================================
# 2. 零样本保鲜神经网络
# ==========================================
class ZeroShotFreshnessNet(nn.Module):
    def __init__(self):
        super().__init__()
        # 只对 8 个类别做 Embedding
        self.cat_embedding = nn.Embedding(10, 8) 
        # 类别Embedding(8维) + 基础天数 + 存储 + 温度 + 状态 = 12维
        self.fc = nn.Sequential(
            nn.Linear(8 + 4, 64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1)
        )

    def forward(self, x):
        cat_ids = x[:, 0].long()
        num_features = x[:, 1:]
        embedded = self.cat_embedding(cat_ids)
        combined = torch.cat((embedded, num_features), dim=1)
        return self.fc(combined)

model1 = ZeroShotFreshnessNet().to(device)
criterion = nn.MSELoss()
optimizer = optim.Adam(model1.parameters(), lr=0.01)

print("🚀 开始训练 AI-1 (零样本泛化架构)...")
for epoch in range(500):
    optimizer.zero_grad()
    loss = criterion(model1(X_tensor), y_tensor)
    loss.backward()
    optimizer.step()

torch.save(model1.cpu().state_dict(), "ai1_zeroshot_freshness.pth")
print("✅ AI-1 重构完成，已免疫未知食材报错！")
