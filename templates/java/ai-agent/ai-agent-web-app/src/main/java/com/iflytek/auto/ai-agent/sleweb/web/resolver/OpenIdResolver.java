package com.iflytek.auto.ai-agent.sleweb.web.resolver;

import com.iflytek.auto.framework.web.web.annotation.AutoHandlerMethodArgumentResolver;
import com.iflytek.auto.ai-agent.sleweb.web.entry.OpenProject;
import org.springframework.core.MethodParameter;
import org.springframework.stereotype.Component;
import org.springframework.util.ObjectUtils;
import org.springframework.web.bind.support.WebDataBinderFactory;
import org.springframework.web.context.request.NativeWebRequest;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.method.support.ModelAndViewContainer;

/**
 * 当前实现没有特别意义，仅仅用来演示
 */
@AutoHandlerMethodArgumentResolver
@Component
public class OpenIdResolver implements HandlerMethodArgumentResolver {
    @Override
    public boolean supportsParameter(MethodParameter parameter) {
        return parameter.getParameterName().equalsIgnoreCase("openProject")
                && parameter.getParameterType() == OpenProject.class;
    }

    @Override
    public Object resolveArgument(MethodParameter parameter, ModelAndViewContainer mavContainer, NativeWebRequest webRequest, WebDataBinderFactory binderFactory) throws Exception {
        String openId = webRequest.getParameter("openId");
        if(ObjectUtils.isEmpty(openId)) {
            return null;
        }

        OpenProject openProject = new OpenProject();
        openProject.setOpenId(openId);

        return openProject;
    }
}
