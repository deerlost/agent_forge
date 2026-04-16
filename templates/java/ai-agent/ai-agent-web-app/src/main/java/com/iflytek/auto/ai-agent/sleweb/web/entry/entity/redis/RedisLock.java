package com.iflytek.auto.ai-agent.sleweb.web.entry.entity.redis;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * @ProjectName: auto-sample-root
 * @Package: com.iflytek.auto.ai-agent.sleweb.web.entry.entity.redis
 * @ClassName: RedisLock
 * @Author: cwli10
 * @Description:
 * @Date: 2022/12/2 14:37
 * @Version: 1.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RedisLock {
    private String value;
    private Boolean lock;
}
