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
    public Double predictFreshness(Integer ingId, Integer storageType, Float temp, Integer status) {
        String url = aiEngineUrl + "/api/ai/predict_freshness";
        
        // 组装发给 Python 的 JSON 数据
        Map<String, Object> request = new HashMap<>();
        request.put("ing_id", ingId);
        request.put("storage_type", storageType);
        request.put("temp", temp);
        request.put("initial_status", status);

        try {
            // 发起 POST 请求
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
            if (response.getBody() != null && "success".equals(response.getBody().get("status"))) {
                // 取出 AI 预测的天数
                return Double.valueOf(response.getBody().get("predicted_days").toString());
            }
        } catch (Exception e) {
            System.err.println("AI 1 预测失败，请检查 Python 服务是否启动！");
        }
        return 3.0; // 如果 AI 挂了，给个默认保底天数
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
}