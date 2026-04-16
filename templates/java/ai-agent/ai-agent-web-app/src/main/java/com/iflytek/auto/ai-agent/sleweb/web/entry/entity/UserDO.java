package com.iflytek.auto.ai-agent.sleweb.web.entry.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.FieldFill;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * @author xxx
 * @since 2022-11-24
 */
@TableName("T_USER")
public class UserDO implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(value = "ID", type = IdType.AUTO)
    private Long id;

    @TableField("`NAME`")
    private String name;

    @TableField("AGE")
    private Integer age;

    @TableField(value = "CREATE_TIME", fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    @TableField(value = "MODIFIED_TIME", fill = FieldFill.UPDATE)
    private LocalDateTime modifiedTime;


    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Integer getAge() {
        return age;
    }

    public void setAge(Integer age) {
        this.age = age;
    }

    public LocalDateTime getCreateTime() {
        return createTime;
    }

    public void setCreateTime(LocalDateTime createTime) {
        this.createTime = createTime;
    }

    public LocalDateTime getModifiedTime() {
        return modifiedTime;
    }

    public void setModifiedTime(LocalDateTime modifiedTime) {
        this.modifiedTime = modifiedTime;
    }

    @Override
    public String toString() {
        return "UserDO{" +
                "id=" + id +
                ", name=" + name +
                ", age=" + age +
                ", createTime=" + createTime +
                ", modifiedTime=" + modifiedTime +
                "}";
    }
}
