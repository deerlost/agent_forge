package com.iflytek.auto.ai-agent.sleweb.web.demo.mp.service;

import com.iflytek.auto.ai-agent.api.entry.bo.mp.UserBO;

import java.util.List;

/**
 * @className: com.iflytek.auto.ai-agent.sleweb.web.demo.mp.service-> IUserService
 * @description: 用户管理接口
 * @author: weiwang111@iflytek.com
 * @createDate: 2022-12-02 7:37
 * @version: 1.0
 * @todo:
 */
public interface IUserService {

    /**
    * 通过id获取用户信息
    * @param id
    * @return
    */
    UserBO getById(Long id);

    /**
    * 通过条件查询用户信息
    * @param bo
    * @return
    */
    List<UserBO> queryByCondition(UserBO bo);

    /**
    * 修改用户信息
    * @param bo
    * @return
    */
    int updateById(UserBO bo);

    /**
    * 删除用户信息
    * @param id
    * @return
    */
    int deleteById(Long id);

    /**
    * 新增用户信息
    * @param userBO
    * @return
    */
    int save(UserBO userBO);
}
