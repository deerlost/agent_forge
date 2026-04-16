package com.iflytek.auto.ai-agent.sleweb.web.controller;

import com.iflytek.auto.ai-agent.api.entry.SampleData;
import com.iflytek.auto.ai-agent.api.entry.SampleData2;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static com.iflytek.auto.ai-agent.sleweb.util.JsonUtils.json;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultHandlers.log;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@Slf4j
public class HeloControllerTests {

    @Autowired
    private MockMvc mockMvc;

    @Test
    public void testHeloWorld() throws Exception {
        mockMvc.perform(get( "/v1/helo/world?message={message}", "测试！！！")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(log())
                .andExpect(status().isOk())
                .andExpect(content().json("{\"code\":200,\"data\":\"Helo world!!!测试！！！\"}"));
    }

    @Test
    public void testHeloEmpty() throws Exception {
        mockMvc.perform(get( "/v1/helo/empty")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(log())
                .andExpect(status().isOk())
                .andExpect(content().json("{\"code\":200}"));
    }

    @Test
    public void testHeloArray() throws Exception {
        SampleData[] array = new SampleData[2];

        SampleData sampleData1 = new SampleData();
        sampleData1.setTestA("A1");
        sampleData1.setTestB("B1");
        array[0] = sampleData1;

        SampleData sampleData2 = new SampleData();
        sampleData2.setTestA("A2");
        sampleData2.setTestB("B2");
        array[1] = sampleData2;

        mockMvc.perform(post( "/v1/helo/array")
                        .contentType(MediaType.APPLICATION_JSON).content(json(array)))
                .andDo(log())
                .andExpect(status().isOk())
                .andExpect(content().json("{\"code\":200,\"data\":[{\"testA\":\"A1\",\"testB\":\"B1\"},{\"testA\":\"A2\",\"testB\":\"B2\"}]}"));
    }

    @Test
    public void testHeloGeneric() throws Exception {
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

        mockMvc.perform(post("/v1/helo/generic")
                        .contentType(MediaType.APPLICATION_JSON).content(json(array)))
                .andDo(log())
                .andExpect(status().isOk())
                .andExpect(content().json("{\"code\":200,\"data\":[{\"name\":\"name a\",\"data\":{\"testA\":\"A1\",\"testB\":\"B1\"}},{\"name\":\"name b\",\"data\":{\"testA\":\"A2\",\"testB\":\"B2\"}}]}"));
    }
}
