package com.iflytek.auto.ai-agent.sleweb.web.exception;

import com.iflytek.auto.framework.api.entry.ResponseData;
import com.iflytek.auto.framework.api.exception.BizException;
import com.iflytek.auto.framework.web.common.exception.BizCodeExceptionHandler;
import lombok.Data;
import org.springframework.stereotype.Component;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@Component
public class Biz1001ExceptionHandler implements BizCodeExceptionHandler {

    @Override
    public int getCode() {
        return 1001;
    }

    @Override
    public Object handleException(HttpServletRequest request, HttpServletResponse response, BizException e) {
        Biz1001Response data = new Biz1001Response();
        data.testA = "Test A";
        data.testB = "Test B";

        return ResponseData.of(e, data);
    }

    @Data
    public static class Biz1001Response{
        private String testA;
        private String testB;
    }
}
