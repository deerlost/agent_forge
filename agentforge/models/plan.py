from typing import Any

from pydantic import BaseModel, Field

from agentforge.models.sprint import Sprint


class Feature(BaseModel):
    id: str
    description: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    business_rules: list[str] = Field(default_factory=list)
    ai_feature: bool = False


class Module(BaseModel):
    id: str
    name: str
    priority: str = "P1"
    features: list[Feature] = Field(default_factory=list)


class RequirementSpec(BaseModel):
    project_name: str
    modules: list[Module] = Field(default_factory=list)
    non_functional: dict[str, Any] = Field(default_factory=dict)
    ambiguities: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def has_ambiguities(self) -> bool:
        return len(self.ambiguities) > 0


class Plan(BaseModel):
    tech_stack: dict[str, str] = Field(default_factory=dict)
    data_model: list[dict[str, Any]] = Field(default_factory=list)
    api_contract: list[dict[str, Any]] = Field(default_factory=list)
    sprints: list[Sprint] = Field(default_factory=list)
