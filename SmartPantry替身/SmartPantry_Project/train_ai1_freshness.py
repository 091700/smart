import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

# ==========================================
# 1. 自动生成模拟训练数据 (Synthetic Data)
# ==========================================
print("正在生成AI 1训练数据...")
num_samples = 10000
# 特征维度：[食材ID(1-6), 存储方式(0冷冻/1冷藏/2常温), 温度(-18~30), 初始状态(1-5)]
X_data = np.zeros((num_samples, 4), dtype=np.float32)
y_data = np.zeros((num_samples, 1), dtype=np.float32)

for i in range(num_samples):
    ing_id = np.random.randint(1, 7) # 1到6的食材
    storage = np.random.randint(0, 3) # 0, 1, 2
    temp = np.random.uniform(-18, 30) if storage == 0 else (np.random.uniform(0, 10) if storage == 1 else np.random.uniform(15, 30))
    status = np.random.randint(1, 6) # 1到5分
    
    # 模拟物理常识的保鲜天数公式（仅为生成训练集，让AI去学这个规律）
    base_days = {1:5, 2:2, 3:15, 4:3, 5:30, 6:2}[ing_id]
    
    # 温度越低保鲜越久，状态越差保鲜越短
    temp_factor = max(0.1, (30 - temp) / 20.0) 
    status_factor = status / 5.0
    
    remain_days = base_days * temp_factor * status_factor
    # 加入一点点随机高斯噪声，模拟现实的不确定性
    remain_days += np.random.normal(0, 0.5) 
    
    X_data[i] = [ing_id, storage, temp, status]
    y_data[i] = [max(0.1, remain_days)] # 天数不能为负数

# 转换为 PyTorch 张量
X_tensor = torch.tensor(X_data, dtype=torch.float32)
y_tensor = torch.tensor(y_data, dtype=torch.float32)

# ==========================================
# 2. 定义 PyTorch 神经网络模型
# ==========================================
class FreshnessNet(nn.Module):
    def __init__(self, num_ingredients=10): # 假设最多支持10种食材ID
        super(FreshnessNet, self).__init__()
        # 核心：将食材ID转化为向量，这样AI能认识“西红柿”和“猪肉”的区别
        self.embedding = nn.Embedding(num_ingredients, 8) 
        
        # 将 Embedding出来的8维 + 剩下的3个特征(存储方式,温度,初始状态) = 11维输入
        self.fc_layers = nn.Sequential(
            nn.Linear(8 + 3, 64),
            nn.ReLU(),
            nn.Dropout(0.2), # 防止死记硬背（过拟合）
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1) # 输出层：1个连续的数值（天数）
        )

    def forward(self, x):
        # x[:, 0] 是食材ID，必须是整数
        ing_ids = x[:, 0].long()
        # 提取剩下的3个特征
        other_features = x[:, 1:] 
        
        embedded = self.embedding(ing_ids)
        # 拼接在一起送入全连接层
        combined = torch.cat((embedded, other_features), dim=1)
        return self.fc_layers(combined)

model1 = FreshnessNet()

# ==========================================
# 3. 训练模型
# ==========================================
criterion = nn.MSELoss() # 回归任务使用均方误差(MSE)
optimizer = optim.Adam(model1.parameters(), lr=0.01) # Adam优化器

print("开始训练 AI 1 (保鲜期预测模型)...")
epochs = 500
for epoch in range(epochs):
    optimizer.zero_grad()    # 清空梯度
    outputs = model1(X_tensor) # 正向传播
    loss = criterion(outputs, y_tensor) # 计算误差
    loss.backward()          # 反向传播求导
    optimizer.step()         # 更新权重
    
    if (epoch+1) % 100 == 0:
        print(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")

# 保存训练好的大脑权重！
torch.save(model1.state_dict(), "ai1_freshness.pth")
print("AI 1 训练完成并保存为 ai1_freshness.pth！")