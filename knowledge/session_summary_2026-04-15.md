# VUI系统 - 会话总结

> 日期: 2026-04-15 | 参与者: yangwang44

---

## 一、今日完成事项

### 1. PRD 分析（Analyst 阶段）

- 输入: `doc/VUI系统.pdf` (V1.0)
- 输出: `state/requirement_spec.md`
- 结果:
  - 7 个功能模块（M001-M007）
  - 26 个功能点（F001-F026），含优先级标注（P0/P1/P2）
  - 29 字段验证规则表
  - 字段权限矩阵（29字段 x 3角色）
  - 语种优先级表（40+语种，含P1/P2标注）
  - 11 个待澄清项（A001-A011）

### 2. 技术方案与Sprint计划（Planner 阶段）

- 输出: `state/plan.md`
- 关键技术决策:

| 决策项 | 结论 | 理由 |
|--------|------|------|
| 前端框架 | Vue 3 + Rsbuild + Element Plus | 平台规范 |
| 流程图编辑器 | 微前端子应用独立接入 | 包体积隔离、技术选型独立 |
| 后端框架 | Spring Boot 2.7 + MyBatis-Plus 3.5 | 接入现有 auto-framework-web |
| 服务架构 | 单服务 vui-web，复用平台网关/认证 | 不新建 gateway/auth |
| 工程结构 | DDD 四层（interfaces/application/domain/infrastructure）+ 4聚合 | 领域驱动设计 |
| 数据库 | **PostgreSQL 15+**（非 MySQL） | jsonb/GIN索引/原生数组/部分索引/CHECK约束全面优于 MySQL |
| 缓存 | Redis Cluster（复用现有） | 业务锁定/用户偏好缓存 |

- Sprint 计划: 11 个 Sprint（S001-S011）
- 数据模型: 11 张表，含 GIN 索引、部分唯一索引、CHECK 约束
- API 契约: 30+ 端点，路径前缀 `/webapi/v1/`

### 3. 代码生成（Generator 阶段 - S001）

S001 工程骨架已生成，但因 agentforge CLI 运行导致 output 目录被清理。需要重新生成。

已完成的代码内容（需重建）:

| 产出 | 描述 | 状态 |
|------|------|------|
| 后端 Maven 四模块工程 | vui-web（project/parent/api/app/client），DDD 包结构，8个 Java 文件，34个 .gitkeep | 需重建 |
| 后端配置 | bootstrap.yml（Nacos）+ application.yml（PG+Redis+MyBatis-Plus） | 需重建 |
| Flyway SQL | V1__init_schema.sql，11张表，315行 DDL | 需重建 |
| 前端 Vue 3 | 11个文件，Rsbuild + Element Plus + Pinia + Vue Router + Axios | 需重建 |
| Docker Compose | PG15 + Redis + vui-web + Dockerfile | 需重建 |

### 4. Review 历程

| 轮次 | 内容 | 发现 | 状态 |
|------|------|------|------|
| R1 | requirement_spec 审查 | 5 Critical + 15 Major | 已修复 |
| R2 | plan.json 审查 | 7 Major + 12 Minor | 已修复 |
| R3 | plan.md 自审 | 7 issues（协作者前端缺失、admin_name、全局禁用条件独立表等） | 已修复 |
| R4 | 技术栈调整 | 用户反馈4项（微前端、单服务、MySQL→PG选型、Docker不变） | 已修复 |
| R5 | DDD工程结构 | 用户要求领域驱动设计 | 已修复 |
| R6 | 数据库选型 | MySQL vs PG 对比，选 PG | 已修复 |
| R7 | 外部服务依赖 | 车企/语种/Appid/车型数据来源明确 | 已修复 |
| R8 | 最终定稿自审 | 2 Critical（MySQL残留、GZIP矛盾）+ 5 Minor | Critical已修复 |

---

## 二、关键设计决策记录

### 2.1 为什么选 PostgreSQL 而非 MySQL

VUI 系统核心表有 7 个 JSON 字段，JSON 是业务核心而非附属品。PG 的 jsonb 二进制存储、GIN 索引、`jsonb_set` 部分更新、原生 `text[]` 数组、真正生效的 CHECK 约束、部分唯一索引（`WHERE is_deleted = false`）在本场景全面优于 MySQL。资源需求两者一致（4C8G 足够）。

### 2.2 为什么用微前端隔离流程图编辑器

流程图引擎（vue-flow/AntV X6/LogicFlow）依赖重，与主应用共存会导致包体积膨胀和样式冲突。独立子应用可单独迭代、技术选型自由、运行时沙箱隔离。

### 2.3 为什么单服务而非微服务拆分

现有平台已提供网关、认证、UAP 权限。VUI 系统业务内聚度高，拆成多个服务增加运维复杂度但无收益。作为单个微服务接入现有平台是最优解。

### 2.4 DDD 四聚合划分

| 聚合 | 聚合根 | 核心不变量 |
|------|--------|------------|
| VUI管理 | Vui | 名称唯一；语种≥1；车企不可改；管理员唯一 |
| 功能编辑 | VuiFunction | 功能点ID VUI内唯一；提示语ID唯一；括号成对 |
| 交互逻辑 | InteractionFlow | flow_data与行数据一致性（保存时同步重建） |
| 发布管理 | VuiVersion | 发布前全量校验；版本号单调递增 |

### 2.5 外部服务依赖

| 数据 | 来源 | 本地存储策略 |
|------|------|-------------|
| 车企 | UAP 服务 | 存 company_id + company_name（冗余，写入时快照） |
| 语种 | 平台枚举 | 存语种编码 text[]（如 zh_CN） |
| Appid | CIVI 产品定义中心接口 | 存 Appid 字符串 text[] |
| 车型 | 用户手动输入 | 存 text[] |

---

## 三、待办事项

### 下一步

1. **重新生成 S001 代码** — agentforge CLI 清理了 output 目录，需要重新执行 `agentforge generate --sprint S001`
2. **解决 agentforge CLI 编码问题** — PRD 文件名含中文导致路径乱码（`VUIϵͳ`）

### 待澄清项（11项，不阻塞开发）

| ID | 问题 | 建议值 |
|----|------|--------|
| A001 | 车型字段格式 | 字符串用\|分隔 |
| A002 | 协议槽位取值格式 | `{"slot_name":["v1","v2"]}` |
| A003 | 交互逻辑节点连线规则 | 条件节点两出口，其他一出口，DAG |
| A004 | 批量导入Excel格式 | 由下载模板反向定义 |
| A006 | 功能参数细节格式 | V1.0自由文本 |
| A007 | 多字段字符限制 | 待确认 |
| A008 | 车型复制交互设计 | 弹窗选车型映射 |
| A009 | 车型打点交互形式 | 表格（行=功能点，列=车型） |
| A010 | 车企权限可配置机制 | 管理员在VUI设置中配置 |
| A011 | 可下载版本数量 | 保留最近10个 |

---

## 四、产出文件清单

| 文件 | 路径 | 说明 |
|------|------|------|
| 需求规格 | `state/requirement_spec.md` | 已定稿 |
| 技术方案 | `state/plan.md` | 已定稿 |
| 会话总结 | `state/session_summary_2026-04-15.md` | 本文件 |
