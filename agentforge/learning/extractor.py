import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Threshold: sprints scoring above this are "good" (pattern sources)
HIGH_SCORE_THRESHOLD = 4.0
# Threshold: sprints scoring below this are "bad" (antipattern sources)
LOW_SCORE_THRESHOLD = 3.0


class Extractor:
    """Extract patterns and antipatterns from completed run results."""

    def extract(self, state_dir: Path, profile: str = "") -> dict:
        patterns = []
        antipatterns = []

        sprints_dir = state_dir / "sprints"
        plan = self._load_plan(state_dir)
        sprint_map = {s["id"]: s for s in plan.get("sprints", [])} if plan else {}

        # Extract from sprint reviews
        if sprints_dir.exists():
            for review_file in sorted(sprints_dir.glob("*_review.json")):
                try:
                    review = json.loads(review_file.read_text(encoding="utf-8"))
                    sprint_id = review.get("sprint_id", "")
                    sprint_info = sprint_map.get(sprint_id, {})
                    sprint_type = sprint_info.get("type", "")
                    agent = self._agent_from_sprint_type(sprint_type)

                    score = review.get("score", 0)

                    # High score = pattern
                    if score >= HIGH_SCORE_THRESHOLD:
                        for dim_name, dim_data in review.get("dimensions", {}).items():
                            if isinstance(dim_data, dict) and dim_data.get("score", 0) >= HIGH_SCORE_THRESHOLD:
                                patterns.append({
                                    "pattern": f"Sprint {sprint_id} ({sprint_info.get('name', '')}): {dim_name} scored {dim_data['score']} - {dim_data.get('notes', '')}",
                                    "context": f"Sprint {sprint_id}",
                                    "agent": agent,
                                    "profile": profile,
                                    "frequency": 1,
                                    "score_impact": dim_data.get("score", 0) - 3.0,
                                })

                    # Low score or issues = antipattern
                    if score < LOW_SCORE_THRESHOLD:
                        for issue in review.get("issues", []):
                            antipatterns.append({
                                "antipattern": issue.get("description", ""),
                                "consequence": f"Caused review failure in sprint {sprint_id} (score: {score})",
                                "fix": "",
                                "agent": agent,
                                "profile": profile,
                                "frequency": 1,
                            })

                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse review {review_file}: {e}")

        # Extract from final QA bugs
        qa_path = state_dir / "final_qa.json"
        if qa_path.exists():
            try:
                qa = json.loads(qa_path.read_text(encoding="utf-8"))
                for bug in qa.get("bugs", []):
                    antipatterns.append({
                        "antipattern": bug.get("description", ""),
                        "consequence": f"Found in final QA (severity: {bug.get('severity', 'unknown')})",
                        "fix": "",
                        "agent": "",
                        "profile": profile,
                        "frequency": 1,
                    })
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse final QA: {e}")

        return {"patterns": patterns, "antipatterns": antipatterns}

    def _load_plan(self, state_dir: Path) -> dict | None:
        plan_path = state_dir / "plan.json"
        if plan_path.exists():
            try:
                return json.loads(plan_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
        return None

    def _agent_from_sprint_type(self, sprint_type: str) -> str:
        mapping = {"backend": "api", "frontend": "ui", "fullstack": "api"}
        return mapping.get(sprint_type, "")
