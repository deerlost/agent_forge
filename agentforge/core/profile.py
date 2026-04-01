import yaml
from pathlib import Path
from pydantic import BaseModel, Field


class Profile(BaseModel):
    name: str
    description: str = ""
    generators: list[str] = Field(default_factory=list)
    reviewers: list[str] = Field(default_factory=list)
    evaluator_strategies: list[str] = Field(default_factory=list)
    templates: list[str] = Field(default_factory=list)
    sprint_types: list[str] = Field(default_factory=list)

    _sprint_generator_map: dict[str, list[str]] = {
        "backend": ["api"],
        "frontend": ["ui"],
        "fullstack": ["api", "ui"],
    }

    def generators_for_sprint_type(self, sprint_type: str) -> list[str]:
        default = self._sprint_generator_map.get(sprint_type, self.generators)
        return [g for g in default if g in self.generators]


def load_profile(name: str, profiles_dir: Path) -> Profile:
    path = profiles_dir / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {path}")
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return Profile.model_validate(data)


def load_profiles_from_string(names: str, profiles_dir: Path) -> list[Profile]:
    return [load_profile(n.strip(), profiles_dir) for n in names.split(",")]


def merge_profiles(profiles: list[Profile]) -> Profile:
    if not profiles:
        return Profile(name="empty")
    if len(profiles) == 1:
        return profiles[0]

    def dedup_ordered(lists):
        seen = set()
        result = []
        for lst in lists:
            for item in lst:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
        return result

    return Profile(
        name="+".join(p.name for p in profiles),
        description=" + ".join(p.description for p in profiles if p.description),
        generators=dedup_ordered(p.generators for p in profiles),
        reviewers=dedup_ordered(p.reviewers for p in profiles),
        evaluator_strategies=dedup_ordered(p.evaluator_strategies for p in profiles),
        templates=dedup_ordered(p.templates for p in profiles),
        sprint_types=dedup_ordered(p.sprint_types for p in profiles),
    )
