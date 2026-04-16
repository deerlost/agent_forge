package com.iflytek.auto.ai-agent.api.service;

import com.iflytek.auto.framework.api.annotation.AutoClientMethod;
import com.iflytek.auto.framework.api.annotation.AutoClientMode;
import com.iflytek.auto.framework.api.annotation.AutoClientService;

import static com.iflytek.auto.ai-agent.api.service.ServiceConstant.*;

@AutoClientService(name = APP_NAME, version = APP_VER, contextPath = APP_CONTEXT_PATH)
public interface ExceptionService {

    /**
     * GET /v1/exception/validate
     */
    @AutoClientMethod(mode = AutoClientMode.GET, path = "/exception/validate")
    void validateExceptionResponse();

    /**
     * GET /v1/exception/biz
     * @return
     */
    @AutoClientMethod(mode = AutoClientMode.GET, path = "/exception/biz")
    String validateBizExceptionResponse();
}