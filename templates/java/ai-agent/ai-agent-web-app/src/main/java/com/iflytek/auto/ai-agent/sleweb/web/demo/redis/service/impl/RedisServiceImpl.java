package com.iflytek.auto.ai-agent.sleweb.web.demo.redis.service.impl;

import com.iflytek.auto.ai-agent.sleweb.web.entry.entity.redis.RedisLock;
import com.iflytek.auto.ai-agent.sleweb.web.entry.entity.redis.UserRedis;
import com.iflytek.auto.ai-agent.sleweb.web.demo.redis.service.RedisService;
import com.iflytek.auto.ai-agent.sleweb.web.demo.redis.util.RedisLockUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ClassPathResource;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.scripting.support.ResourceScriptSource;
import org.springframework.stereotype.Service;

import java.util.Arrays;
import java.util.concurrent.TimeUnit;

/**
 * @ProjectName: auto-sample-root
 * @Package: com.iflytek.auto.ai-agent.sleweb.web.demo.redis.service.impl
 * @ClassName: RedisServiceImpl
 * @Author: cwli10
 * @Description:
 * @Date: 2022/11/22 16:45
 * @Version: 1.0
 */
@Service
@Slf4j
public class RedisServiceImpl implements RedisService {

    private RedisTemplate redisTemplate;

    @Autowired
    public void setRedisTemplate(RedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    @Override
    public void save(String key, UserRedis userRedis) {
        redisTemplate.opsForValue().set(key, userRedis);
    }

    @Override
    public Boolean delete(String key) {
        Boolean delete = redisTemplate.delete(key);
        return delete;
    }

    @Override
    public UserRedis get(String key) {
        return (UserRedis) redisTemplate.opsForValue().get(key);
    }

    @Override
    public void setTime(String key, Long time) {
        redisTemplate.expire(key, time, TimeUnit.SECONDS);
    }

    @Override
    public Long getTime(String key) {
        return redisTemplate.getExpire(key);
    }


    /**
    * redis分布式锁加上lua脚本案例
    * @param key
    */
    @Override
    public void lock(String key) {
        //加锁
        RedisLock lock = RedisLockUtils.instance().lock(key, 20000);
        try {
            if (lock.getLock()) {
                log.info("key:{} 锁定成功，开始处理业务", key);
//                Thread.sleep(1000);
                log.info("key:{} 业务处理完成", key);
            }
        } finally {
            //解锁
            RedisLockUtils.instance().unLock(key, lock.getValue());
        }
    }

    /**
    * lua使用
    */
    @Override
    public void lua() {
        //解析lua脚本
        DefaultRedisScript<Long> script = new DefaultRedisScript<>();
        script.setResultType(Long.class);
        script.setScriptSource(new ResourceScriptSource(new ClassPathResource("lua/demo.lua")));
        Long execute = (Long) redisTemplate.execute(script, Arrays.asList("demo:test"), "英语");
        log.info("匹配:{}",(execute == 11111 ? "成功" : "失败"));
    }

}
