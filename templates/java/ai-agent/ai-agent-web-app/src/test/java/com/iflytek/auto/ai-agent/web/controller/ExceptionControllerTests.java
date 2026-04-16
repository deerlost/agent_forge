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
public class ExceptionControllerTests {

    @Autowired
    private MockMvc mockMvc;

    @Test
    public void testValidateExceptionResponse() throws Exception {
        mockMvc.perform(get( "/v1/exception/validate")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(log())
                .andExpect(status().isOk())
                .andExpect(content().json("{\"code\":1001,\"message\":\"未知异常\"}"))
                .andReturn();
    }

    @Test
    public void testValidateBizExceptionResponse() throws Exception {
        mockMvc.perform(get( "/v1/exception/biz")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(log())
                .andExpect(status().isOk())
                .andExpect(content().json("{\"code\":1002,\"message\":\"测试\"}"));
    }
}
