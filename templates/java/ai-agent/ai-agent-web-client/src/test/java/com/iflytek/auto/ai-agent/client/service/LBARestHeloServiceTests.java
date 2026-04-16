package com.iflytek.auto.ai-agent.client.service;

import com.iflytek.auto.ai-agent.api.entry.SampleData;
import com.iflytek.auto.ai-agent.api.entry.SampleData2;
import com.iflytek.auto.ai-agent.api.service.HeloService;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.util.Assert;

import static com.iflytek.auto.ai-agent.client.util.JsonUtils.json;

@SpringBootTest(args = "--spring.profiles.active=lba")
@Slf4j
class LBARestHeloServiceTests {

	@Autowired(required = false)
	private HeloService restHeloService;

	@Test
	public void testHeloWorld(){
		String message = restHeloService.heloWorld("test!!!");
		log.info(message);
		Assert.isTrue("Helo world!!!test!!!".equalsIgnoreCase(message), "return value is error");
	}

	@Test
	public void testHeloEmpty() {
		restHeloService.heloEmpty();
	}

	@Test
	public void testHeloArray() {
		SampleData[] array = new SampleData[2];

		SampleData sampleData1 = new SampleData();
		sampleData1.setTestA("A1");
		sampleData1.setTestB("B1");
		array[0] = sampleData1;

		SampleData sampleData2 = new SampleData();
		sampleData2.setTestA("A2");
		sampleData2.setTestB("B2");
		array[1] = sampleData2;

		SampleData[] result = restHeloService.heloArray(array);

		log.info("result:" + json(result));

		Assert.isTrue(equalsSampleData(array, result), "return value is error");
	}

	boolean equalsSampleData(SampleData[] obj1, SampleData[] obj2){
		if(obj1.length != obj2.length)
			return false;

		for(int i = 0; i<obj1.length; i++){
			SampleData data1 = obj1[i];
			SampleData data2 = obj2[i];

			if(!data1.getTestA().equalsIgnoreCase(data2.getTestA()))
				return false;

			if(!data1.getTestB().equalsIgnoreCase(data2.getTestB()))
				return false;
		}

		return true;
	}

	@Test
	public void testHeloGeneric() {
		SampleData2<SampleData>[] array = new SampleData2[2];

		SampleData2<SampleData> obj1 = new SampleData2<>();
		obj1.setName("name a");
		SampleData sampleData1 = new SampleData();
		sampleData1.setTestA("A1");
		sampleData1.setTestB("B1");
		obj1.setData(sampleData1);
		array[0] = obj1;

		SampleData2<SampleData> obj2 = new SampleData2<>();
		obj2.setName("name b");
		SampleData sampleData2 = new SampleData();
		sampleData2.setTestA("A2");
		sampleData2.setTestB("B2");
		obj2.setData(sampleData2);
		array[1] = obj2;

		SampleData2<SampleData>[] result = restHeloService.heloGeneric(array);

		log.info("result:" + json(result));

		Assert.isTrue(equalsSampleData(array, result), "return value is error");
	}

	boolean equalsSampleData(SampleData2<SampleData>[] obj1, SampleData2<SampleData>[] obj2){
		if(obj1.length != obj2.length)
			return false;

		for(int i = 0; i<obj1.length; i++){
			SampleData2<SampleData> data1 = obj1[i];
			SampleData2<SampleData> data2 = obj2[i];

			if(!data1.getName().equalsIgnoreCase(data2.getName()))
				return false;

			if(!data1.getData().getTestA().equalsIgnoreCase(data2.getData().getTestA()))
				return false;

			if(!data1.getData().getTestB().equalsIgnoreCase(data2.getData().getTestB()))
				return false;
		}

		return true;
	}
}
