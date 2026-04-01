import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class PluginRegistry:
    def __init__(self, agents_dir: Path):
        self.agents_dir = agents_dir
        self.agents: dict[str, Path] = {}
        self.generators: dict[str, Path] = {}
        self.reviewers: dict[str, Path] = {}

    def discover(self) -> None:
        for item in self.agents_dir.iterdir():
            if item.is_dir() and item.name not in ("generators", "reviewers"):
                prompts_dir = item / "prompts"
                if prompts_dir.exists() and any(prompts_dir.glob("*.md")):
                    self.agents[item.name] = prompts_dir
        generators_dir = self.agents_dir / "generators"
        if generators_dir.exists():
            for item in generators_dir.iterdir():
                if item.is_dir():
                    prompts_dir = item / "prompts"
                    if prompts_dir.exists() and any(prompts_dir.glob("*.md")):
                        self.generators[item.name] = prompts_dir
        reviewers_dir = self.agents_dir / "reviewers"
        if reviewers_dir.exists():
            for item in reviewers_dir.iterdir():
                if item.is_dir():
                    prompts_dir = item / "prompts"
                    if prompts_dir.exists() and any(prompts_dir.glob("*.md")):
                        self.reviewers[item.name] = prompts_dir

    def get_prompt_path(self, category: str, name: str) -> Optional[Path]:
        registry_map = {"agents": self.agents, "generators": self.generators, "reviewers": self.reviewers}
        registry = registry_map.get(category, {})
        prompts_dir = registry.get(name)
        if prompts_dir is None:
            return None
        md_files = list(prompts_dir.glob("*.md"))
        return md_files[0] if md_files else None

    def validate_profile(self, profile) -> list[str]:
        errors = []
        for gen in profile.generators:
            if gen not in self.generators:
                errors.append(f"Generator not found: {gen}")
        for rev in profile.reviewers:
            if rev not in self.reviewers:
                errors.append(f"Reviewer not found: {rev}")
        return errors

    def list_available(self) -> dict[str, list[str]]:
        return {
            "agents": list(self.agents.keys()),
            "generators": list(self.generators.keys()),
            "reviewers": list(self.reviewers.keys()),
        }
