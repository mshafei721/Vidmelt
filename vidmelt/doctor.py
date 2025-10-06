"""Environment diagnostics for Vidmelt."""

from __future__ import annotations

import importlib
import os
import shutil
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import redis

DEFAULT_REDIS_URL = "redis://localhost:6379/0"


@dataclass(frozen=True)
class Diagnostic:
    name: str
    ok: bool
    message: str


def _check_ffmpeg() -> Diagnostic:
    path = shutil.which("ffmpeg")
    if path:
        return Diagnostic("FFmpeg", True, f"found at {path}")
    return Diagnostic("FFmpeg", False, "ffmpeg binary not found on PATH")


def _check_redis(redis_url: str = DEFAULT_REDIS_URL) -> Diagnostic:
    try:
        client = redis.from_url(redis_url)
        client.ping()
    except Exception as exc:  # pragma: no cover - specific redis errors exercised in tests
        return Diagnostic("Redis", False, f"connection failed to {redis_url} ({exc})")
    return Diagnostic("Redis", True, f"reachable at {redis_url}")


def _check_whisper() -> Diagnostic:
    try:
        importlib.import_module("whisper")
    except ImportError as exc:
        return Diagnostic("Whisper", False, f"import failed ({exc})")
    return Diagnostic("Whisper", True, "import successful")


def _check_openai_key(env: dict[str, str]) -> Diagnostic:
    key = env.get("OPENAI_API_KEY", "")
    if key:
        return Diagnostic("OPENAI_API_KEY", True, "present")
    return Diagnostic("OPENAI_API_KEY", False, "missing or empty")


def run_diagnostics(*, redis_url: str = DEFAULT_REDIS_URL, env: dict[str, str] | None = None) -> Tuple[bool, List[str]]:
    """Run health checks and return tuple(success, issues)."""

    environment = env or os.environ

    checks: Sequence[Diagnostic] = (
        _check_ffmpeg(),
        _check_redis(redis_url),
        _check_whisper(),
        _check_openai_key(environment),
    )

    issues = [f"{check.name}: {check.message}" for check in checks if not check.ok]
    return (len(issues) == 0, issues)


def format_report(ok: bool, issues: Sequence[str]) -> str:
    if ok:
        return "✅ Vidmelt doctor: all checks passed"
    bullet_list = "\n".join(f" - {issue}" for issue in issues)
    return f"❌ Vidmelt doctor found issues:\n{bullet_list}"


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover - thin CLI wrapper
    ok, issues = run_diagnostics()
    print(format_report(ok, issues))
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
