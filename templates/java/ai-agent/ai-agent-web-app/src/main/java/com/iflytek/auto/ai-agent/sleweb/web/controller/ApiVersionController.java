package com.iflytek.auto.ai-agent.sleweb.web.controller;

import com.iflytek.auto.framework.web.web.mapping.ApiVersion;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@ApiVersion("v2")
@RequestMapping("/apiversion")
public class ApiVersionController {

    @GetMapping("/validateCtl")
    public String validateControllerVersion(String apiVersion) {
        return  "api version " + apiVersion + " not 404";
    }


    @GetMapping("/validateMethod")
    @ApiVersion({"v2.1", "v3"})
    public String validateMethodVersion(String apiVersion) {
        return "api version " + apiVersion + " not 404";
    }
}
