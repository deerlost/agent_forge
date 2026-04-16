package com.iflytek.auto.ai-agent.sleweb.web.demo.mp.controller;

import com.iflytek.auto.framework.web.web.mapping.ApiVersion;
import com.iflytek.auto.ai-agent.api.entry.bo.mp.UserBO;
import com.iflytek.auto.ai-agent.sleweb.web.demo.mp.service.IUserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

import java.util.List;

/**
 * @title: 用户管理Controller
 * @createAuthor: weiwang111@iflytek.com
 * @createDate: 2022/12/2 8:26
 * @description: TODO
 * @params: * @param null:
 * @return: 注意事项：在自定义mybatis-xml时，为了避免增加系统复杂性和系统负担，不要使用【级联查询】.如：
 * <association property="dep" column="emp_dep" javaType="com.worldly.config.entity.Department">
 * <collection column="dep_id" property="employeeList" javaType="java.util.List" ofType="com.worldly.config.entity.Employee" select="selectEmpBydepId"/>
 */
@ApiVersion("v2")
@RestController
@RequestMapping("/user")
public class UserController {


    private IUserService userService;

    /**
     * @title: 根据用户ID查询用户信息
     * @createAuthor: weiwang111@iflytek.com
     * @createDate: 2022/12/2 8:27
     * @description: TODO
     * @params: [id]
     * @return: com.iflytek.auto.sample.sleweb.web.demo.mp.domain.vo.UserBO
     */
    @RequestMapping("/queryById")
    public UserBO queryById(@RequestParam("id") Long id) {
        return userService.getById(id);
    }

    @PostMapping("/queryByCondition")
    public List<UserBO> queryByCondition(@RequestBody UserBO bo) {
        return userService.queryByCondition(bo);
    }

    /**
     * @title: 根据用户ID更新用户信息
     * @createAuthor: weiwang111@iflytek.com
     * @createDate: 2022/12/2 8:27
     * @description: TODO
     * @params: [dto]
     * @return: int
     */
    @PostMapping("/updateById")
    public int update(@RequestBody UserBO bo) {
        return userService.updateById(bo);
    }

    /**
     * @title: 根据用户ID删除用户信息
     * @createAuthor: weiwang111@iflytek.com
     * @createDate: 2022/12/2 8:28
     * @description: TODO
     * @params: [id]
     * @return: int
     */
    @RequestMapping("/deleteById")
    public int delete(@RequestParam("id") Long id) {
        return userService.deleteById(id);
    }

    /**
     * @title: 新增用户
     * @createAuthor: weiwang111@iflytek.com
     * @createDate: 2022/12/2 8:28
     * @description: TODO
     * @params: [dto]
     * @return: int
     */
    @PostMapping("/save")
    public int save(UserBO bo) {
        return userService.save(bo);
    }

    @Autowired
    public void setUserService(IUserService userService) {
        this.userService = userService;
    }
}
