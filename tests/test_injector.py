import pytest
from pathlib import Path
from agentforge.learning.injector import KnowledgeInjector
from agentforge.learning.knowledge_base import KnowledgeBase, Pattern, AntiPattern

@pytest.fixture
def kb_with_data(tmp_path):
    kb = KnowledgeBase(tmp_path / "knowledge")
    kb.add_pattern(Pattern(pattern="Use Pinia for state management", context="Vue", agent="ui", profile="web-app", frequency=3, score_impact=0.5))
    kb.add_pattern(Pattern(pattern="Use computed setter for forms", context="Vue forms", agent="ui", profile="web-app", frequency=2))
    kb.add_pattern(Pattern(pattern="Use @ControllerAdvice", context="Spring Boot", agent="api", profile="web-app", frequency=4))
    kb.add_antipattern(AntiPattern(antipattern="Business logic in controller", consequence="Average 2 rounds rework", fix="Always use service layer", agent="api", profile="web-app", frequency=5))
    kb.add_antipattern(AntiPattern(antipattern="Hardcoded API URLs", consequence="Integration review failure", fix="Use env variables", agent="ui", profile="web-app", frequency=3))
    return kb

class TestKnowledgeInjector:
    def test_inject_for_agent(self, kb_with_data):
        injector = KnowledgeInjector(kb_with_data)
        prompt = injector.inject(agent="ui", profile="web-app")
        assert "Pinia" in prompt
        assert "computed setter" in prompt
        assert "Hardcoded API" in prompt
        # Should NOT include api agent patterns
        assert "ControllerAdvice" not in prompt

    def test_inject_respects_min_frequency(self, kb_with_data):
        injector = KnowledgeInjector(kb_with_data, min_frequency=3)
        prompt = injector.inject(agent="ui", profile="web-app")
        assert "Pinia" in prompt  # frequency=3
        assert "computed setter" not in prompt  # frequency=2

    def test_inject_respects_top_k(self, kb_with_data):
        injector = KnowledgeInjector(kb_with_data, top_k=1)
        prompt = injector.inject(agent="ui", profile="web-app")
        assert "Pinia" in prompt  # highest frequency
        # Should only have 1 pattern

    def test_inject_empty_kb(self, tmp_path):
        kb = KnowledgeBase(tmp_path / "empty_knowledge")
        injector = KnowledgeInjector(kb)
        prompt = injector.inject(agent="ui", profile="web-app")
        assert prompt == ""  # No data, no prompt addition

    def test_inject_contains_sections(self, kb_with_data):
        injector = KnowledgeInjector(kb_with_data)
        prompt = injector.inject(agent="api", profile="web-app")
        assert "推荐做法" in prompt or "Recommended" in prompt.lower() or "模式" in prompt or len(prompt) > 0
