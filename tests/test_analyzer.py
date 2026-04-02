import json
import pytest
from pathlib import Path
from agentforge.learning.analyzer import Analyzer

@pytest.fixture
def project_histories(tmp_path):
    history_dir = tmp_path / "knowledge" / "project_history"
    history_dir.mkdir(parents=True)

    for i in range(5):
        history = {
            "project_name": f"Project {i}",
            "profile": "web-app",
            "total_cost": 100 + i * 20,
            "total_sprints": 8,
            "avg_reviewer_rounds": 3.0 - i * 0.3,
            "final_qa_score": 3.2 + i * 0.2,
            "patterns_extracted": 5 + i,
            "antipatterns_extracted": 3 - (i // 2),
        }
        (history_dir / f"project_{i}.json").write_text(json.dumps(history))
    return tmp_path / "knowledge"

class TestAnalyzer:
    def test_analyze_trends(self, project_histories):
        analyzer = Analyzer(project_histories)
        report = analyzer.analyze()
        assert "total_projects" in report
        assert report["total_projects"] == 5

    def test_cost_trend(self, project_histories):
        analyzer = Analyzer(project_histories)
        report = analyzer.analyze()
        assert "avg_cost" in report
        assert report["avg_cost"] > 0

    def test_quality_trend(self, project_histories):
        analyzer = Analyzer(project_histories)
        report = analyzer.analyze()
        assert "avg_qa_score" in report

    def test_empty_history(self, tmp_path):
        analyzer = Analyzer(tmp_path / "empty")
        report = analyzer.analyze()
        assert report["total_projects"] == 0

    def test_format_report(self, project_histories):
        analyzer = Analyzer(project_histories)
        text = analyzer.format_report()
        assert "项目" in text or "project" in text.lower()
