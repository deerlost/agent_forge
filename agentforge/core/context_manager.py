import json
from pathlib import Path
from typing import Any, Optional


class ContextManager:
    def __init__(
        self,
        state_dir: Path,
        recent_window: int = 3,
        max_files: int = 200,
        max_decisions: int = 30,
        max_issues: int = 20,
    ):
        self.state_dir = state_dir
        self.sprints_dir = state_dir / "sprints"
        self.recent_window = recent_window
        self.max_files = max_files
        self.max_decisions = max_decisions
        self.max_issues = max_issues

    def build_handoff(
        self,
        plan: dict[str, Any],
        current_sprint_id: str,
        completed_sprints: list[str],
        file_manifest: list[dict],
        key_decisions: list[str],
        known_issues: list[dict],
    ) -> dict[str, Any]:
        current_sprint = None
        all_sprints = plan.get("sprints", [])
        for s in all_sprints:
            s_id = s["id"] if isinstance(s, dict) else s.id
            if s_id == current_sprint_id:
                current_sprint = s if isinstance(s, dict) else s.model_dump()
                break

        recent = []
        for sid in completed_sprints[-self.recent_window:]:
            for s in all_sprints:
                s_id = s["id"] if isinstance(s, dict) else s.id
                if s_id == sid:
                    recent.append(s if isinstance(s, dict) else s.model_dump())
                    break

        return {
            "tech_stack": plan.get("tech_stack", {}),
            "api_contract": plan.get("api_contract", []),
            "data_model": plan.get("data_model", []),
            "recent_sprints": recent,
            "file_manifest": file_manifest[-self.max_files:],
            "key_decisions": key_decisions[-self.max_decisions:],
            "current_sprint": current_sprint,
            "known_issues": known_issues[-self.max_issues:],
        }

    def save_handoff(self, sprint_id: str, handoff: dict[str, Any]) -> None:
        self.sprints_dir.mkdir(parents=True, exist_ok=True)
        path = self.sprints_dir / f"{sprint_id}_handoff.json"
        path.write_text(json.dumps(handoff, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_handoff(self, sprint_id: str) -> Optional[dict[str, Any]]:
        path = self.sprints_dir / f"{sprint_id}_handoff.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def format_as_prompt(self, handoff: dict[str, Any]) -> str:
        handoff_json = json.dumps(handoff, indent=2, ensure_ascii=False)
        return (
            "## Context Handoff Data\n\n"
            f"```json\n{handoff_json}\n```\n\n"
            "You are a fresh session. The above is all the context you need. "
            "Begin implementing the current Sprint."
        )
