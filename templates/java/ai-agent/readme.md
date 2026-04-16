# 项目的结构说明

## 项目的文件目录结构如下

### ai-agent
### &emsp; |——ai-agent-web-parent
### &emsp; |——ai-agent-web-app
### &emsp; |——ai-agent-web-api
### &emsp; |——ai-agent-web-client

<br><br>

## 项目的mvn的parent结构如下
### ai-agent-web-project（ai-agent）
### &emsp; |——ai-agent-web-parent
### &emsp;&emsp;&emsp; |——ai-agent-web-app
### &emsp;&emsp;&emsp; |——ai-agent-web-api
### &emsp;&emsp;&emsp; |——ai-agent-web-client

<br><br>

## 项目的dependency结构如下

ai-agent-web-app &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; ai-agent-web-client<br>
&emsp;&emsp;&emsp;&emsp;&emsp;|____________________________________________|
<br>
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;|
<br>
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;ai-agent-web-api

<br><br>

## 模块的功能说明

## **ai-agent模块**
ai-agent模块是纯pom工程，父依赖是auto-root-repository，用来指定公司的maven仓库，全局编译环境配置，编译插件的引入。

<br>

## **ai-agent-web-parent模块**
parent模块模块是纯pom工程，通过dependencyManagement配置，管理project所有dependency的版本。

<br>

## **ai-agent-web-app模块**
app是springboot的模块，里面提供业务的实现代码，全部的dao，bo，po，vo的定义和业务实现全部在app里面实现。

<br>

## **ai-agent-web-client模块**
client是调用app的sdk实现，当前client使用的动态代理技术，会通过接口的注解说明生成调用app的接口实现。<br>
client中的dependency的组件如果是spring-boot的常用组件，请申明成provider，由集成方指定版本。

<br>

## **ai-agent-web-api模块**
api里面存放调用app的接口定义，和app&client数据传输用的对象实体定义，当前的对象实体仅用于数据传输，保持app和client的数据一致性，如果需要在实体定义上加入其它功能，如mongo的声明，数据转换的方法，请在app里面对当前对接进行继承扩展实现，不要在api里面的实体定义中扩展。<br>
api中的dependency的组件如果是spring-boot的常用组件，请申明成provider，由集成方指定版本。

<br><br>

# 微服务的工程
一个app是一个微服务，通常一个project中建议只放入一个app。根据实际的project需求，可以在一个project工程中放入多个app，需要自行进行调整。

<br>

如果一个project有多个微服务，每个微服务的业务实体定义，业务方法实现，不要放入共同依赖的module中，即使这块的业务实体或者业务方法完全一样，这样会打破微服务的code工程边界，导致和单体服务同样的高耦合问题，后续代码迭代困难。

<br>

如果多个微服务，使用了同样的非业务实体或非业务方法，根据需要可以创建共同依赖的module，但要谨慎管理这类module中的代码和外部依赖