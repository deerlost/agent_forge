# AgentForge - 长运行多智能体应用生成框架

基于 [Anthropic Harness Design](https://www.anthropic.com/engineering/harness-design-long-running-apps) 论文，采用 GAN 式 Generator-Reviewer 分离 + Sprint 驱动上下文重置架构。

## 安装

```bash
cd agentforge
pip install -e ".[dev]"
```

**前置条件：**
```bash
# 安装 Claude Code CLI
npm install -g @anthropic-ai/claude-code

# 设置 API Key
export ANTHROPIC_API_KEY=sk-ant-xxx
```

## 框架结构

```
agentforge/
├── agentforge/                      # Python 包（核心代码）
│   ├── cli.py                       # CLI 入口（click）
│   ├── api.py                       # Python API 入口
│   │
│   ├── core/                        # ═══ 编排引擎 ═══
│   │   ├── orchestrator.py          # 状态机：驱动 Sprint 循环（分析→规划→生成→评审→测试）
│   │   ├── cli_executor.py          # Claude Code CLI 子进程执行器（stdin 传 prompt，UTF-8 编码）
│   │   ├── config.py                # AppConfig 配置加载（agentforge.yaml + CLI 参数 + defaults）
│   │   ├── context_manager.py       # 上下文管理（Sprint 间 handoff JSON 传递状态）
│   │   ├── checkpoint.py            # 断点持久化（file-based state，支持 resume）
│   │   ├── cost_tracker.py          # 成本追踪（解析 Claude CLI 返回的 total_cost_usd）
│   │   ├── human_gate.py            # 人工检查点（planning 后确认、Sprint 失败后干预）
│   │   ├── profile.py               # Service Profile 加载器（web-app / api-service / scheduler 等）
│   │   ├── resources.py             # 资源路径解析器（CWD → 安装目录 fallback，空目录跳过）
│   │   ├── template_copier.py       # 项目模板复制器
│   │   └── plugin_registry.py       # 插件注册（预留扩展点）
│   │
│   ├── learning/                    # ═══ 自学习引擎 ═══
│   │   ├── knowledge_base.py        # 知识库：Pattern/AntiPattern 模型 + tags 索引 + 语义检索
│   │   ├── injector.py              # 知识注入器：按任务上下文检索 top-K + token 预算裁剪
│   │   ├── extractor.py             # 经验提取器：从 Sprint 评审结果提取 pattern/antipattern
│   │   └── analyzer.py              # 趋势分析器：跨项目经验统计
│   │
│   └── models/                      # ═══ 数据模型 ═══
│       ├── agent.py                 # AgentResult（执行结果 + 成本）
│       ├── plan.py                  # Plan（Sprint 列表 + 依赖图）
│       ├── sprint.py                # Sprint（handoff + 评审结果）
│       └── state.py                 # ProjectState（全局状态机枚举）
│
├── config/                          # 框架默认配置
│   ├── orchestrator.yaml            # 编排引擎（重试次数、超时、人工检查点）
│   ├── agents.yaml                  # Agent 配置（模型、工具权限、max_turns、timeout）
│   ├── defaults.yaml                # 默认参数
│   └── learning.yaml                # 自学习引擎配置
│
├── agents/                          # Agent Prompt 模板
│   ├── analyst/                     # 需求分析 Agent（PRD → requirement_spec）
│   ├── planner/                     # 架构规划 Agent（requirement_spec → plan）
│   ├── generators/                  # 代码生成 Agent（按 profile 分：ui / api / scheduler）
│   ├── reviewers/                   # 代码评审 Agent（GAN 式独立评审）
│   └── evaluator/                   # 集成测试 Agent（编译 + 启动 + 端到端验证）
│
├── profiles/                        # Service Profile 定义
│   └── web-app.yaml                 # 全栈 Web 应用画像（前端+后端+基础设施）
│
├── templates/                       # 项目脚手架模板
│   ├── ui/                          # 前端模板（Vue3 / React）
│   ├── api/                         # 后端模板（FastAPI / Spring Boot）
│   ├── java/                        # Java 项目模板（Maven 多模块 + DDD）
│   └── infra/                       # 基础设施模板（Docker Compose / K8s）
│
├── knowledge/                       # 自学习知识库（本地文件存储）
│   ├── patterns.json                # 推荐做法（含 tags 索引，语义检索用）
│   ├── antipatterns.json            # 避免做法（含 tags 索引）
│   ├── *.yaml                       # 批量导入源（项目经验、团队规则）
│   └── project_history/             # 项目执行历史
│
├── tests/                           # 测试
└── pyproject.toml                   # 包定义（零外部依赖：pydantic + pyyaml + click）
```

## 架构概览

```
PRD ─→ Analyst（需求分析）─→ Planner（架构规划）
         │                      │
         ▼                      ▼
   requirement_spec          plan.json
   (.md + .json)         (Sprint 列表 + API 契约)
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
              Sprint 循环              自学习引擎
              ┌──────────┐         ┌──────────────┐
              │Generator │         │ KnowledgeBase│
              │(代码生成) │◄────────│ (patterns +  │
              └────┬─────┘  注入    │ antipatterns)│
                   │     top-K 经验 │              │
              ┌────▼─────┐         │  search()    │
              │Reviewer  │         │  按任务语义   │
              │(代码评审) │         │  检索相关经验 │
              └────┬─────┘         └──────┬───────┘
                   │                      ▲
              ┌────▼─────┐                │
              │Evaluator │     提取经验    │
              │(集成测试) │───────────────┘
              └────┬─────┘
                   │
              Context Reset
              (handoff JSON)
                   │
              下一个 Sprint
                   │
              ┌────▼─────┐
              │Final QA  │
              └──────────┘
                   │
              完整应用
```

### 核心机制

| 机制 | 说明 |
|------|------|
| GAN 式分离 | Generator 不评审自己，配独立 Reviewer + Evaluator |
| Sprint 驱动 | 每个 Sprint 结束清空上下文，handoff JSON 传递状态 |
| 断点恢复 | 任意时刻可中断，`agentforge resume` 从 checkpoint 继续 |
| 资源 Fallback | 项目目录 → 安装目录自动查找 config/agents/templates |

### 自学习引擎

| 机制 | 说明 |
|------|------|
| 语义检索 | 按当前 Sprint 任务描述检索 top-K 相关经验，不全量注入 |
| 关键词索引 | 中文 2/3-gram + 英文分词，Jaccard + 子串匹配打分 |
| token 预算 | 注入上限 1500 token，超出按相关性裁剪 |
| 多项目验证 | frequency 字段记录跨项目验证次数，高频经验优先 |
| 治理流程 | pending → approve/reject，status 过滤非 approved |
| 零依赖 | 纯 Python 实现，知识库存本地 JSON 文件 |

## 快速开始

```bash
# 1. 准备 PRD 文档
echo "# 订单管理系统\n## 功能\n- 用户登录\n- 订单CRUD" > docs/prd.md

# 2. 生成应用（全自动）
agentforge run --prd docs/prd.md --profile web-app --auto

# 3. 启动生成的应用
cd output/prd/workspace
docker-compose up
```

**分步执行（推荐首次使用）：**

```bash
agentforge analyze --prd docs/prd.md           # 需求分析
agentforge plan --prd docs/prd.md --profile web-app  # 架构设计
agentforge run --prd docs/prd.md --profile web-app --auto  # 自动跳过已完成步骤
```

## CLI 命令

### 核心命令

| 命令 | 说明 |
|------|------|
| `agentforge analyze --prd <file>` | 仅需求分析，输出 requirement_spec |
| `agentforge plan --prd <file> --profile <p>` | 分析 + 架构设计，输出 plan.json |
| `agentforge run --prd <file> --profile <p> --auto` | 完整生成（自动从断点继续） |
| `agentforge resume --project <name>` | 断点恢复 |
| `agentforge status --project <name>` | 查看运行状态 |
| `agentforge cost --project <name>` | 成本报告 |
| `agentforge profiles [--details]` | 查看可用 Service Profile |

### 自学习命令

| 命令 | 说明 |
|------|------|
| `agentforge learn [--analyze]` | 查看知识库摘要 / 跨项目趋势分析 |
| `agentforge add-pattern "<text>" --agent <a>` | 添加推荐做法 |
| `agentforge add-antipattern "<text>" --fix "<f>" --agent <a>` | 添加避免做法 |
| `agentforge import-rules <yaml> --profile <p>` | 从 YAML 批量导入 |
| `agentforge extract --state-dir <dir> --profile <p>` | 从已完成项目提取经验 |
| `agentforge pending` | 查看待审核条目 |
| `agentforge approve "<text>"` / `reject "<text>"` | 审核单条 |
| `agentforge approve-all` | 批量通过 |
| `agentforge rebuild-tags` | 重建知识库关键词索引 |
| `agentforge search-knowledge "<query>"` | 按任务描述语义检索经验 |

## Python API

```python
from agentforge import AgentForge

# 全流程运行
forge = AgentForge(prd_path="./docs/prd.md", profile="web-app")
forge.run()

# 分步执行
spec = forge.analyze()
plan = forge.plan(spec)
forge.execute(plan)

# 事件回调
@forge.on("sprint_completed")
def on_sprint(sprint_id, result):
    print(f"Sprint {sprint_id} 完成")
```

## 在新项目中使用

```bash
mkdir my-project && cd my-project

# 创建项目配置（可选，不创建则用框架默认）
cat > agentforge.yaml << 'EOF'
project:
  name: "CRM系统"
profile: web-app
knowledge_dir: /path/to/shared/knowledge  # 共享知识库
EOF

# 运行（资源自动从安装目录加载，无需复制）
agentforge run --prd docs/prd.md --profile web-app
```

## 产出物结构

```
output/{项目名}/
├── workspace/                     # 生成的可运行应用
│   ├── frontend/                  # 前端项目
│   ├── backend/                   # 后端项目
│   └── infra/                     # Docker Compose 等
├── state/                         # 过程数据
│   ├── checkpoint.json            # 断点
│   ├── requirement_spec.md/json   # 需求规格
│   ├── plan.md/json               # 技术方案
│   ├── change-guides/             # 变更执行指导文件（跨会话协作用）
│   ├── sprints/                   # Sprint handoff + 评审记录
│   └── cost_tracking.json         # 成本明细
└── logs/                          # 执行日志
```

## 可用 Profile

| Profile | 生成器 | 模板 | 适用场景 |
|---------|--------|------|---------|
| web-app | UI + API | Vue3/React + FastAPI/Spring Boot | 全栈 Web 应用 |
| api-service | API | FastAPI/Spring Boot | 纯后端 API 服务 |
| scheduler | Scheduler + API | Celery/XXL-Job | 调度服务 |
| algorithm | Algorithm + API | Python-Algo | 算法推理服务 |
| data-pipeline | Data | Spark/Flink | 数据管道 |

Profile 可组合：`--profile web-app,scheduler`

## 配置文件说明

| 文件 | 作用 |
|------|------|
| `config/orchestrator.yaml` | 编排引擎（重试、超时、人工检查点） |
| `config/agents.yaml` | Agent 配置（模型、工具权限、prompt 文件、max_turns） |
| `config/defaults.yaml` | 默认参数 |
| `config/learning.yaml` | 自学习引擎配置 |
| `profiles/web-app.yaml` | 服务画像定义 |
| `agentforge.yaml` | 项目级配置覆盖（可选，放项目根目录） |

**配置优先级：** CLI 参数 > agentforge.yaml > Profile > config/ > defaults.yaml

**资源查找顺序：** 项目 CWD → agentforge 安装目录（自动 fallback，无需复制）
