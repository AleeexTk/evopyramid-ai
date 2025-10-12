"""Interactive EvoCodex shell helpers with honest error reporting."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class CommandResult:
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    error: Optional[str] = None


def execute_command(command: str) -> CommandResult:
    """Execute a shell command and return a structured result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return CommandResult(
                success=False,
                stdout=(result.stdout or "").strip(),
                stderr=(result.stderr or "").strip(),
                exit_code=result.returncode,
            )
        return CommandResult(success=True, stdout=(result.stdout or "").strip())
    except Exception as exc:  # pragma: no cover - defensive
        return CommandResult(success=False, error=str(exc))


def render_result(result: CommandResult) -> str:
    """Format the command result for CLI output."""
    if result.success:
        body = result.stdout or "(no output)"
        return "\n".join(["✅ Команда выполнена успешно:", body])

    lines = ["❌ Ошибка выполнения команды."]
    if result.stderr:
        lines.append(f"stderr: {result.stderr}")
    if result.stdout:
        lines.append(f"stdout: {result.stdout}")
    if result.exit_code is not None:
        lines.append(f"Код возврата: {result.exit_code}")
    if result.error:
        lines.append(f"Ошибка: {result.error}")
    return "\n".join(lines)


__all__ = ["CommandResult", "execute_command", "render_result"]
