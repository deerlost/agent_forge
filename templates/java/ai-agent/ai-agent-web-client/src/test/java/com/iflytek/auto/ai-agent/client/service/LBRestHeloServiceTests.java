package com.iflytek.auto.ai-agent.client.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest(args = "--spring.profiles.active=lb")
@Slf4j
class LBRestHeloServiceTests extends RestHeloServiceTests {

}
