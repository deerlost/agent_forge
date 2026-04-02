import pytest
from agentforge.learning.knowledge_base import KnowledgeBase, Pattern, AntiPattern

@pytest.fixture
def kb(tmp_path):
    return KnowledgeBase(tmp_path / "knowledge")

class TestKnowledgeBase:
    def test_add_pattern(self, kb):
        p = Pattern(pattern="Use Pinia for state", context="Vue app", agent="ui", profile="web-app", frequency=1, score_impact=0.5)
        kb.add_pattern(p)
        patterns = kb.get_patterns(agent="ui", profile="web-app")
        assert len(patterns) == 1
        assert patterns[0].pattern == "Use Pinia for state"

    def test_add_antipattern(self, kb):
        ap = AntiPattern(antipattern="Business logic in controller", consequence="2 rounds wasted", fix="Use service layer", agent="api", profile="web-app", frequency=1)
        kb.add_antipattern(ap)
        aps = kb.get_antipatterns(agent="api", profile="web-app")
        assert len(aps) == 1
        assert "controller" in aps[0].antipattern

    def test_increment_frequency(self, kb):
        p = Pattern(pattern="Use Pinia", context="Vue", agent="ui", profile="web-app", frequency=1)
        kb.add_pattern(p)
        kb.add_pattern(p)  # Same pattern again
        patterns = kb.get_patterns(agent="ui", profile="web-app")
        assert len(patterns) == 1
        assert patterns[0].frequency == 2

    def test_filter_by_min_frequency(self, kb):
        kb.add_pattern(Pattern(pattern="p1", context="", agent="ui", profile="web-app", frequency=1))
        kb.add_pattern(Pattern(pattern="p2", context="", agent="ui", profile="web-app", frequency=3))
        patterns = kb.get_patterns(agent="ui", profile="web-app", min_frequency=2)
        assert len(patterns) == 1
        assert patterns[0].pattern == "p2"

    def test_top_k(self, kb):
        for i in range(10):
            kb.add_pattern(Pattern(pattern=f"p{i}", context="", agent="ui", profile="web-app", frequency=10-i))
        patterns = kb.get_patterns(agent="ui", profile="web-app", top_k=3)
        assert len(patterns) == 3
        assert patterns[0].frequency >= patterns[1].frequency  # sorted by frequency desc

    def test_persistence(self, tmp_path):
        kb1 = KnowledgeBase(tmp_path / "knowledge")
        kb1.add_pattern(Pattern(pattern="test", context="", agent="ui", profile="web-app", frequency=1))
        kb2 = KnowledgeBase(tmp_path / "knowledge")
        assert len(kb2.get_patterns(agent="ui", profile="web-app")) == 1

    def test_filter_by_agent_and_profile(self, kb):
        kb.add_pattern(Pattern(pattern="vue pattern", context="", agent="ui", profile="web-app", frequency=1))
        kb.add_pattern(Pattern(pattern="api pattern", context="", agent="api", profile="web-app", frequency=1))
        kb.add_pattern(Pattern(pattern="scheduler pattern", context="", agent="scheduler", profile="scheduler", frequency=1))
        assert len(kb.get_patterns(agent="ui", profile="web-app")) == 1
        assert len(kb.get_patterns(agent="api", profile="web-app")) == 1
        assert len(kb.get_patterns(agent="scheduler", profile="scheduler")) == 1

    def test_max_patterns_limit(self, kb):
        kb.max_patterns = 5
        for i in range(10):
            kb.add_pattern(Pattern(pattern=f"p{i}", context="", agent="ui", profile="web-app", frequency=i+1))
        # Should keep only top 5 by frequency
        patterns = kb.get_patterns(agent="ui", profile="web-app")
        assert len(patterns) <= 5
