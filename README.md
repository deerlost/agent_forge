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

## 快速开始

```bash
# 1. 准备 PRD 文档
echo "# 订单管理系统\n## 功能\n- 用户登录\n- 订单CRUD\n- 商品管理" > docs/prd.md

# 2. 生成应用（全自动）
agentforge run --prd docs/prd.md --profile web-app --auto

# 3. 启动生成的应用
cd output/prd/workspace
docker-compose up
```

## 所有 CLI 命令

### agentforge run — 从 PRD 生成完整应用

```bash
agentforge run --prd docs/prd.md --profile web-app
agentforge run --prd docs/prd.md --profile web-app --auto          # 全自动
agentforge run --prd docs/prd.md --profile web-app,scheduler       # 组合 Profile
agentforge run --prd docs/prd.md --profile web-app --backend spring-boot  # 指定后端
agentforge run --prd docs/prd.md --profile web-app -v              # 详细日志
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--prd` | 是 | - | PRD 文件路径 |
| `--profile` | 否 | web-app | 服务画像 |
| `--backend` | 否 | fastapi | 后端技术栈（fastapi / spring-boot） |
| `--auto` | 否 | false | 跳过所有人工确认 |
| `--config-dir` | 否 | config | 配置目录 |
| `--output-dir` | 否 | output | 输出目录 |
| `-v` | 否 | false | 详细日志 |

### agentforge analyze — 仅需求分析

```bash
agentforge analyze --prd docs/prd.md
```

只运行 Analyst Agent，输出 `output/{项目}/state/requirement_spec.json`。成本约 $1-3。

### agentforge plan — 需求分析 + 技术规划

```bash
agentforge plan --prd docs/prd.md --profile web-app
```

输出 `requirement_spec.json` + `plan.json`（Sprint 列表、API 契约、数据模型）。不生成代码。

### agentforge resume — 断点恢复

```bash
agentforge resume --project my-app
```

从上次中断的位置继续运行。

### agentforge status — 查看运行状态

```bash
agentforge status --project my-app
```

输出：当前状态、已完成 Sprint、失败次数、错误信息。

### agentforge cost — 查看成本报告

```bash
agentforge cost --project my-app
```

输出：总成本、按 Agent 分类、按 Sprint 分类的费用明细。

### agentforge profiles — 查看可用服务画像

```bash
agentforge profiles              # 列出名称
agentforge profiles --details    # 显示详细配置
```

### agentforge learn — 学习知识库

```bash
agentforge learn                 # 查看知识库摘要
agentforge learn --analyze       # 跨项目趋势分析
```

## Python API

```python
from agentforge import AgentForge

# 全流程运行
forge = AgentForge(prd_path="./docs/prd.md", profile="web-app")
forge.run()

# 仅需求分析
spec = forge.analyze()
print(spec["modules"])

# 分步执行
spec = forge.analyze()
plan = forge.plan(spec)
forge.execute(plan)

# 配置覆盖
forge = AgentForge(
    prd_path="./docs/prd.md",
    config_overrides={
        "cost.max_total_cost": 50,
        "orchestrator.max_sprint_retries": 5,
    },
)

# 事件回调
@forge.on("sprint_completed")
def on_sprint(sprint_id, result):
    print(f"Sprint {sprint_id} 完成")
```

## 在新项目中使用

```bash
# 1. 创建项目目录
mkdir my-project && cd my-project

# 2. 复制框架资源
cp -r /path/to/agentforge/config ./config
cp -r /path/to/agentforge/agents ./agents
cp -r /path/to/agentforge/templates ./templates
cp -r /path/to/agentforge/profiles ./profiles

# 3. （可选）创建领域知识文件
mkdir prompts
cat > prompts/domain.md << 'EOF'
## 业务背景
这是一个面向 B2B 的订单管理系统。
客户是企业用户，订单金额较大。
## 术语表
- 询价单：客户发起的价格咨询
- 合同订单：签约后的正式订单
EOF

# 4. （可选）创建项目级配置
cat > agentforge.yaml << 'EOF'
project:
  name: "CRM系统"
  domain_prompt: "./prompts/domain.md"
profile: web-app
orchestrator:
  human_checkpoints:
    after_planning: false
EOF

# 5. 写 PRD 并运行
agentforge run --prd docs/prd.md --profile web-app
```

## 产出物结构

```
output/{项目名}/
├── workspace/                 # 生成的可运行应用
│   ├── frontend/              # Vue 3 项目 → npm run dev
│   ├── backend/               # FastAPI/Spring Boot → uvicorn/mvn
│   └── infra/
│       └── docker-compose.yaml  # docker-compose up 一键启动
├── state/                     # 过程数据
│   ├── requirement_spec.json  # 结构化需求规格
│   ├── plan.json              # 技术方案 + Sprint 列表
│   ├── sprints/               # 每个 Sprint 的 handoff 和评审记录
│   ├── final_qa.json          # 全局 QA 报告
│   ├── cost_tracking.json     # 成本明细
│   └── checkpoint.json        # 断点（用于恢复）
└── logs/                      # 执行日志
```

## 可用 Profile

| Profile | 生成器 | 模板 | 适用场景 |
|---------|--------|------|---------|
| web-app | UI + API | Vue3 + FastAPI | 全栈 Web 应用 |
| api-service | API | FastAPI/Spring Boot | 纯后端 API 服务 |
| scheduler | Scheduler + API | Celery/XXL-Job | 调度服务 |
| algorithm | Algorithm + API | Python-Algo | 算法推理服务 |
| data-pipeline | Data | Spark/Flink | 数据管道 |

Profile 可组合：`--profile web-app,scheduler`

## 架构概览

```
PRD → Analyst(需求分析) → Planner(技术规划)
  → Sprint 循环:
      Generator(代码生成) → Reviewer(代码评审) → Evaluator(集成测试)
      → Context Reset → 下一个 Sprint
  → Final QA(全局评审) → 完整应用
```

**核心机制：**
- **GAN 式分离**：Generator 不评审自己，配独立 Reviewer
- **Sprint 驱动**：每个 Sprint 结束清空上下文，handoff JSON 传递状态
- **自学习**：自动从已完成项目提取经验，注入到未来运行
- **断点恢复**：任意时刻可中断，`agentforge resume` 继续

## 配置文件说明

| 文件 | 作用 |
|------|------|
| `config/orchestrator.yaml` | 编排引擎配置（重试次数、超时、人工检查点） |
| `config/agents.yaml` | Agent 配置（模型、工具权限、prompt 文件） |
| `config/defaults.yaml` | 默认参数 |
| `config/learning.yaml` | 自学习引擎配置 |
| `profiles/web-app.yaml` | 服务画像定义 |
| `agentforge.yaml` | 项目级配置覆盖（可选，放项目根目录） |

**配置优先级：** CLI 参数 > agentforge.yaml > Profile > config/ > defaults.yaml
