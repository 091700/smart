package com.pantry;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.client.RestTemplate;
//cd C:\Users\10200\Desktop\SmartPantry\smart-pantry-backend
//java -jar target/smart-pantry-backend-0.0.1-SNAPSHOT.jar
@SpringBootApplication

public class SmartPantryApplication {
    public static void main(String[] args) {
        SpringApplication.run(SmartPantryApplication.class, args);
    }

    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate(); // 用于发起 HTTP 请求的神器
    }
}