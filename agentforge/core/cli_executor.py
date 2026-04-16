import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from agentforge.models.agent import AgentResult

logger = logging.getLogger(__name__)


def _find_claude_cli() -> str:
    """Find the claude CLI executable path."""
    # 1. Check if 'claude' is directly available
    found = shutil.which("claude")
    if found:
        return found

    # 2. Common npm global paths on Windows
    npm_global = os.environ.get("APPDATA", "")
    if npm_global:
        for name in ("claude.cmd", "claude.ps1", "claude"):
            candidate = Path(npm_global) / "npm" / name
            if candidate.exists():
                return str(candidate)

    # 3. Try npm root -g based path
    home = Path.home()
    for npm_dir in [
        home / "AppData" / "Roaming" / "npm",
        home / ".npm-global" / "bin",
        Path("/usr/local/bin"),
    ]:
        for name in ("claude.cmd", "claude", "claude.ps1"):
            candidate = npm_dir / name
            if candidate.exists():
                return str(candidate)

    return "claude"  # Fallback, let subprocess raise FileNotFoundError


class CLIExecutor:
    def __init__(self):
        self._claude_path = _find_claude_cli()
        logger.info(f"Claude CLI path: {self._claude_path}")

    def _build_command(
        self,
        model: str,
        allowed_tools: list[str],
        max_turns: int,
    ) -> list[str]:
        """Build base command without prompt (prompt goes via stdin)."""
        cmd = [
            self._claude_path,
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
        return cmd

    def _build_full_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        append_prompt: Optional[str] = None,
    ) -> str:
        """Merge system prompt + append prompt + task prompt into one string."""
        parts = []
        if system_prompt:
            parts.append(system_prompt)
        if append_prompt:
            parts.append(append_prompt)
        parts.append(prompt)
        return "\n\n---\n\n".join(parts)

    def _parse_result(self, proc_result) -> AgentResult:
        stdout = proc_result.stdout or ""
        exit_code = proc_result.returncode
        try:
            data = json.loads(stdout)
            # Claude CLI uses "total_cost_usd" not "cost"
            cost = data.get("total_cost_usd", data.get("cost", 0.0))
            # Claude CLI uses "usage" with nested structure
            usage = data.get("usage", {})
            is_error = data.get("is_error", False)
            return AgentResult(
                output=data.get("result", ""),
                files_changed=data.get("files_changed", []),
                token_usage=usage,
                cost=cost,
                exit_code=1 if is_error else exit_code,
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
            model=model,
            allowed_tools=allowed_tools or [],
            max_turns=max_turns,
        )

        # Merge all prompts and pass via stdin to avoid Windows cmd line limits
        full_prompt = self._build_full_prompt(prompt, system_prompt, append_prompt)
        cmd.extend(["-p", "-"])  # "-" means read prompt from stdin

        logger.info(f"Executing CLI: model={model}, workspace={workspace}")
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            proc = subprocess.run(
                cmd,
                cwd=workspace,
                input=full_prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_minutes * 60,
                env=env,
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
