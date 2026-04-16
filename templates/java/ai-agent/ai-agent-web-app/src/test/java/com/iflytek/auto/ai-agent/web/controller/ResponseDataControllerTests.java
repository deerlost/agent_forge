package com.iflytek.auto.ai-agent.sleweb.web.controller;

import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultHandlers.log;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@Slf4j
public class ResponseDataControllerTests {

    @Autowired
    private MockMvc mockMvc;

    @Test
    public void testGetData() throws Exception {
        mockMvc.perform(get( "/v1/response/data")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(log())
                .andExpect(status().isOk())
                .andExpect(content().json("{\"code\":200,\"data\":{\"testA\":\"Test A\",\"testB\":\"Test B\"}}"));
    }

    @Test
    public void testGetResp() throws Exception {
        mockMvc.perform(get( "/v1/response/resp")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(log())
                .andExpect(status().isOk())
                .andExpect(content().json("{\"code\":200,\"data\":{\"testA\":\"Test A\",\"testB\":\"Test B\"}}"));
    }
}
