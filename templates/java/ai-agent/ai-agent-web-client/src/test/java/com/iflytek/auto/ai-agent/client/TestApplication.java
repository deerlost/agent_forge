package com.iflytek.auto.ai-agent.client;


import com.iflytek.auto.framework.sdk.FrameworkSdkConfiguretion;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@FrameworkSdkConfiguretion
public class TestApplication {

    public static void main(String[] args) {
        SpringApplication.run(TestApplication.class, args);
    }
}
