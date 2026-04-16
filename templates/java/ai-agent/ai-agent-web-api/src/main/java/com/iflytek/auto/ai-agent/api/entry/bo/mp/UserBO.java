package com.iflytek.auto.ai-agent.api.entry.bo.mp;

import lombok.Data;
import lombok.ToString;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
* @className: com.iflytek.auto.sample.sleweb.web.demo.mp.domain.bo-> UserBO
* @description: 用户业务对象
* @author: weiwang111@iflytek.com
* @createDate: 2022-12-02 7:54
* @version: 1.0
* @todo:
*/
@Data
@ToString
public class UserBO implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;

    private String name;

    private Integer age;

    private LocalDateTime createTime;

    private LocalDateTime modifiedTime;


}
