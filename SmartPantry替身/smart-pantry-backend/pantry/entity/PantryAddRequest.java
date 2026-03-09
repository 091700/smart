package com.pantry.entity;
import lombok.Data;

@Data
public class PantryAddRequest {
    private Object ingredientInput; // 核心：可以是 Integer(已有ID)，也可以是 String(手打新食材)
    private Integer storageType;
    private Float currentTemp;
    private Integer initialStatus;
}