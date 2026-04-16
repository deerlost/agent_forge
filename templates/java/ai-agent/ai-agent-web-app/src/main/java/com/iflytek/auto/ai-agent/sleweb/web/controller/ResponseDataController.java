package com.iflytek.auto.ai-agent.sleweb.web.controller;

import com.iflytek.auto.framework.api.entry.ResponseData;
import com.iflytek.auto.ai-agent.api.entry.SampleData;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/response")
public class ResponseDataController {

    @GetMapping("/data")
    public SampleData getData() {
        SampleData sampleData = new SampleData();
        sampleData.setTestA("Test A");
        sampleData.setTestB("Test B");

        return sampleData;
    }

    @GetMapping("/resp")
    public ResponseData getResp() {
        SampleData sampleData = new SampleData();
        sampleData.setTestA("Test A");
        sampleData.setTestB("Test B");

        return ResponseData.of(sampleData);
    }

}
