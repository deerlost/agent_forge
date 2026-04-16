package com.iflytek.auto.ai-agent.sleweb.web.demo.redis.service;

import com.iflytek.auto.ai-agent.sleweb.web.entry.entity.redis.UserRedis;

public interface RedisService {

    /**
    * 新增key
    * @param key
    * @param userRedis
    */
    void save(String key, UserRedis userRedis);

    /**
    * 删除key
    * @param key
    * @return
    */
    Boolean delete(String key);

    /**
    * 获取key对应value
    * @param key
    * @return
    */
    UserRedis get(String key);

    /**
    * 设置过期时间
    * @param key
    * @param time
    */
    void setTime(String key, Long time);

    /**
    * 获取过期时间
    * @param key
    * @return
    */
    Long getTime(String key);

    /**
    * redis锁
    * @param key
    */
    void lock(String key);

    /**
    * lua脚本
    */
    void lua();
}
