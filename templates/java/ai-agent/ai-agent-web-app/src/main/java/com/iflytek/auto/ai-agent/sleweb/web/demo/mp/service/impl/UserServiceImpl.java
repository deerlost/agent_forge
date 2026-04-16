package com.iflytek.auto.ai-agent.sleweb.web.demo.mp.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.iflytek.auto.ai-agent.api.entry.bo.mp.UserBO;
import com.iflytek.auto.ai-agent.sleweb.web.demo.mp.dao.mapper.generate.UserMapper;
import com.iflytek.auto.ai-agent.sleweb.web.demo.mp.service.IUserService;
import com.iflytek.auto.ai-agent.sleweb.web.demo.utils.O2OUtils;
import com.iflytek.auto.ai-agent.sleweb.web.entry.entity.UserDO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.List;
import java.util.stream.Collectors;

/**
 * @className: com.iflytek.auto.ai-agent.sleweb.web.demo.mp.service.impl-> UserServiceImpl
 * @description: 用户管理实现类
 * @author: weiwang111@iflytek.com
 * @createDate: 2022-12-02 7:38
 * @version: 1.0
 * @todo:
 */

@Service
public class UserServiceImpl implements IUserService {

    private UserMapper userMapper;

    @Override
    public UserBO getById(Long id) {
        return O2OUtils.o2o(userMapper.selectById(id), new UserBO());
    }

    @Override
    public List<UserBO> queryByCondition(UserBO bo) {
        return userMapper
                .selectList(bo2QueryWrapper(bo))
                .stream()
                .map(userDO -> O2OUtils.o2o(userDO, new UserBO()))
                .collect(Collectors.toList());
    }

    @Override
    public int updateById(UserBO bo) {
        return userMapper.updateById(O2OUtils.o2o(bo, new UserDO()));
    }

    @Override
    public int deleteById(Long id) {
        return userMapper.deleteById(id);
    }

    @Override
    public int save(UserBO bo) {
        return userMapper.insert(O2OUtils.o2o(bo, new UserDO()));
    }

    @Autowired
    private void setUserMapper(UserMapper userMapper) {
        this.userMapper = userMapper;
    }

    /**
     * @title: bo2QueryWrapper
     * @createAuthor: weiwang111@iflytek.com
     * @createDate: 2022/12/5 19:55
     * @description: 构造查询条件
     * @params: [bo]
     * @return: com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<com.iflytek.auto.sample.sleweb.web.entry.entity.UserDO>
     */
    private QueryWrapper<UserDO> bo2QueryWrapper(UserBO bo) {
        QueryWrapper<UserDO> queryWrapper = new QueryWrapper<>();
        if (null == bo) {
            return queryWrapper;
        }
        if (StringUtils.hasLength(bo.getName())) {
            // 等于
            queryWrapper.eq("name", bo.getName());
        }
        if (null != bo.getAge()) {
            // 范围条件
            queryWrapper.between("age", bo.getAge() - 5, bo.getAge() + 5);
        }
        return queryWrapper;
    }
}
