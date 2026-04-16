package com.iflytek.auto.ai-agent.client.service;

import com.iflytek.auto.framework.api.exception.BizException;
import com.iflytek.auto.ai-agent.api.service.ExceptionService;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.util.Assert;

@SpringBootTest(args = "--spring.profiles.active=base")
@Slf4j
class RestExceptionServiceTests {

	@Autowired
	private ExceptionService exceptionService;

	@Test
	public void testValidateExceptionResponse(){
		try {
			exceptionService.validateExceptionResponse();
		}catch (BizException e){
			log.info("", e);
			Assert.isTrue(e.getCode() == 1001, "");
		}
	}

	@Test
	public void testValidateBizExceptionResponse(){
		try {
			exceptionService.validateBizExceptionResponse();
		}catch (BizException e){
			log.info("", e);
			Assert.isTrue(e.getCode() == 1002, "");
		}
	}
}
