package com.iflytek.auto.ai-agent.client.service;

import com.iflytek.auto.ai-agent.api.entry.SampleData;
import com.iflytek.auto.ai-agent.api.service.ResponseDataService;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.util.Assert;

import static com.iflytek.auto.ai-agent.client.util.JsonUtils.json;

@SpringBootTest(args = "--spring.profiles.active=base")
@Slf4j
class RestResponseDataServiceTests {

	@Autowired
	private ResponseDataService responseDataService;

	@Test
	public void testGetData() {
		SampleData sampleData = responseDataService.getData();
		log.info(json(sampleData));
		Assert.isTrue(sampleData != null
				&& "Test A".equalsIgnoreCase(sampleData.getTestA())
				&& "Test B".equalsIgnoreCase(sampleData.getTestB()),
				"");
	}

	@Test
	public void testGetResp() {
		SampleData sampleData = responseDataService.getResp();
		log.info(json(sampleData));
		Assert.isTrue(sampleData != null
						&& "Test A".equalsIgnoreCase(sampleData.getTestA())
						&& "Test B".equalsIgnoreCase(sampleData.getTestB()),
				"");
	}
}
