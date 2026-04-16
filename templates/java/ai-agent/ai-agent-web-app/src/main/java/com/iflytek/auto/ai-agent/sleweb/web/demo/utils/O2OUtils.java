package com.iflytek.auto.ai-agent.sleweb.web.demo.utils;

import org.springframework.beans.BeanUtils;

/**
 * @className: com.iflytek.auto.ai-agent.sleweb.web.demo.utils-> O2OUtils
 * @description: BO、DO转换工具类
 * @author: weiwang111@iflytek.com
 * @createDate: 2022-12-05 19:23
 * @version: 1.0
 * @todo:
 */
public class O2OUtils {

    private O2OUtils() {
        throw new IllegalStateException("Utility class");
    }

    /**
     * @title: o2o
     * @createAuthor: weiwang111@iflytek.com
     * @createDate: 2022/12/5 19:50
     * @description: BO、DO转换
     * @params: [source, dest]
     * @return: D
     */
    public static <S extends Object, D extends Object> D o2o(S source, D dest) {
        if (null == source) {
            return dest;
        }
        BeanUtils.copyProperties(source, dest);
        return dest;
    }
}
