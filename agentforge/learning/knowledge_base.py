import json
import logging
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Pattern(BaseModel):
    pattern: str
    context: str = ""
    agent: str = ""
    profile: str = ""
    frequency: int = 1
    score_impact: float = 0.0
    # Governance fields
    submitted_by: str = ""          # Who submitted this
    source_project: str = ""        # Which project it came from
    status: str = "approved"        # pending | approved | rejected
    created_at: str = ""
    updated_at: str = ""


class AntiPattern(BaseModel):
    antipattern: str
    consequence: str = ""
    fix: str = ""
    agent: str = ""
    profile: str = ""
    frequency: int = 1
    # Governance fields
    submitted_by: str = ""
    source_project: str = ""
    status: str = "approved"        # pending | approved | rejected
    created_at: str = ""
    updated_at: str = ""


class KnowledgeBase:
    def __init__(self, knowledge_dir: Path, require_approval: bool = False):
        self.knowledge_dir = knowledge_dir
        self._patterns_path = knowledge_dir / "patterns.json"
        self._antipatterns_path = knowledge_dir / "antipatterns.json"
        self.max_patterns = 50
        self.max_antipatterns = 30
        self.require_approval = require_approval
        self._patterns: list[Pattern] = self._load_list(self._patterns_path, Pattern)
        self._antipatterns: list[AntiPattern] = self._load_list(self._antipatterns_path, AntiPattern)

    def _load_list(self, path: Path, model_class):
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return [model_class.model_validate(item) for item in data]

    def _save_patterns(self):
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self._patterns_path.write_text(
            json.dumps([p.model_dump() for p in self._patterns], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _save_antipatterns(self):
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self._antipatterns_path.write_text(
            json.dumps([a.model_dump() for a in self._antipatterns], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add_pattern(self, pattern: Pattern):
        now = datetime.utcnow().isoformat()
        if not pattern.created_at:
            pattern.created_at = now
        pattern.updated_at = now

        # Auto-set status based on governance mode
        if self.require_approval and pattern.status != "approved":
            pattern.status = "pending"

        # Deduplicate
        for existing in self._patterns:
            if existing.pattern == pattern.pattern and existing.agent == pattern.agent and existing.profile == pattern.profile:
                existing.frequency += 1
                existing.score_impact = max(existing.score_impact, pattern.score_impact)
                existing.updated_at = now
                if pattern.source_project and pattern.source_project not in existing.context:
                    existing.context = f"{existing.context}, {pattern.source_project}".strip(", ")
                self._save_patterns()
                return

        self._patterns.append(pattern)
        if len(self._patterns) > self.max_patterns:
            self._patterns.sort(key=lambda p: p.frequency, reverse=True)
            self._patterns = self._patterns[:self.max_patterns]
        self._save_patterns()

    def add_antipattern(self, antipattern: AntiPattern):
        now = datetime.utcnow().isoformat()
        if not antipattern.created_at:
            antipattern.created_at = now
        antipattern.updated_at = now

        if self.require_approval and antipattern.status != "approved":
            antipattern.status = "pending"

        for existing in self._antipatterns:
            if existing.antipattern == antipattern.antipattern and existing.agent == antipattern.agent and existing.profile == antipattern.profile:
                existing.frequency += 1
                existing.updated_at = now
                self._save_antipatterns()
                return

        self._antipatterns.append(antipattern)
        if len(self._antipatterns) > self.max_antipatterns:
            self._antipatterns.sort(key=lambda a: a.frequency, reverse=True)
            self._antipatterns = self._antipatterns[:self.max_antipatterns]
        self._save_antipatterns()

    def get_patterns(self, agent: str = "", profile: str = "", min_frequency: int = 0, top_k: int = 0) -> list[Pattern]:
        results = [p for p in self._patterns
                   if (not agent or p.agent == agent)
                   and (not profile or p.profile == profile)
                   and p.frequency >= min_frequency
                   and p.status == "approved"]  # Only return approved
        results.sort(key=lambda p: p.frequency, reverse=True)
        if top_k > 0:
            results = results[:top_k]
        return results

    def get_antipatterns(self, agent: str = "", profile: str = "", min_frequency: int = 0, top_k: int = 0) -> list[AntiPattern]:
        results = [a for a in self._antipatterns
                   if (not agent or a.agent == agent)
                   and (not profile or a.profile == profile)
                   and a.frequency >= min_frequency
                   and a.status == "approved"]  # Only return approved
        results.sort(key=lambda a: a.frequency, reverse=True)
        if top_k > 0:
            results = results[:top_k]
        return results

    def get_pending(self) -> dict:
        """Get all pending items awaiting approval."""
        return {
            "patterns": [p for p in self._patterns if p.status == "pending"],
            "antipatterns": [a for a in self._antipatterns if a.status == "pending"],
        }

    def approve(self, text: str) -> bool:
        """Approve a pending pattern or antipattern by its text."""
        for p in self._patterns:
            if p.pattern == text and p.status == "pending":
                p.status = "approved"
                p.updated_at = datetime.utcnow().isoformat()
                self._save_patterns()
                return True
        for a in self._antipatterns:
            if a.antipattern == text and a.status == "pending":
                a.status = "approved"
                a.updated_at = datetime.utcnow().isoformat()
                self._save_antipatterns()
                return True
        return False

    def reject(self, text: str) -> bool:
        """Reject a pending pattern or antipattern by its text."""
        for p in self._patterns:
            if p.pattern == text and p.status == "pending":
                p.status = "rejected"
                p.updated_at = datetime.utcnow().isoformat()
                self._save_patterns()
                return True
        for a in self._antipatterns:
            if a.antipattern == text and a.status == "pending":
                a.status = "rejected"
                a.updated_at = datetime.utcnow().isoformat()
                self._save_antipatterns()
                return True
        return False
