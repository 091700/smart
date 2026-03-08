package com.pantry.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class AiIntegrationService {

    @Autowired
    private RestTemplate restTemplate;

    @Value("${ai.engine.url}")
    private String aiEngineUrl;

    /**
     * 召唤 AI 1：预测食材还能放几天
     */
    public Double predictFreshness(Integer catId, Integer baseShelfLife, Integer storageType, Float temp, Integer status) {
        String url = aiEngineUrl + "/api/ai/predict_freshness";
        
        // 组装发给 Python 的 JSON 数据
        Map<String, Object> request = new HashMap<>();
        request.put("cat_id", catId);
        request.put("base_shelf_life", baseShelfLife);
        request.put("storage_type", storageType);
        request.put("temp", temp);
        request.put("initial_status", status);
        try {
        ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
        if (response.getBody() != null && "success".equals(response.getBody().get("status"))) {
            return Double.valueOf(response.getBody().get("predicted_days").toString());
        }
    } catch (Exception e) {
        System.err.println("AI 1 预测失败，请检查 Python 引擎是否切换到了 Zero-Shot 版本！");
    }
    return 3.0; // 保底
}

    /**
     * 召唤 AI 2：评估暗黑料理指数
     */
    public Double predictHarmony(List<Integer> ingredientIds) {
        String url = aiEngineUrl + "/api/ai/predict_harmony";
        
        Map<String, Object> request = new HashMap<>();
        request.put("ing_ids", ingredientIds);

        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
            if (response.getBody() != null && "success".equals(response.getBody().get("status"))) {
                // 取出和谐度分数 (0-100)
                return Double.valueOf(response.getBody().get("harmony_score").toString());
            }
        } catch (Exception e) {
            System.err.println("AI 2 预测失败！");
        }
        return 50.0;
    }
    /**
     * 调用本地 LLM 提取未知食材特征
     */
    public Map<String, Object> extractIngredientFeatures(String ingredientName) {
        String url = aiEngineUrl + "/api/ai/extract_features";
        Map<String, String> request = new HashMap<>();
        request.put("ingredient_name", ingredientName);
        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
            return (Map<String, Object>) response.getBody().get("data");
        } catch (Exception e) {
            Map<String, Object> fallback = new HashMap<>();
            fallback.put("category", "其他");
            fallback.put("base_shelf_life", 3);
            return fallback;
        }
    }

    // 映射中文类别到 AI-1 的数字张量
    public Integer mapCategoryToId(String category) {
        switch (category) {
            case "蔬菜": return 1; case "肉禽": return 2; case "水果": return 3;
            case "海鲜": return 4; case "豆制品": return 5; case "加工食品": return 6;
            case "调料": return 7; default: return 8;
        }
    }
}
