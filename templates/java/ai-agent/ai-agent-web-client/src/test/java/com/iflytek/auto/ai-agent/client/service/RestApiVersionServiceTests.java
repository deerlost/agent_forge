package com.iflytek.auto.ai-agent.client.service;

import com.iflytek.auto.ai-agent.api.service.ApiVersionService;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.util.Assert;

@SpringBootTest(args = "--spring.profiles.active=base")
@Slf4j
class RestApiVersionServiceTests {

	@Autowired
	private ApiVersionService apiVersionService;

	@Test
	public void testValidateControllerVersion(){
		String message = apiVersionService.validateControllerVersion();
		log.info(message);
		Assert.isTrue("api version v2 not 404".equalsIgnoreCase(message), "return value is error");
	}

	@Test
	public void testValidateMethodVersion(){
		String message = apiVersionService.validateMethodVersion();
		log.info(message);
		Assert.isTrue("api version v3 not 404".equalsIgnoreCase(message), "return value is error");
	}
}
