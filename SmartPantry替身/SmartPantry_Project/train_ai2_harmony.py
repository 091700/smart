import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

# ==========================================
# 1. 自动生成组合数据 (正样本/负样本)
# ==========================================
print("正在生成AI 2训练数据...")
# 假设词典：1西红柿, 2猪肉, 3鸡蛋, 4西瓜, 5皮蛋, 6豆腐
# 我们定义一些人类常识中的“好搭配”(标签1) 和 “暗黑搭配”(标签0)
good_recipes = [
    [1, 3, 0], # 西红柿炒鸡蛋 (0代表没有第三种食材，补位)
    [2, 6, 0], # 猪肉炖豆腐
    [5, 6, 0], # 皮蛋豆腐
    [1, 2, 0]  # 西红柿炒肉
]
bad_recipes = [
    [4, 2, 0], # 西瓜炒肉
    [4, 5, 0], # 西瓜拌皮蛋
    [1, 4, 3], # 西红柿西瓜炒蛋
]

X_data = []
y_data = []

# 扩充数据集，让模型有足够的数据学习
for _ in range(1000):
    for recipe in good_recipes:
        X_data.append(recipe)
        y_data.append([1.0]) # 好吃
    for recipe in bad_recipes:
        X_data.append(recipe)
        y_data.append([0.0]) # 难吃

X_tensor = torch.tensor(X_data, dtype=torch.long)
y_tensor = torch.tensor(y_data, dtype=torch.float32)

# ==========================================
# 2. 定义 PyTorch 模型
# ==========================================
class RecipeHarmonyNet(nn.Module):
    def __init__(self, vocab_size=10, embedding_dim=16):
        super(RecipeHarmonyNet, self).__init__()
        # 让AI学习食材的味道坐标
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        
        # 每次固定输入3种食材，所以展平后是 3 * embedding_dim
        self.fc = nn.Sequential(
            nn.Linear(3 * embedding_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid() # Sigmoid 会把结果压缩到 0~1 之间（即和谐度百分比）
        )

    def forward(self, x):
        embedded = self.embedding(x) # shape: (batch_size, 3, embedding_dim)
        # 将3个食材的向量展平拼在一起
        flattened = embedded.view(x.size(0), -1) 
        return self.fc(flattened)

model2 = RecipeHarmonyNet()

# ==========================================
# 3. 训练模型
# ==========================================
criterion = nn.BCELoss() # 二分类任务使用交叉熵损失函数
optimizer = optim.Adam(model2.parameters(), lr=0.005)

print("开始训练 AI 2 (味觉冲突模型)...")
epochs = 300
for epoch in range(epochs):
    optimizer.zero_grad()
    outputs = model2(X_tensor)
    loss = criterion(outputs, y_tensor)
    loss.backward()
    optimizer.step()
    
    if (epoch+1) % 50 == 0:
        print(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")

torch.save(model2.state_dict(), "ai2_harmony.pth")
print("AI 2 训练完成并保存为 ai2_harmony.pth！")