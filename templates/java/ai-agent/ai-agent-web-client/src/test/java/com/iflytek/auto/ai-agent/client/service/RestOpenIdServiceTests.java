package com.iflytek.auto.ai-agent.client.service;

import com.iflytek.auto.ai-agent.api.service.OpenIdService;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.util.Assert;

@SpringBootTest(args = "--spring.profiles.active=base")
@Slf4j
class RestOpenIdServiceTests {

	@Autowired
	private OpenIdService openIdService;

	@Test
	public void testValidateGetOpenId() {
		String openId = openIdService.validateGetOpenId("123456");
		log.info(openId);
		Assert.isTrue("123456".equalsIgnoreCase(openId), "");
	}
}
