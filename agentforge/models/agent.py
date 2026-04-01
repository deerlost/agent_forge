from typing import Optional

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    engine: str = "claude-cli"
    model: str = "opus"
    max_turns: int = 50
    timeout_minutes: int = 30
    allowed_tools: list[str] = Field(default_factory=list)
    prompt_file: str = ""
    provider: Optional[str] = None


class AgentResult(BaseModel):
    output: str = ""
    files_changed: list[str] = Field(default_factory=list)
    token_usage: dict = Field(default_factory=dict)
    cost: float = 0.0
    exit_code: int = 0

    @property
    def is_success(self) -> bool:
        return self.exit_code == 0
