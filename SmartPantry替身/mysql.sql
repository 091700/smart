-- 给用户冰箱表增加 '状态' 字段
-- 0: 在库 (默认), 1: 已吃掉 (光盘), 2: 已丢弃 (浪费)
ALTER TABLE user_pantry 
ADD COLUMN status INT DEFAULT 0 COMMENT '0:在库, 1:已吃掉, 2:已丢弃' AFTER initial_status;

CREATE DATABASE IF NOT EXISTS smart_pantry DEFAULT CHARSET utf8mb4;
USE smart_pantry;

-- 1. 食材字典表（存储常识数据）
CREATE TABLE ingredient_dict (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    category VARCHAR(20) NOT NULL, -- 蔬菜, 肉类, 水果, 海鲜, 调料
    base_shelf_life INT NOT NULL -- 基础保鲜天数（常温下的基准值）
);

-- 插入一些基础食材
INSERT INTO ingredient_dict (name, category, base_shelf_life) VALUES 
('西红柿', '蔬菜', 5), ('猪肉', '肉类', 2), ('鸡蛋', '肉禽', 15), 
('西瓜', '水果', 3), ('皮蛋', '加工食品', 30), ('豆腐', '豆制品', 2);

-- 2. 用户冰箱表
CREATE TABLE user_pantry (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT DEFAULT 1, -- 默认用户1
    ingredient_id INT NOT NULL,
    entry_date DATE NOT NULL, -- 入库时间
    storage_type INT NOT NULL, -- 0:冷冻, 1:冷藏, 2:常温
    current_temp FLOAT, -- 存放温度
    initial_status INT DEFAULT 5, -- 初始状态(1-5分，5为最新鲜)
    predicted_expire_date DATE -- AI预测的过期时间（由Java调用AI后回填）
);-- 增加状态变更的记录时间，方便后续做时间轴动画
ALTER TABLE user_pantry 
ADD COLUMN update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '状态更新时间';