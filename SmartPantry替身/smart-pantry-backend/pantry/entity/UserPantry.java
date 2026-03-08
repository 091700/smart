package com.pantry.entity;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("user_pantry")
public class UserPantry {
    @TableId(type = IdType.AUTO)
    private Integer id;
    private Integer userId;
    private Integer ingredientId;
    private LocalDate entryDate;
    private Integer storageType;
    private Float currentTemp;
    private Integer initialStatus;
    
    // --- 新增字段 ---
    private Integer status; // 0:在库, 1:已吃掉, 2:已丢弃
    private LocalDateTime updateTime; // 记录吃掉或丢弃的精准时间
    
    private LocalDate predictedExpireDate; 
}