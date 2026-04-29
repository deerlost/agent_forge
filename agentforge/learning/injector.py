import logging
from agentforge.learning.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

# ─── 治理规则 ───
# 1. token 预算：注入内容不超过 max_tokens，避免 prompt 膨胀
# 2. 语义检索：按任务描述匹配相关经验，不全量注入
# 3. 多项目验证权重：frequency > 1 的条目优先
# 4. 退役机制：status=retired 的条目不注入（KnowledgeBase.search 已过滤非 approved）
# 5. profile 隔离：只注入匹配当前 profile 的条目


class KnowledgeInjector:
    def __init__(self, knowledge_base: KnowledgeBase, top_k: int = 10, max_tokens: int = 1500):
        self.kb = knowledge_base
        self.top_k = top_k
        self.max_tokens = max_tokens

    def inject(self, agent: str, profile: str, task_context: str = "") -> str:
        """根据任务上下文语义检索相关经验，拼装为 prompt 片段。

        Args:
            agent: Agent 类型（如 "api"）
            profile: 项目 profile（如 "web-app"）
            task_context: 当前任务描述（Sprint 内容、错误信息等），用于语义检索

        Returns:
            拼装好的 prompt 片段，可直接追加到 system prompt
        """
        if task_context:
            # 语义检索模式：按任务上下文匹配
            results = self.kb.search(
                query=task_context,
                agent=agent,
                profile=profile,
                top_k=self.top_k,
            )
            patterns = results["patterns"]
            antipatterns = results["antipatterns"]
            logger.info(f"Semantic search: {len(patterns)} patterns, {len(antipatterns)} antipatterns matched")
        else:
            # 降级：无任务上下文时按 agent/profile 过滤 + frequency 排序
            patterns = self.kb.get_patterns(agent=agent, profile=profile, top_k=self.top_k)
            antipatterns = self.kb.get_antipatterns(agent=agent, profile=profile, top_k=self.top_k)
            logger.info(f"Fallback filter: {len(patterns)} patterns, {len(antipatterns)} antipatterns")

        if not patterns and not antipatterns:
            return ""

        lines = ["## 从历史项目中学到的经验（按相关性排序）\n"]

        if patterns:
            lines.append("### 推荐做法")
            for i, p in enumerate(patterns, 1):
                freq_note = f"（{p.frequency} 个项目验证）" if p.frequency > 1 else ""
                lines.append(f"{i}. {p.pattern}{freq_note}")
            lines.append("")

        if antipatterns:
            lines.append("### 避免做法")
            for i, ap in enumerate(antipatterns, 1):
                fix_note = f" → ✅ {ap.fix}" if ap.fix else ""
                lines.append(f"{i}. ❌ {ap.antipattern}{fix_note}")
            lines.append("")

        result = "\n".join(lines)

        # Token 预算裁剪（1 token ≈ 2 chars for Chinese）
        char_budget = self.max_tokens * 2
        if len(result) > char_budget:
            result = result[:char_budget].rsplit("\n", 1)[0] + "\n...(已按 token 预算截断)"
            logger.warning(f"Knowledge injection truncated to {self.max_tokens} tokens")

        return result

    def inject_legacy(self, agent: str, profile: str) -> str:
        """向后兼容：无任务上下文时的全量注入（不推荐，会逐步废弃）。"""
        return self.inject(agent=agent, profile=profile, task_context="")
