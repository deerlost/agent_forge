import json
import logging
import subprocess
from typing import Optional

from agentforge.models.agent import AgentResult

logger = logging.getLogger(__name__)


class CLIExecutor:
    def _build_command(
        self,
        prompt: str,
        model: str,
        allowed_tools: list[str],
        max_turns: int,
        system_prompt: Optional[str] = None,
        append_prompt: Optional[str] = None,
    ) -> list[str]:
        cmd = [
            "claude",
            "--print",
            "--model",
            model,
            "--max-turns",
            str(max_turns),
            "--output-format",
            "json",
        ]
        if allowed_tools:
            cmd.extend(["--allowedTools", ",".join(allowed_tools)])
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])
        if append_prompt:
            cmd.extend(["--append-system-prompt", append_prompt])
        cmd.extend(["-p", prompt])
        return cmd

    def _parse_result(self, proc_result) -> AgentResult:
        stdout = proc_result.stdout or ""
        exit_code = proc_result.returncode
        try:
            data = json.loads(stdout)
            return AgentResult(
                output=data.get("result", ""),
                files_changed=data.get("files_changed", []),
                token_usage=data.get("usage", {}),
                cost=data.get("cost", 0.0),
                exit_code=exit_code,
            )
        except (json.JSONDecodeError, TypeError):
            return AgentResult(
                output=stdout,
                files_changed=[],
                token_usage={},
                cost=0.0,
                exit_code=exit_code,
            )

    def run_agent(
        self,
        prompt: str,
        workspace: str,
        model: str = "opus",
        allowed_tools: Optional[list[str]] = None,
        max_turns: int = 50,
        timeout_minutes: int = 30,
        system_prompt: Optional[str] = None,
        append_prompt: Optional[str] = None,
    ) -> AgentResult:
        cmd = self._build_command(
            prompt=prompt,
            model=model,
            allowed_tools=allowed_tools or [],
            max_turns=max_turns,
            system_prompt=system_prompt,
            append_prompt=append_prompt,
        )
        logger.info(f"Executing CLI: model={model}, workspace={workspace}")
        try:
            proc = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=timeout_minutes * 60,
            )
            return self._parse_result(proc)
        except subprocess.TimeoutExpired:
            logger.error(f"Agent timed out after {timeout_minutes} minutes")
            return AgentResult(
                output=f"Timeout: agent exceeded {timeout_minutes} minute limit",
                exit_code=-1,
            )
        except FileNotFoundError:
            logger.error("Claude CLI not found")
            return AgentResult(output="Error: claude CLI not found", exit_code=-2)
