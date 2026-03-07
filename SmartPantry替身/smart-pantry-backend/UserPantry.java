package com.pantry.entity;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDate;

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
    private LocalDate predictedExpireDate; // AI 算出来后填这里
}