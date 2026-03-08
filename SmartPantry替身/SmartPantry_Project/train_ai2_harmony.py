import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

# 自动检测你的 RTX 5060 显卡
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"当前使用的计算设备: {device}")

# ==========================================
# 1. 动态生成可变长训练数据
# ==========================================
print("正在生成动态维度 AI 2 训练数据...")
# 词典：1西红柿, 2猪肉, 3鸡蛋, 4西瓜, 5皮蛋, 6豆腐 (0为Padding空位)
good_recipes = [
    [1, 3],          # 2种：西红柿鸡蛋
    [2, 6],          # 2种：猪肉豆腐
    [1, 2, 6],       # 3种：西红柿肉末豆腐
    [5, 6],          # 2种：皮蛋豆腐
    [1, 2, 3, 6]     # 4种：终极大杂烩(好吃)
]
bad_recipes = [
    [4, 2],          # 2种：西瓜炒肉
    [4, 5, 6],       # 3种：西瓜皮蛋豆腐
    [1, 4, 3],       # 3种：西红柿西瓜蛋
    [1, 4, 5, 2]     # 4种：极致暗黑料理
]

# 找到最大长度以便补齐 (Padding)
max_len = max(max(len(r) for r in good_recipes), max(len(r) for r in bad_recipes))

X_data, y_data = [], []
for _ in range(1500):
    for recipe in good_recipes:
        # 不足最大长度的用 0 补齐
        padded = recipe + [0] * (max_len - len(recipe))
        X_data.append(padded)
        y_data.append([1.0])
    for recipe in bad_recipes:
        padded = recipe + [0] * (max_len - len(recipe))
        X_data.append(padded)
        y_data.append([0.0])

# 转为张量并推送到 GPU
X_tensor = torch.tensor(X_data, dtype=torch.long).to(device)
y_tensor = torch.tensor(y_data, dtype=torch.float32).to(device)

# ==========================================
# 2. 定义动态融合神经网络 (NLP 架构)
# ==========================================
class DynamicRecipeNet(nn.Module):
    def __init__(self, vocab_size=20, embedding_dim=32):
        super().__init__()
        # padding_idx=0 保证空位的初始向量全是0
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        
        # 因为引入了池化层，输入的维度被死死固定在了 embedding_dim (32维)，再也不受食材数量限制！
        self.mlp = nn.Sequential(
            nn.Linear(embedding_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.3), # 强大的正则化，防止过拟合
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        # x shape: (batch_size, seq_len)
        embedded = self.embedding(x) # shape: (batch_size, seq_len, 32)
        
        # 核心算法：生成掩码 (Mask)，过滤掉为 0 的无效占位符
        mask = (x != 0).float().unsqueeze(-1) # shape: (batch_size, seq_len, 1)
        
        # 将有效特征向量相加
        sum_embedded = (embedded * mask).sum(dim=1) 
        # 计算有效食材的真实数量，防止除以 0
        valid_counts = mask.sum(dim=1).clamp(min=1.0) 
        
        # 全局平均池化 (Global Average Pooling)
        pooled = sum_embedded / valid_counts # shape: (batch_size, 32)
        
        return self.mlp(pooled)

model2 = DynamicRecipeNet().to(device)

# ==========================================
# 3. 显卡满载训练
# ==========================================
criterion = nn.BCELoss()
optimizer = optim.Adam(model2.parameters(), lr=0.005)

print("🚀 开始在 CUDA 环境下训练动态 AI 2...")
epochs = 400
for epoch in range(epochs):
    optimizer.zero_grad()
    outputs = model2(X_tensor)
    loss = criterion(outputs, y_tensor)
    loss.backward()
    optimizer.step()
    
    if (epoch+1) % 50 == 0:
        print(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")

# 将训练好的权重拉回 CPU 保存，保证部署时的兼容性
torch.save(model2.cpu().state_dict(), "ai2_dynamic_harmony.pth")
print("✅ 动态大脑训练完成并保存为 ai2_dynamic_harmony.pth！")
