package com.iflytek.auto.ai-agent.sleweb.web.demo.mp;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.generator.FastAutoGenerator;
import com.baomidou.mybatisplus.generator.config.DataSourceConfig;
import com.baomidou.mybatisplus.generator.config.OutputFile;
import com.baomidou.mybatisplus.generator.config.converts.MySqlTypeConvert;
import com.baomidou.mybatisplus.generator.config.querys.MySqlQuery;
import com.baomidou.mybatisplus.generator.config.rules.NamingStrategy;
import com.baomidou.mybatisplus.generator.fill.Column;
import com.baomidou.mybatisplus.generator.fill.Property;
import com.baomidou.mybatisplus.generator.keywords.MySqlKeyWordsHandler;

import java.util.Collections;

public class CodeGenerator {
    public static void main(String[] args) {
        FastAutoGenerator
                .create(
                        new DataSourceConfig
                                // 数据库连接地址
                                .Builder("jdbc:mysql://mysql.internal.autocar.com:3307/weiwang_test",
                                // 用户名
                                "iflyauto",
                                // 密码
                                "Kzw87vv2XLWsOwEN")
                                // 设置数据库类型
                                .dbQuery(new MySqlQuery())
                                // 数据库名
                                .schema("weiwang_test")
                                // 类型转换这里是mysql，选择自己使用的数据库对应的转换类就可以
                                .typeConvert(new MySqlTypeConvert())
                                // 数据库关键词处理
                                .keyWordsHandler(new MySqlKeyWordsHandler())
                )
                .globalConfig(builder ->
                    // 设置作者
                    builder.author("weiwang111")
                            // 开启 swagger 模式
                            .enableSwagger()
                            // 覆盖已生成文件,3.5.3会被删除，不建议使用
                           .fileOverride()
                            //禁止打开输出目录
                            .disableOpenDir()
                            // 指定输出目录
                            .outputDir(getBasePath() + "/simple-web-project/simple-web-app/src/main/java/com/iflytek/auto/sample/sleweb/web/demo/mp/tmp")
                ).strategyConfig(builder ->
                    // 去除的表前缀,默认生成所有表对应的实体
                    builder.addTablePrefix("T_")
                            // 添加需要生成实体的表名
                            .addInclude("t_user")
                            // 添加不需要生成实体的表名
                            .addExclude("t_user")
                            // 控制器controller配置
                            .controllerBuilder()
                            // 开启生成@RestController 控制器
                            .enableRestStyle()
                            // 开启驼峰转连字符
                            .enableHyphenStyle()
                            // 开启父类
                            .superClass("com.xxx.BaseController")
                            // 控制器统一后缀
                            .formatFileName("%sController")

                            // service配置
                            .serviceBuilder()
                            // service统一后缀
                            .formatServiceFileName("%sService")
                            // serviceImpl统一后缀
                            .formatServiceImplFileName("%sServiceImpl")

                            //mapper配置
                            .mapperBuilder()
                            // 生成基础字段的map映射map
                            .enableBaseResultMap()
                            // 生成基础查询的sql
                            .enableBaseColumnList()

                            // 实体类配置
                            .entityBuilder()
                            // 开启链式模型，开启lombok模型不需要开启这个
                            .enableChainModel()
                            // 开启lombok模型
                            .enableLombok()
                            // 开启表字段注解
                            .enableTableFieldAnnotation()
                            // 逻辑删除字段
                            .logicDeleteColumnName("is_deleted")
                            // 数据库表映射到实体的命名策略
                            .naming(NamingStrategy.underline_to_camel)
                            // 数据库表字段映射到实体的命名策略,驼峰命名，这个未设置会按照naming来配置
                            .columnNaming(NamingStrategy.underline_to_camel)
                            // 指定实体类父类
                            .superClass("com.mybatisplus.generator.entity.BaseEntity")
                            // 父类字段
                            .addSuperEntityColumns("id", "create_id", "modify_id", "create_date", "modify_date", "is_deleted")
                            //开启 ActiveRecord 模式，即实体类继承Model类,自己提供CRUD操作,不建议使用,会和父类形成单继承冲突
                            .enableActiveRecord()
                            // 表字段填充字段，对应数据库字段，插入的时候自动填充
                            .addTableFills(new Column("CREATE_TIME", FieldFill.INSERT))
                            // 表字段填充字段，对应实体类字段，插入的时候自动填充
                            .addTableFills(new Property("createTime", FieldFill.INSERT))
                            // 表字段填充字段，对应数据库字段，更新的时候自动填充
                            .addTableFills(new Column("MODIFIED_TIME", FieldFill.UPDATE))
                            // 表字段填充字段，对应实体类字段，更新的时候自动填充
                            .addTableFills(new Property("modifiedTime", FieldFill.UPDATE))
                            // 忽略的字段
                            .addIgnoreColumns("version")
                            // id自增
                            .idType(IdType.AUTO)
                            // 实体类统一后缀
                            .formatFileName("%sEntity"))
                .packageConfig(builder ->
                            // 设置父包名
                            builder.parent("")
                                    // 设置父包模块名
                            .moduleName("test")
                                    //设置entity包名
                                    .entity("entity")
                                    // 设置service包名
                                    .service("service")
                                    // 设置serviceImpl包名
                                    .serviceImpl("service.impl")
                                    // 指定mapper.xml生成的路径
                                    .pathInfo(Collections.singletonMap(OutputFile.xml, getBasePath() + "/simple-web-project/simple-web-app/src/main/resources/mapper")) // 设置mapperXml生成路径

                ).execute();
    }

    /**
     * 获取当前项目的输出路径
     *
     * @return 当前项目的输出路径
     */
    public static String getBasePath() {
        return System.getProperty("user.dir");
    }
}


