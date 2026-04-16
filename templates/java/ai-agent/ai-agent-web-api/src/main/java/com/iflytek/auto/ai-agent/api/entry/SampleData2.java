package com.iflytek.auto.ai-agent.api.entry;

import lombok.Data;

@Data
public class SampleData2 <T> {
    private String name;
    private T data;
}
