package com.iflytek.auto.ai-agent.sleweb.web.controller;

import com.iflytek.auto.framework.api.exception.BizException;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/exception")
public class ExceptionController {

    @GetMapping("/validate")
    public String validateExceptionResponse() {
        throw new BizException(1002, "测试");
    }

    @GetMapping("/biz")
    public String validateBizExceptionResponse() {
        throw new BizException(1002, "测试");
    }
}
