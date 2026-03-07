package com.pantry.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.pantry.entity.IngredientDict;
import com.pantry.entity.UserPantry;
import com.pantry.mapper.IngredientDictMapper;
import com.pantry.mapper.UserPantryMapper;
import com.pantry.service.AiIntegrationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/pantry")
@CrossOrigin // 允许 Vue 跨域访问
public class PantryController {

    @Autowired
    private UserPantryMapper userPantryMapper;
    
    @Autowired
    private IngredientDictMapper dictMapper;

    @Autowired
    private AiIntegrationService aiService;

    /**
     * 1. 往冰箱放东西（核心联动逻辑）
     * 前端传进来：ingredientId, storageType, currentTemp, initialStatus
     */
    @PostMapping("/add")
    public String addIngredientToPantry(@RequestBody UserPantry pantryItem) {
        // 设置入库时间为今天
        pantryItem.setEntryDate(LocalDate.now());
        pantryItem.setUserId(1); // 默认单用户模式

        // 🔥 高光时刻：召唤 AI 预测保鲜天数！
        Double predictedDays = aiService.predictFreshness(
                pantryItem.getIngredientId(),
                pantryItem.getStorageType(),
                pantryItem.getCurrentTemp(),
                pantryItem.getInitialStatus()
        );

        // 计算出具体的过期日期：今天 + 预测出的天数 (向下取整)
        LocalDate expireDate = LocalDate.now().plusDays(predictedDays.longValue());
        pantryItem.setPredictedExpireDate(expireDate);

        // 存入 MySQL 数据库
        userPantryMapper.insert(pantryItem);

        return "放入冰箱成功！AI预测将于 " + expireDate + " 变质，请及时食用。";
    }

    /**
     * 2. 打开冰箱看一眼（按变质风险排序）
     */
    @GetMapping("/my-fridge")
    public List<UserPantry> getMyFridge() {
        QueryWrapper<UserPantry> query = new QueryWrapper<>();
        // 按照过期时间升序排列（快坏的排在最前面）
        query.orderByAsc("predicted_expire_date");
        return userPantryMapper.selectList(query);
    }

    /**
     * 3. 字典数据：前端录入时需要知道有哪些食材可选
     */
    @GetMapping("/dict")
    public List<IngredientDict> getDict() {
        return dictMapper.selectList(null);
    }

    /**
     * 4. 厨房防雷：检查暗黑料理组合
     * 前端传入形如：[1, 5, 6] (西红柿、皮蛋、豆腐的ID)
     */
    @PostMapping("/check-recipe")
    public String checkRecipe(@RequestBody Map<String, List<Integer>> payload) {
        List<Integer> ingredientIds = payload.get("ids");
        
        // 召唤 AI 计算和谐度
        Double score = aiService.predictHarmony(ingredientIds);
        
        if (score > 70) {
            return "味觉和谐度：" + score + "分。绝妙搭配，快去大显身手！";
        } else if (score > 40) {
            return "味觉和谐度：" + score + "分。中规中矩，可以一试。";
        } else {
            return "味觉和谐度：" + score + "分。💥 暗黑料理预警！极度容易拉肚子，请三思！";
        }
    }
}