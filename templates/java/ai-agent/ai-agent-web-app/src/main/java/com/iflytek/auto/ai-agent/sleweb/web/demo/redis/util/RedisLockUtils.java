package com.iflytek.auto.ai-agent.sleweb.web.demo.redis.util;

import com.iflytek.auto.ai-agent.sleweb.web.entry.entity.redis.RedisLock;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ClassPathResource;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.scripting.support.ResourceScriptSource;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import java.util.Arrays;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

/**
 * @ProjectName: auto-sample-root
 * @Package: com.iflytek.auto.ai-agent.sleweb.web.demo.redis
 * @ClassName: RedisLockUtils
 * @Author: cwli10
 * @Description:
 * @Date: 2022/12/2 10:58
 * @Version: 1.0
 */
@Component
@Slf4j
public class RedisLockUtils {

    private static RedisLockUtils redisLock;

    private RedisTemplate redisTemplate;

    public static RedisLockUtils instance() {
        return redisLock;
    }

    @SuppressWarnings("all")
    @PostConstruct
    public void init() {
        redisLock = this;
    }

    public RedisLockUtils(RedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    /**
    * 加锁
    * @param key
    * @param time
    * @return
    */
    public RedisLock lock(String key, long time) {
        String value = UUID.randomUUID().toString();
        Boolean lock = redisTemplate.opsForValue().setIfAbsent(key, value, time, TimeUnit.MILLISECONDS);
        return new RedisLock(value, lock);
    }

    /**
    * 解锁
    * @param key
    * @param value
    */
    public void unLock(String key, String value) {
        //解析lua脚本
        DefaultRedisScript<Long> script = new DefaultRedisScript<>();
        script.setResultType(Long.class);
        script.setScriptSource(new ResourceScriptSource(new ClassPathResource("lua/lock.lua")));
        Long execute = (Long) redisTemplate.execute(script, Arrays.asList(key), value);
        log.info("释放锁 : {},execute:{}" ,(execute == 0 ? "失败" : "成功"), value, execute);
    }
}
