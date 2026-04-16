package com.iflytek.auto.ai-agent.api.service;

import com.iflytek.auto.framework.api.annotation.AutoClientMethod;
import com.iflytek.auto.framework.api.annotation.AutoClientMode;
import com.iflytek.auto.framework.api.annotation.AutoClientRequestBody;
import com.iflytek.auto.framework.api.annotation.AutoClientService;
import com.iflytek.auto.ai-agent.api.entry.SampleData;
import com.iflytek.auto.ai-agent.api.entry.SampleData2;

import static com.iflytek.auto.ai-agent.api.service.ServiceConstant.*;

@AutoClientService(name = APP_NAME, version = APP_VER, contextPath = APP_CONTEXT_PATH)
public interface HeloService {

    /**
     * GET /v1/helo/world
     * @param message
     * @return
     */
    @AutoClientMethod(mode = AutoClientMode.GET, path = "/helo/world?message={+message}")
    String heloWorld(String message);

    /**
     * GET /v1/helo/empty
     */
    @AutoClientMethod(mode = AutoClientMode.GET, path = "/helo/empty")
    void heloEmpty();

    /**
     * POST /v1/helo/array
     * @param dataArray
     * @return
     */
    @AutoClientMethod(mode = AutoClientMode.POST, path = "/helo/array")
    SampleData[] heloArray(@AutoClientRequestBody SampleData[] dataArray);

    /**
     * POST /v1/helo/generic
     * @param dataArray
     * @return
     */
    @AutoClientMethod(mode = AutoClientMode.POST, path = "/helo/generic")
    SampleData2<SampleData>[] heloGeneric(@AutoClientRequestBody SampleData2<SampleData>[] dataArray);
}
