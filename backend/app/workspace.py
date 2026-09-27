"""Temporary project files for a pair's build round."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def apply_named(
    files: dict[str, str],
    prompt: str,
    solutions: dict[str, str],
    jobs: dict[str, str],
    gates: dict[str, tuple[str, ...]] | None = None,
) -> tuple[dict[str, str], str]:
    """Write a solved file when the prompt names that file and its rule.

    Naming the function, or pasting the NotImplementedError line, is not enough.
    Used when Grok is offline, and as the stand-in edit for rehearsal.
    """
    lowered = prompt.lower()
    updated = dict(files)
    changed: list[str] = []
    needed = gates or {}
    for filename, content in solutions.items():
        words = needed.get(filename, ())
        named = filename.lower() in lowered and any(word.lower() in lowered for word in words)
        if named and filename in updated:
            updated[filename] = content
            changed.append(filename)
    if not changed:
        return updated, "Name the file and the rule for that file. Pasting the error is not enough."
    return updated, "Updated " + ", ".join(changed) + "."


def apply_edits(files: dict[str, str], edits: list[dict]) -> dict[str, str]:
    """Replace existing project files. Unknown paths are ignored."""
    updated = dict(files)
    allowed = set(updated)
    for edit in edits:
        if not isinstance(edit, dict):
            continue
        name = Path(str(edit.get("path") or "")).name
        content = edit.get("content")
        if name not in allowed or not isinstance(content, str):
            continue
        updated[name] = content[:20_000]
    return updated


def project_passes(files: dict[str, str], check: str) -> bool:
    """Run the round's check against the current files. False on any failure."""
    if not check or not files:
        return False
    try:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name, body in files.items():
                (folder / Path(name).name).write_text(body, encoding="utf-8")
            (folder / "_check.py").write_text(check, encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "_check.py"],
                cwd=folder,
                timeout=3,
                capture_output=True,
                check=False,
            )
            return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False
