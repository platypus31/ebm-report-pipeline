#!/usr/bin/env python3
"""
共用工具模組 — 統一路徑解析、YAML 讀取、檔案驗證。

供 scripts/ 下的所有腳本共用，避免重複實作。
"""

from pathlib import Path

try:
    import yaml as _yaml
    HAS_YAML = True
except ImportError:
    _yaml = None  # type: ignore[assignment]
    HAS_YAML = False

# ── 路徑解析 ──

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECTS_DIR = BASE_DIR / "projects"


def get_project_path(name: str) -> Path:
    """Return the project directory path for a given project name."""
    return PROJECTS_DIR / name


# ── YAML 讀取 ──

def _parse_yaml_fallback(filepath: Path) -> dict:
    """Fallback YAML parser when PyYAML is not installed.

    Handles up to 4 levels of indentation (0, 2, 4, 6 spaces).
    """
    data: dict = {}
    stack: list[tuple[int, dict, str]] = []  # (indent_level, parent_dict, key)

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if ":" not in stripped:
                continue

            # Calculate indent level
            indent = len(line) - len(line.lstrip())

            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")

            # Pop stack to find parent at correct indent
            while stack and stack[-1][0] >= indent:
                stack.pop()

            if stack:
                parent = stack[-1][1]
                parent_key = stack[-1][2]
                target = parent.get(parent_key, {})
                if not isinstance(target, dict):
                    target = {}
                parent[parent_key] = target
            else:
                target = data

            if val:
                # Handle list values like "[]"
                if val == "[]":
                    target[key] = []
                else:
                    target[key] = val
            else:
                target[key] = {}
                stack.append((indent, target, key))

    return data


def read_yaml(filepath: Path) -> dict:
    """Read a YAML file using PyYAML if available, else fallback parser.

    Returns empty dict on any error.
    """
    if not filepath.exists():
        return {}
    try:
        if HAS_YAML:
            with open(filepath, encoding="utf-8") as f:
                return _yaml.safe_load(f) or {}
        return _parse_yaml_fallback(filepath)
    except Exception:
        return {}


# ── 檔案驗證 ──

MIN_CONTENT_BYTES = 10


def file_has_content(filepath: Path, min_bytes: int = MIN_CONTENT_BYTES) -> bool:
    """Check that a file exists and has meaningful content (not just whitespace)."""
    return filepath.exists() and filepath.stat().st_size >= min_bytes
