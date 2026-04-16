package com.iflytek.auto.ai-agent.sleweb.web.controller;

import com.iflytek.auto.ai-agent.api.entry.SampleData;
import com.iflytek.auto.ai-agent.api.entry.SampleData2;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

@RestController
@RequestMapping("/helo")
public class HeloController {

    @GetMapping("/world")
    public String heloWorld(String message) {
        return "Helo world!!!" + message;
    }

    @GetMapping("/empty")
    public void heloEmpty() {
        // This method is intentionally left blank because it's a placeholder for future implementation.
    }

    @PostMapping("/array")
    public SampleData[] heloArray(@RequestBody SampleData[] dataArray) {
        return dataArray;
    }

    @PostMapping("/generic")
    public SampleData2<SampleData>[] heloGeneric(@RequestBody SampleData2<SampleData>[] dataArray){
        return dataArray;
    }
}
