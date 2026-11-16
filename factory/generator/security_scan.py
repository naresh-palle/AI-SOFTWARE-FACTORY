"""
Static scan of a generated workspace.

The scan reads source files and records findings. It does not execute them.
"""

import re
from pathlib import Path
from typing import Dict, List

from factory.generator.workspace import WorkspaceManager


BLOCKING_RULES = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"), "critical"),
    ("github_token", re.compile(r"ghp_[A-Za-z0-9]{20,}"), "critical"),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}"), "critical"),
    ("live_stripe_key", re.compile(r"sk_live_[A-Za-z0-9]+"), "critical"),
)

ADVISORY_RULES = (
    ("embedded_signing_key", re.compile(r"development-secret-key"), "medium"),
    ("dynamic_exec", re.compile(r"\beval\s*\("), "high"),
    ("shell_true", re.compile(r"shell\s*=\s*True"), "high"),
)

SKIP_PARTS = {".git", ".worktrees", ".sandbox-deps", "node_modules", ".next", "__pycache__"}
BLOCKED_NAMES = {".env", ".env.local", "id_rsa", "credentials.json", "secrets.json"}


def find_blocking_secrets(workspace: WorkspaceManager) -> List[Dict[str, str]]:
    return [item for item in scan_workspace(workspace) if item["blocking"]]


def scan_workspace(workspace: WorkspaceManager, root: Path | None = None) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    scan_root = (root or workspace.active_root).resolve()
    for path in scan_root.rglob("*"):
        if not path.is_file():
            continue
        relative_to_scan = path.relative_to(scan_root)
        if any(part in SKIP_PARTS for part in relative_to_scan.parts):
            continue
        relative = str(path.relative_to(workspace.workspace_path)).replace("\\", "/")
        if path.name in BLOCKED_NAMES:
            findings.append(_finding(relative, "blocked_filename", "critical", True))
            continue
        if path.stat().st_size > 1_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for rule, pattern, severity in BLOCKING_RULES:
            if pattern.search(text):
                findings.append(_finding(relative, rule, severity, True))
                break
        else:
            for rule, pattern, severity in ADVISORY_RULES:
                if pattern.search(text):
                    findings.append(_finding(relative, rule, severity, False))
                    break
    return findings


def _finding(relative: str, rule: str, severity: str, blocking: bool) -> Dict[str, object]:
    return {
        "path": relative,
        "rule": rule,
        "severity": severity,
        "blocking": blocking,
        "title": f"{severity} {rule} in {Path(relative).name}",
    }
