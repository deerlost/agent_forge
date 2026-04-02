import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Analyzer:
    """Cross-project trend analysis."""

    def __init__(self, knowledge_dir: Path):
        self.knowledge_dir = knowledge_dir
        self.history_dir = knowledge_dir / "project_history"

    def _load_histories(self) -> list[dict]:
        if not self.history_dir.exists():
            return []
        histories = []
        for f in sorted(self.history_dir.glob("*.json")):
            try:
                histories.append(json.loads(f.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, KeyError):
                logger.warning(f"Failed to load history: {f}")
        return histories

    def analyze(self) -> dict:
        histories = self._load_histories()
        if not histories:
            return {"total_projects": 0, "avg_cost": 0, "avg_qa_score": 0, "avg_reviewer_rounds": 0, "total_patterns": 0, "total_antipatterns": 0}

        n = len(histories)
        return {
            "total_projects": n,
            "avg_cost": sum(h.get("total_cost", 0) for h in histories) / n,
            "avg_qa_score": sum(h.get("final_qa_score", 0) for h in histories) / n,
            "avg_reviewer_rounds": sum(h.get("avg_reviewer_rounds", 0) for h in histories) / n,
            "total_patterns": sum(h.get("patterns_extracted", 0) for h in histories),
            "total_antipatterns": sum(h.get("antipatterns_extracted", 0) for h in histories),
            "cost_trend": [h.get("total_cost", 0) for h in histories],
            "quality_trend": [h.get("final_qa_score", 0) for h in histories],
        }

    def format_report(self) -> str:
        data = self.analyze()
        if data["total_projects"] == 0:
            return "暂无项目历史数据。"

        lines = [
            f"跨项目学习报告（基于 {data['total_projects']} 个已完成项目）",
            "=" * 50,
            f"平均成本: ${data['avg_cost']:.2f}",
            f"平均 QA 评分: {data['avg_qa_score']:.1f}/5",
            f"平均评审轮数: {data['avg_reviewer_rounds']:.1f}",
            f"累计沉淀模式: {data['total_patterns']} 条",
            f"累计沉淀反模式: {data['total_antipatterns']} 条",
        ]

        if len(data.get("cost_trend", [])) >= 3:
            first_half = data["cost_trend"][:len(data["cost_trend"]) // 2]
            second_half = data["cost_trend"][len(data["cost_trend"]) // 2:]
            if first_half and second_half:
                avg_first = sum(first_half) / len(first_half)
                avg_second = sum(second_half) / len(second_half)
                if avg_second < avg_first:
                    pct = (avg_first - avg_second) / avg_first * 100
                    lines.append(f"成本趋势: 下降 {pct:.0f}%")
                else:
                    lines.append(f"成本趋势: 持平或上升")

        return "\n".join(lines)
