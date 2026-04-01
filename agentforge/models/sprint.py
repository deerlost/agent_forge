from pydantic import BaseModel, Field


class SprintContract(BaseModel):
    done_criteria: list[str] = Field(default_factory=list)
    test_scenarios: list[str] = Field(default_factory=list)


class Sprint(BaseModel):
    id: str
    name: str
    type: str
    features: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    contract: SprintContract = Field(default_factory=SprintContract)
