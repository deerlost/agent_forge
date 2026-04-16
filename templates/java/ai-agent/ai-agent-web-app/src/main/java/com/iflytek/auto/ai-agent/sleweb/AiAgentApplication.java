package com.iflytek.auto.ai-agent.sleweb;

import com.iflytek.auto.framework.web.FrameworkWebConfiguretion;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.mybatis.spring.annotation.MapperScan;
@SpringBootApplication
@FrameworkWebConfiguretion
@MapperScan({"com.**.mapper"})
public class AiAgentApplication {

    public static void main(String[] args) {
        SpringApplication.run(AiAgentApplication.class, args);
    }
}
