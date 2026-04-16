package com.iflytek.auto.ai-agent.sleweb.web.handler;

import com.iflytek.auto.framework.api.exception.BizException;
import com.iflytek.auto.framework.web.web.annotation.AutoHandlerInterceptor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.HandlerInterceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.util.Objects;

@AutoHandlerInterceptor(name = "sign-verify")
@Configuration
public class SignVerifyHandlerInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        String openId = request.getParameter("openId");

        checkSign(openId);

        return true;
    }

    private void checkSign(String openId){
        if(Objects.isNull(openId)) {
            throw new BizException(1002, "签名错误");
        }

    }
}
