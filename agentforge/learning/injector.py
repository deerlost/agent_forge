from agentforge.learning.knowledge_base import KnowledgeBase


class KnowledgeInjector:
    def __init__(self, knowledge_base: KnowledgeBase, min_frequency: int = 2, top_k: int = 10, max_tokens: int = 800):
        self.kb = knowledge_base
        self.min_frequency = min_frequency
        self.top_k = top_k
        self.max_tokens = max_tokens

    def inject(self, agent: str, profile: str) -> str:
        patterns = self.kb.get_patterns(agent=agent, profile=profile, min_frequency=self.min_frequency, top_k=self.top_k)
        antipatterns = self.kb.get_antipatterns(agent=agent, profile=profile, min_frequency=self.min_frequency, top_k=self.top_k)

        if not patterns and not antipatterns:
            return ""

        lines = ["## 从历史项目中学到的经验\n"]

        if patterns:
            lines.append("### 推荐做法（经过多个项目验证）")
            for i, p in enumerate(patterns, 1):
                freq_note = f"（{p.frequency} 个项目验证有效）" if p.frequency > 1 else ""
                lines.append(f"{i}. {p.pattern}{freq_note}")
            lines.append("")

        if antipatterns:
            lines.append("### 避免做法（历史上反复导致返工）")
            for i, ap in enumerate(antipatterns, 1):
                fix_note = f" → ✅ {ap.fix}" if ap.fix else ""
                lines.append(f"{i}. ❌ {ap.antipattern}{fix_note}")
            lines.append("")

        result = "\n".join(lines)
        # Rough token estimate (1 token ~ 2 chars for Chinese)
        if len(result) > self.max_tokens * 2:
            result = result[:self.max_tokens * 2] + "\n...(已截断)"
        return result
