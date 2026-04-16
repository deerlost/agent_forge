package com.iflytek.auto.ai-agent.api.service;

import com.iflytek.auto.framework.api.annotation.AutoClientMethod;
import com.iflytek.auto.framework.api.annotation.AutoClientMode;
import com.iflytek.auto.framework.api.annotation.AutoClientService;

import static com.iflytek.auto.ai-agent.api.service.ServiceConstant.*;

@AutoClientService(name = APP_NAME, version = APP_VER, contextPath = APP_CONTEXT_PATH)
public interface ApiVersionService {

    /**
     * Get /v{2}/apiversion/validateCtl
     * @return
     */
    @AutoClientMethod(mode = AutoClientMode.GET, path = "/apiversion/validateCtl", version = "v2")
    String validateControllerVersion();

    /**
     * Get /v{2.1,3}/apiversion/validateMethod
     * @return
     */
    @AutoClientMethod(mode = AutoClientMode.GET, path = "/apiversion/validateMethod", version = "v3")
    String validateMethodVersion();
}
