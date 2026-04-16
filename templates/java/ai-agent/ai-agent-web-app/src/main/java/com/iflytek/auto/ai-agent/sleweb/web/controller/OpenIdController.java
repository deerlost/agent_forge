package com.iflytek.auto.ai-agent.sleweb.web.controller;

import com.iflytek.auto.ai-agent.sleweb.web.entry.OpenProject;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/openId")
public class OpenIdController {

    @GetMapping("validate")
    public String validateGetOpenId(OpenProject openProject){
        if(openProject == null) {
            return null;
        }

        return openProject.getOpenId();
    }
}
