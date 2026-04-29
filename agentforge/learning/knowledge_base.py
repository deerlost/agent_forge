import json
import logging
import re
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ─── 轻量关键词提取（零外部依赖）───

_STOP_WORDS = frozenset({
    "的", "了", "在", "是", "和", "与", "或", "不", "要", "有", "到", "为", "中",
    "会", "可以", "需要", "必须", "使用", "通过", "进行", "如果", "但", "而",
    "the", "a", "an", "is", "are", "in", "on", "for", "to", "and", "or", "not",
    "with", "from", "by", "that", "this", "be", "do", "if", "but", "as", "at",
})

_SPLIT_RE = re.compile(r'[，。、；：\s/→↔\-\+\(\)\[\]\{\}""''"""\n]+')
_CJK_RE = re.compile(r'[\u4e00-\u9fff]+')
_ENG_RE = re.compile(r'[a-z][a-z0-9_]*')


def extract_tags(text: str) -> list[str]:
    """从文本中提取关键词标签（中英文混合，零依赖）。

    中文：按 2-4 字滑动窗口提取词组 + 完整短语
    英文：按空格/符号分词
    """
    text_lower = text.lower()
    tags = []

    # 1. 先按分隔符拆成片段
    segments = _SPLIT_RE.split(text_lower)

    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue

        # 2. 提取英文词
        for m in _ENG_RE.finditer(seg):
            word = m.group()
            if len(word) >= 2 and word not in _STOP_WORDS:
                tags.append(word)

        # 3. 提取中文：完整短语 + 2-gram/3-gram
        for m in _CJK_RE.finditer(seg):
            phrase = m.group()
            if len(phrase) >= 2:
                tags.append(phrase)  # 完整短语
            # 2-gram
            for i in range(len(phrase) - 1):
                bigram = phrase[i:i+2]
                if bigram not in _STOP_WORDS:
                    tags.append(bigram)
            # 3-gram
            for i in range(len(phrase) - 2):
                trigram = phrase[i:i+3]
                tags.append(trigram)

    return list(dict.fromkeys(tags))  # 去重保序


def compute_relevance(query_tags: list[str], item_tags: list[str]) -> float:
    """计算查询标签与条目标签的相关性分数（Jaccard + 包含匹配）。"""
    if not query_tags or not item_tags:
        return 0.0
    q_set = set(query_tags)
    i_set = set(item_tags)
    # 精确匹配
    intersection = q_set & i_set
    jaccard = len(intersection) / len(q_set | i_set) if (q_set | i_set) else 0.0
    # 子串包含匹配（如查询"jsonb"匹配标签"jsonb动态列"）
    contain_score = 0
    for qt in q_set:
        for it in i_set:
            if qt in it or it in qt:
                contain_score += 1
    contain_ratio = contain_score / max(len(q_set), 1)
    return jaccard * 0.6 + contain_ratio * 0.4


class Pattern(BaseModel):
    pattern: str
    context: str = ""
    agent: str = ""
    profile: str = ""
    frequency: int = 1
    score_impact: float = 0.0
    tags: list[str] = Field(default_factory=list)  # 自动提取的关键词标签
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
    tags: list[str] = Field(default_factory=list)  # 自动提取的关键词标签
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

    def search(self, query: str, agent: str = "", profile: str = "", top_k: int = 10) -> dict:
        """按任务描述语义检索相关的 pattern 和 antipattern。"""
        query_tags = extract_tags(query)
        if not query_tags:
            return {"patterns": [], "antipatterns": []}

        scored_patterns = []
        for p in self._patterns:
            if p.status != "approved":
                continue
            if agent and p.agent and p.agent != agent:
                continue
            if profile and p.profile and p.profile != profile:
                continue
            tags = p.tags or extract_tags(p.pattern + " " + p.context)
            score = compute_relevance(query_tags, tags)
            # frequency 加权
            score *= (1 + 0.1 * min(p.frequency, 10))
            if score > 0.05:
                scored_patterns.append((score, p))

        scored_antipatterns = []
        for a in self._antipatterns:
            if a.status != "approved":
                continue
            if agent and a.agent and a.agent != agent:
                continue
            if profile and a.profile and a.profile != profile:
                continue
            tags = a.tags or extract_tags(a.antipattern + " " + (a.fix or "") + " " + (a.consequence or ""))
            score = compute_relevance(query_tags, tags)
            score *= (1 + 0.1 * min(a.frequency, 10))
            if score > 0.05:
                scored_antipatterns.append((score, a))

        scored_patterns.sort(key=lambda x: x[0], reverse=True)
        scored_antipatterns.sort(key=lambda x: x[0], reverse=True)

        return {
            "patterns": [p for _, p in scored_patterns[:top_k]],
            "antipatterns": [a for _, a in scored_antipatterns[:top_k]],
        }

    def rebuild_tags(self):
        """为所有无 tags 的条目自动提取标签并保存。"""
        changed = False
        for p in self._patterns:
            if not p.tags:
                p.tags = extract_tags(p.pattern + " " + p.context)
                changed = True
        for a in self._antipatterns:
            if not a.tags:
                a.tags = extract_tags(a.antipattern + " " + (a.fix or "") + " " + (a.consequence or ""))
                changed = True
        if changed:
            self._save_patterns()
            self._save_antipatterns()
            logger.info("Rebuilt tags for all knowledge items")

    def add_pattern(self, pattern: Pattern):
        now = datetime.utcnow().isoformat()
        if not pattern.created_at:
            pattern.created_at = now
        pattern.updated_at = now

        # Auto-extract tags if not provided
        if not pattern.tags:
            pattern.tags = extract_tags(pattern.pattern + " " + pattern.context)

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

        # Auto-extract tags if not provided
        if not antipattern.tags:
            antipattern.tags = extract_tags(
                antipattern.antipattern + " " + (antipattern.fix or "") + " " + (antipattern.consequence or "")
            )

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
