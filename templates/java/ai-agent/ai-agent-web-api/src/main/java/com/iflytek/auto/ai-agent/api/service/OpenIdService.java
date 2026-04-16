package com.iflytek.auto.ai-agent.api.service;

import com.iflytek.auto.framework.api.annotation.AutoClientMethod;
import com.iflytek.auto.framework.api.annotation.AutoClientMode;
import com.iflytek.auto.framework.api.annotation.AutoClientService;

import static com.iflytek.auto.ai-agent.api.service.ServiceConstant.*;

@AutoClientService(name = APP_NAME, version = APP_VER, contextPath = APP_CONTEXT_PATH)
public interface OpenIdService {

    /**
     * GET /v1/openId/validate?openId=xxx
     * @param openId
     * @return
     */
    @AutoClientMethod(mode = AutoClientMode.GET, path = "/openId/validate?openId={+openId}")
    String validateGetOpenId(String openId);
}
