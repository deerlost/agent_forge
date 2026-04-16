//package com.iflytek.auto.ai-agent.client;
//
//import com.iflytek.auto.framework.api.exception.BizException;
//import com.iflytek.auto.framework.sdk.converter.AutoMappingJackson2HttpMessageConverter;
//import org.apache.http.client.HttpClient;
//import org.apache.http.impl.client.HttpClientBuilder;
//import org.apache.http.impl.conn.PoolingHttpClientConnectionManager;
//import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
//import org.springframework.boot.web.client.RestTemplateBuilder;
//import org.springframework.cloud.client.loadbalancer.LoadBalanced;
//import org.springframework.context.annotation.Bean;
//import org.springframework.context.annotation.Configuration;
//import org.springframework.http.HttpRequest;
//import org.springframework.http.MediaType;
//import org.springframework.http.client.*;
//import org.springframework.web.client.ResponseErrorHandler;
//import org.springframework.web.client.RestTemplate;
//
//import java.io.IOException;
//import java.nio.charset.Charset;
//import java.nio.charset.StandardCharsets;
//import java.util.ArrayList;
//import java.util.List;
//
//@Configuration
//public class RestTemplateConfigure {
//
//    @Bean("auto.framework.bizRestTemplate")
//    @ConditionalOnMissingBean
//    public RestTemplate bizRestTemplate() {
//        return buildRestTemplate();
//    }
//
//    @Bean("auto.framework.bizLBRestTemplate")
//    @LoadBalanced
//    @ConditionalOnMissingBean
//    public RestTemplate bizLBRestTemplate() {
//        return buildRestTemplate();
//    }
//
//    private RestTemplate buildRestTemplate() {
//        PoolingHttpClientConnectionManager connectionPoolManager = new PoolingHttpClientConnectionManager();
//        connectionPoolManager.setMaxTotal(1000);
//        connectionPoolManager.setDefaultMaxPerRoute(400);
//
//        HttpClient httpClient = HttpClientBuilder.create()
//                .setConnectionManager(connectionPoolManager).build();
//
//        HttpComponentsClientHttpRequestFactory httpRequestFactory = new HttpComponentsClientHttpRequestFactory();
//        httpRequestFactory.setHttpClient(httpClient);
//        httpRequestFactory.setConnectionRequestTimeout(3000);
//        httpRequestFactory.setConnectTimeout(3000);
//        httpRequestFactory.setReadTimeout(10000);
//
//        RestTemplate restTemplate = new RestTemplateBuilder().requestFactory(()-> httpRequestFactory).build();
//        restTemplate.getMessageConverters().clear();
//        restTemplate.getMessageConverters().add(new AutoMappingJackson2HttpMessageConverter());
//        restTemplate.getInterceptors().add(new StdClientHttpRequestInterceptor());
//        restTemplate.setErrorHandler(new StdResponseErrorHandler());
//        restTemplate.getClientHttpRequestInitializers().add(new StdClientHttpRequestInitializer());
//
//        return restTemplate;
//    }
//
//
//    private class StdClientHttpRequestInitializer implements ClientHttpRequestInitializer {
//
//        @Override
//        public void initialize(ClientHttpRequest request) {
//            request.getHeaders().setContentType(MediaType.APPLICATION_JSON);
//
//            List<Charset> charsetList = new ArrayList<>();
//            charsetList.add(StandardCharsets.UTF_8);
//            request.getHeaders().setAcceptCharset(charsetList);
//
//            List<MediaType> mediaTypeList = new ArrayList<>();
//            mediaTypeList.add(MediaType.APPLICATION_JSON);
//            request.getHeaders().setAccept(mediaTypeList);
//        }
//    }
//
//    private class StdClientHttpRequestInterceptor implements ClientHttpRequestInterceptor {
//
//        @Override
//        public ClientHttpResponse intercept(HttpRequest request, byte[] body, ClientHttpRequestExecution execution) throws IOException {
//            try {
//                ClientHttpResponse response = execution.execute(request, body);
//                return response;
//            } catch (BizException e) {
//                throw e;
//            } catch (Exception e) {
//                throw new BizException(1503, "调用服务端异常", e);
//            }
//        }
//    }
//
//    private class StdResponseErrorHandler implements ResponseErrorHandler {
//
//        @Override
//        public boolean hasError(ClientHttpResponse response) throws IOException {
//            return !response.getStatusCode().is2xxSuccessful();
//        }
//
//        @Override
//        public void handleError(ClientHttpResponse response) throws IOException {
//            throw new BizException(1502, response.getStatusCode() + ";" + response.getStatusText());
//        }
//    }
//}
