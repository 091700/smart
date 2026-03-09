package com.pantry.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.pantry.entity.IngredientDict;
import com.pantry.entity.PantryAddRequest;
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
    public String addIngredientToPantry(@RequestBody PantryAddRequest req) {
        Integer finalIngredientId = null;
        IngredientDict dict = null;

        // 判断前端传的是数字(旧食材)还是字符串(新食材)
        if (req.getIngredientInput() instanceof Integer) {
            finalIngredientId = (Integer) req.getIngredientInput();
            dict = dictMapper.selectById(finalIngredientId);
        } else if (req.getIngredientInput() instanceof String) {
            String newName = (String) req.getIngredientInput();
            
            // 查库看有没有同名的，防止重复录入
            QueryWrapper<IngredientDict> query = new QueryWrapper<>();
            query.eq("name", newName);
            dict = dictMapper.selectOne(query);
            
            if (dict == null) {
                // 💥 高光时刻：本地大模型零样本学习！
                Map<String, Object> features = aiService.extractIngredientFeatures(newName);
                
                dict = new IngredientDict();
                dict.setName(newName);
                dict.setCategory((String) features.get("category"));
                dict.setBaseShelfLife((Integer) features.get("base_shelf_life"));
                
                dictMapper.insert(dict); // 自动写入 MySQL，实现认知自我扩充
            }
            finalIngredientId = dict.getId();
        }

        // 调用重构后的 AI-1
        Integer catId = aiService.mapCategoryToId(dict.getCategory());
        Double predictedDays = aiService.predictFreshness(
                catId, 
                dict.getBaseShelfLife(), 
                req.getStorageType(), 
                req.getCurrentTemp(), 
                req.getInitialStatus()
        );

        UserPantry pantryItem = new UserPantry();
        pantryItem.setUserId(1);
        pantryItem.setIngredientId(finalIngredientId);
        pantryItem.setEntryDate(LocalDate.now());
        pantryItem.setStorageType(req.getStorageType());
        pantryItem.setCurrentTemp(req.getCurrentTemp());
        pantryItem.setInitialStatus(req.getInitialStatus());
        pantryItem.setStatus(0); // 0代表在库
        pantryItem.setPredictedExpireDate(LocalDate.now().plusDays(predictedDays.longValue()));

        userPantryMapper.insert(pantryItem);

        return "【" + dict.getName() + "】入库成功！AI预测将于 " + pantryItem.getPredictedExpireDate() + " 变质。";
    }

    /**
     * 2. 打开冰箱看一眼（按变质风险排序）
     */
    @GetMapping("/my-fridge")
    public List<UserPantry> getMyFridge() {
        QueryWrapper<UserPantry> query = new QueryWrapper<>();
        // 核心修改：只查询 status = 0 (在库) 的食材
        query.eq("status", 0);
        query.orderByAsc("predicted_expire_date");
        return userPantryMapper.selectList(query);
    }
    
    @PostMapping("/consume/{id}")
    public String consumeIngredient(@PathVariable Integer id) {
        UserPantry item = userPantryMapper.selectById(id);
        if (item != null) {
            item.setStatus(1); // 1 代表已吃掉
            userPantryMapper.updateById(item);
            return "干饭人，干饭魂！已记录到你的光盘成就中。";
        }
        return "找不到该食材！";
    }
    @PostMapping("/discard/{id}")
    public String discardIngredient(@PathVariable Integer id) {
        UserPantry item = userPantryMapper.selectById(id);
        if (item != null) {
            item.setStatus(2); // 2 代表已丢弃
            userPantryMapper.updateById(item);
            return "已清理。下次记得在过期前吃掉哦！";
        }
        return "找不到该食材！";
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