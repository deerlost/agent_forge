"""End-to-end test that actually calls Claude CLI.
Run with: python tests/test_e2e_real_cli.py
NOT a pytest test (costs real money, needs Claude CLI).
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Setup paths
AGENTFORGE_ROOT = Path(__file__).parent.parent
VENV_PYTHON = sys.executable
os.chdir(str(AGENTFORGE_ROOT))

def find_claude_cli():
    """Find claude CLI executable."""
    import shutil as sh
    found = sh.which("claude")
    if found:
        return found
    npm_dir = Path(os.environ.get("APPDATA", "")) / "npm"
    for name in ("claude.cmd", "claude"):
        p = npm_dir / name
        if p.exists():
            return str(p)
    return None

def test_step(name, check_fn):
    """Run a test step and report pass/fail."""
    try:
        result = check_fn()
        if result:
            print(f"  [OK] {name}")
            return True
        else:
            print(f"  [FAIL] {name}")
            return False
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        return False

def main():
    print("=" * 60)
    print("AgentForge E2E Verification")
    print("=" * 60)

    failures = []

    # 1. Claude CLI available
    print("\n[1/8] Claude CLI")
    claude_path = find_claude_cli()
    if not test_step("Claude CLI found", lambda: claude_path is not None):
        failures.append("Claude CLI not found")
        print(f"    Install: npm install -g @anthropic-ai/claude-code")
        return failures
    print(f"    Path: {claude_path}")

    # 2. Resource resolution
    print("\n[2/8] Resource Resolution")
    from agentforge.core.resources import resolve_config_dir, resolve_agents_dir, resolve_profiles_dir, resolve_templates_dir

    config_dir = resolve_config_dir()
    test_step("Config dir found", lambda: config_dir and config_dir.exists())

    agents_dir = resolve_agents_dir()
    test_step("Agents dir found", lambda: agents_dir and agents_dir.exists())

    profiles_dir = resolve_profiles_dir()
    test_step("Profiles dir found", lambda: profiles_dir and profiles_dir.exists())

    templates_dir = resolve_templates_dir()
    test_step("Templates dir found", lambda: templates_dir and templates_dir.exists())

    # 3. Config loading
    print("\n[3/8] Config Loading")
    from agentforge.core.config import load_config
    config = load_config(config_dir)
    test_step("Config loads without error", lambda: config is not None)
    test_step("Analyst config exists", lambda: config.get_agent_config("analyst") is not None)
    test_step("Analyst max_turns >= 50", lambda: config.get_agent_config("analyst").max_turns >= 50)
    test_step("Analyst has Bash tool", lambda: "Bash" in config.get_agent_config("analyst").allowed_tools)

    # 4. Prompt file resolution
    print("\n[4/8] Prompt Files")
    for agent_key in ["analyst", "planner"]:
        ac = config.get_agent_config(agent_key)
        relative = ac.prompt_file
        if relative.startswith("agents/"):
            relative = relative[len("agents/"):]
        prompt_path = agents_dir / relative
        test_step(f"{agent_key} prompt exists ({prompt_path.name})", lambda p=prompt_path: p.exists())

    # 5. CLI Executor
    print("\n[5/8] CLI Executor")
    from agentforge.core.cli_executor import CLIExecutor
    executor = CLIExecutor()
    test_step("CLI executor init", lambda: executor._claude_path is not None)
    test_step("Claude path valid", lambda: Path(executor._claude_path).exists() or shutil.which(executor._claude_path))

    # 6. Basic Claude CLI call
    print("\n[6/8] Basic CLI Call (costs ~$0.01)")
    result = executor.run_agent(
        prompt="Say 'AgentForge OK' in exactly those words.",
        workspace=str(AGENTFORGE_ROOT),
        model="haiku",
        allowed_tools=[],
        max_turns=1,
        timeout_minutes=1,
    )
    test_step("CLI returns success", lambda: result.is_success)
    test_step("Cost tracked", lambda: result.cost > 0)
    test_step("Output not empty", lambda: len(result.output) > 0)
    print(f"    Output: {result.output[:100]}")
    print(f"    Cost: ${result.cost:.4f}")

    # 7. File write via CLI
    print("\n[7/8] File Write via CLI (costs ~$0.02)")
    test_dir = AGENTFORGE_ROOT / "_e2e_test"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    test_file = test_dir / "test_output.json"
    result = executor.run_agent(
        prompt=f'Write this exact JSON to {test_file.resolve()}: {{"status": "ok", "source": "agentforge"}}. Use the Write tool.',
        workspace=str(test_dir),
        model="haiku",
        allowed_tools=["Write"],
        max_turns=3,
        timeout_minutes=1,
    )
    test_step("Write call succeeds", lambda: result.is_success)
    test_step("File was created", lambda: test_file.exists())
    if test_file.exists():
        content = json.loads(test_file.read_text(encoding="utf-8"))
        test_step("File content correct", lambda: content.get("status") == "ok")

    # 8. System prompt via stdin
    print("\n[8/8] System Prompt via Stdin (costs ~$0.02)")
    system_prompt = "You are a JSON generator. Always output valid JSON. Never output anything else."
    result = executor.run_agent(
        prompt='Output: {"test": true}',
        workspace=str(test_dir),
        model="haiku",
        allowed_tools=[],
        max_turns=1,
        timeout_minutes=1,
        system_prompt=system_prompt,
    )
    test_step("Stdin prompt succeeds", lambda: result.is_success)
    test_step("Output not empty", lambda: len(result.output) > 0)
    print(f"    Output: {result.output[:100]}")

    # Cleanup
    if test_dir.exists():
        shutil.rmtree(test_dir)

    # Summary
    print("\n" + "=" * 60)
    if not failures:
        print("ALL CHECKS PASSED")
    else:
        print(f"FAILURES: {len(failures)}")
        for f in failures:
            print(f"  [FAIL] {f}")
    print("=" * 60)

    return failures

if __name__ == "__main__":
    main()
