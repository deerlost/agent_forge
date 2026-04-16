package com.iflytek.auto.ai-agent.sleweb.web.demo.redis.config;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.PropertyAccessor;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.jsontype.impl.LaissezFaireSubTypeValidator;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.Jackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

/**
 * @ProjectName: auto-sample-root
 * @Package: com.iflytek.auto.ai-agent.sleweb.web.demo.redis.config
 * @ClassName: RedisConfig
 * @Author: cwli10
 * @Description: redis配置类
 * @Date: 2022/11/22 16:20
 * @Version: 1.0
 */
@Configuration
public class RedisConfig {

    /**
     * 自定义RedisTemplate方法序列化配置
     *
     * @param redisConnectionFactory
     * @return
     */
    @Bean
    @SuppressWarnings("all")
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory redisConnectionFactory) {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(redisConnectionFactory);
        //自定义Jackson序列化配置
        Jackson2JsonRedisSerializer jsonRedisSerializer = new Jackson2JsonRedisSerializer(Object.class);
        ObjectMapper objectMapper = new ObjectMapper();
        objectMapper.setVisibility(PropertyAccessor.ALL, JsonAutoDetect.Visibility.ANY);
        objectMapper.activateDefaultTyping(LaissezFaireSubTypeValidator.instance, ObjectMapper.DefaultTyping.NON_FINAL);
        jsonRedisSerializer.setObjectMapper(objectMapper);
        //key使用String的序列化方式
        StringRedisSerializer stringRedisSerializer = new StringRedisSerializer();
        template.setKeySerializer(stringRedisSerializer);
        //hash的key也是用String的序列化方式
        template.setHashKeySerializer(stringRedisSerializer);
        //value的key使用jackson的序列化方式
        template.setValueSerializer(jsonRedisSerializer);
        //hash的value也是用jackson的序列化方式
        template.setHashValueSerializer(jsonRedisSerializer);
        //加上这个事物支持，反而会报错。这个问题搞了很久，都没找到原因。错误：java.lang.UnsupportedOperationException: null；如果有读者知道为什么，请一定要私信我，谢谢！！！！
        //网上都说要加这个才能让redis支持事物。我就很懵逼了,为什么我加了报错，不加反而可以用。这个问题困扰了很久也没找到原因
        //template.setEnableTransactionSupport(true);
        template.afterPropertiesSet();
        return template;
    }

}
