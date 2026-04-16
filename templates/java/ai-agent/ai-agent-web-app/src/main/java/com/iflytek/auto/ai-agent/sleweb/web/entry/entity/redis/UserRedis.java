package com.iflytek.auto.ai-agent.sleweb.web.entry.entity.redis;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Date;

/**
 * @ProjectName: auto-sample-root
 * @Package: com.iflytek.auto.ai-agent.sleweb.web.entry.entity.redis
 * @ClassName: UserRedis
 * @Author: cwli10
 * @Description:
 * @Date: 2022/11/22 16:41
 * @Version: 1.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserRedis {
    private String id;

    private String userName;

    private String addr;

    private Integer gender;
}
