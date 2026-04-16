package com.iflytek.auto.ai-agent.api.service;

import com.iflytek.auto.framework.api.annotation.AutoClientMethod;
import com.iflytek.auto.framework.api.annotation.AutoClientMode;
import com.iflytek.auto.framework.api.annotation.AutoClientService;
import  com.iflytek.auto.ai-agent.api.entry.SampleData;

import static com.iflytek.auto.ai-agent.api.service.ServiceConstant.*;

@AutoClientService(name = APP_NAME, version = APP_VER, contextPath = APP_CONTEXT_PATH)
public interface ResponseDataService {

    /**
     * GET /v1/response/data
     * @return
     */
    @AutoClientMethod(mode = AutoClientMode.GET, path = "/response/data")
    SampleData getData();

    /**
     * GET /v1/response/resp
     * @return
     */
    @AutoClientMethod(mode = AutoClientMode.GET, path = "/response/resp")
    SampleData getResp();
}
