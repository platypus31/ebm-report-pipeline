#!/usr/bin/env python3
"""
EBM 專案進度總覽儀表板。

用法：
    python3 scripts/status.py              # 顯示所有專案（排除 example-*）
    python3 scripts/status.py --all        # 包含範例專案
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# 5A 步驟與對應目錄 / 必要檔案（精簡版，取自 validate_step.py）
STEPS = {
    "ASK": {
        "dir": "01_ask",
        "required": ["pico.yaml", "clinical_scenario.md", "classification.md"],
    },
    "ACQUIRE": {
        "dir": "02_acquire",
        "required": ["search_strategy.md", "selected_articles.md"],
    },
    "APPRAISE": {
        "dir": "03_appraise",
        "required": ["tool_selection.md", "appraisal.csv", "results_summary.md"],
    },
    "APPLY": {
        "dir": "04_apply",
        "required": ["evidence_level.md", "clinical_reply.md"],
    },
    "AUDIT": {
        "dir": "05_audit",
        "required": ["self_assessment.md"],
    },
    "SLIDES": {
        "dir": "06_slides",
        "required": ["slides.json"],
    },
}

STEP_NAMES = list(STEPS.keys())


def get_topic(project_path: Path) -> str:
    """從 TOPIC.txt 或 pico.yaml 取得主題名稱。"""
    topic_file = project_path / "TOPIC.txt"
    if topic_file.exists():
        lines = topic_file.read_text(encoding="utf-8").splitlines()
        in_question = False
        for line in lines:
            if "臨床問題" in line:
                in_question = True
                continue
            if in_question and line.strip().startswith("##"):
                break
            if in_question and line.strip():
                return line.strip()[:60]

    # Fallback: pico.yaml 的 topic 欄位
    pico_file = project_path / "01_ask" / "pico.yaml"
    if pico_file.exists():
        for line in pico_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("topic:"):
                val = line.split(":", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val[:60]

    return "（未設定主題）"


def check_step(project_path: Path, step_name: str) -> bool:
    """檢查單一步驟是否完成（所有必要檔案存在且非空）。"""
    spec = STEPS[step_name]
    step_dir = project_path / spec["dir"]
    if not step_dir.exists():
        return False
    for filename in spec["required"]:
        fp = step_dir / filename
        if not fp.exists() or fp.stat().st_size <= 10:
            return False
    return True


def get_last_modified(project_path: Path) -> str:
    """取得專案目錄中最新修改日期。"""
    latest = 0.0
    for f in project_path.rglob("*"):
        if f.is_file():
            mtime = f.stat().st_mtime
            if mtime > latest:
                latest = mtime
    if latest == 0.0:
        return "—"
    return datetime.fromtimestamp(latest).strftime("%Y-%m-%d")


def build_progress_bar(project_path: Path) -> str:
    """產生進度條字串，例如 "ASK ✓  ACQUIRE ✓  APPRAISE →  APPLY  AUDIT  SLIDES"。"""
    parts = []
    found_incomplete = False
    for name in STEP_NAMES:
        done = check_step(project_path, name)
        if done:
            parts.append(f"{name} ✓")
        elif not found_incomplete:
            parts.append(f"{name} →")
            found_incomplete = True
        else:
            parts.append(name)
    return "  ".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="EBM 專案進度總覽",
    )
    parser.add_argument(
        "--all", action="store_true", help="包含範例專案（example-*）",
    )
    args = parser.parse_args()

    projects_dir = Path(__file__).resolve().parent.parent / "projects"
    if not projects_dir.exists():
        print("錯誤：找不到 projects/ 目錄。", file=sys.stderr)
        sys.exit(1)

    # 收集專案目錄
    dirs = sorted(
        d for d in projects_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )
    if not args.all:
        dirs = [d for d in dirs if not d.name.startswith("example-")]

    if not dirs:
        hint = "" if args.all else "（加上 --all 可顯示範例專案）"
        print(f"目前沒有專案。{hint}")
        sys.exit(0)

    # 顯示表格
    print("═══ EBM 專案進度總覽 ═══\n")
    for d in dirs:
        topic = get_topic(d)
        progress = build_progress_bar(d)
        modified = get_last_modified(d)
        print(f"【{d.name}】")
        print(f"  主題：{topic}")
        print(f"  進度：{progress}")
        print(f"  更新：{modified}")
        print()

    total = len(dirs)
    done = sum(
        1 for d in dirs
        if all(check_step(d, s) for s in STEP_NAMES)
    )
    print(f"共 {total} 個專案，{done} 個已完成。")
    if not args.all:
        examples = sum(
            1 for d in projects_dir.iterdir()
            if d.is_dir() and d.name.startswith("example-")
        )
        if examples:
            print(f"（另有 {examples} 個範例專案，使用 --all 顯示）")


if __name__ == "__main__":
    main()
