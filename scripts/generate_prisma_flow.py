#!/usr/bin/env python3
"""
產生 PRISMA 2020 風格的文獻篩選流程圖（文字版）。

用法：
    python3 scripts/generate_prisma_flow.py --project <name>
    python3 scripts/generate_prisma_flow.py --identified 45 --screened 38 --eligible 12 --included 3

從專案的 02_acquire/ 讀取資料，或直接傳入數字。
輸出到 projects/<name>/02_acquire/prisma_flow.md。
"""

import argparse
import json
import sys
from pathlib import Path

PRISMA_TEMPLATE = """\
# PRISMA 篩選流程

```
┌─────────────────────────────────────────────────┐
│              Identification 辨識                  │
│                                                   │
│  資料庫搜尋結果: {identified:>5} 篇                │
│  {db_details}│
│  其他來源:      {other:>5} 篇                     │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
               移除重複: {duplicates:>5} 篇
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│               Screening 篩選                      │
│                                                   │
│  標題/摘要篩選: {screened:>5} 篇                   │
│  排除:          {screen_excluded:>5} 篇            │
│  {screen_reasons}│
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│              Eligibility 合格性                    │
│                                                   │
│  全文評估:      {eligible:>5} 篇                   │
│  排除:          {elig_excluded:>5} 篇              │
│  {elig_reasons}│
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│               Included 收納                       │
│                                                   │
│  最終納入:      {included:>5} 篇                   │
│  {included_types}│
└─────────────────────────────────────────────────┘
```

## 篩選摘要

| 階段 | 數量 | 說明 |
|------|------|------|
| Identification | {identified} | 資料庫搜尋 + 其他來源 |
| 移除重複 | -{duplicates} | DOI/PMID/標題比對 |
| Screening | {screened} | 標題/摘要篩選 |
| Eligibility | {eligible} | 全文評估 |
| **Included** | **{included}** | **最終納入分析** |
"""


def generate_flow(
    identified: int = 0,
    screened: int = 0,
    eligible: int = 0,
    included: int = 0,
    other: int = 0,
    db_counts: dict = None,
    screen_reasons: list = None,
    elig_reasons: list = None,
    included_types: list = None,
) -> str:
    """Generate PRISMA flow text."""
    duplicates = max(0, identified + other - screened) if screened < identified + other else 0
    screen_excluded = max(0, screened - eligible)
    elig_excluded = max(0, eligible - included)

    # Format database details
    db_details = ""
    if db_counts:
        parts = [f"{db}: {n}" for db, n in db_counts.items()]
        db_details = "  (" + ", ".join(parts) + ")\n"
    else:
        db_details = "\n"

    # Format exclusion reasons
    def format_reasons(reasons, prefix="    "):
        if not reasons:
            return "\n"
        return "\n".join(f"{prefix}- {r}" for r in reasons[:4]) + "\n"

    sr = format_reasons(screen_reasons) if screen_reasons else "\n"
    er = format_reasons(elig_reasons) if elig_reasons else "\n"

    # Format included types
    it = ""
    if included_types:
        it = "  " + ", ".join(included_types) + "\n"
    else:
        it = "\n"

    return PRISMA_TEMPLATE.format(
        identified=identified,
        other=other,
        duplicates=duplicates,
        screened=screened,
        screen_excluded=screen_excluded,
        eligible=eligible,
        elig_excluded=elig_excluded,
        included=included,
        db_details=db_details,
        screen_reasons=sr,
        elig_reasons=er,
        included_types=it,
    )


def load_from_project(project_path: Path) -> dict:
    """Try to load PRISMA data from project files."""
    data = {
        "identified": 0,
        "screened": 0,
        "eligible": 0,
        "included": 0,
        "other": 0,
    }

    # Try loading from progress JSON in project dir
    progress_files = sorted(project_path.glob("*.json"))
    if not progress_files:
        # Try legacy output/ location (relative to repo root)
        base_dir = Path(__file__).resolve().parent.parent
        output_dir = base_dir / "output"
        progress_files = sorted(output_dir.glob("ebm-*.json"))

    for pf in progress_files:
        try:
            with open(pf, encoding="utf-8") as f:
                progress = json.load(f)
            prisma = progress.get("search_strategy", {}).get("prisma", {})
            if prisma:
                data["identified"] = prisma.get("identification", 0)
                data["screened"] = prisma.get("screening", 0)
                data["eligible"] = prisma.get("eligibility", 0)
                data["included"] = prisma.get("included", 0)
                return data
        except (json.JSONDecodeError, KeyError):
            continue

    return data


def main():
    parser = argparse.ArgumentParser(
        description="產生 PRISMA 2020 篩選流程圖",
    )
    parser.add_argument("--project", help="專案名稱（從專案讀取資料）")
    parser.add_argument("--identified", type=int, default=0, help="Identification 數量")
    parser.add_argument("--screened", type=int, default=0, help="Screening 數量")
    parser.add_argument("--eligible", type=int, default=0, help="Eligibility 數量")
    parser.add_argument("--included", type=int, default=0, help="Included 數量")
    parser.add_argument("--other", type=int, default=0, help="其他來源數量")
    parser.add_argument("--output", help="輸出檔案路徑（預設寫入專案目錄）")

    args = parser.parse_args()
    base_dir = Path(__file__).resolve().parent.parent

    if args.project:
        project_path = base_dir / "projects" / args.project
        if not project_path.exists():
            print(f"錯誤：找不到專案 '{args.project}'。", file=sys.stderr)
            sys.exit(1)

        data = load_from_project(project_path)
        # Override with command-line args if provided
        if args.identified:
            data["identified"] = args.identified
        if args.screened:
            data["screened"] = args.screened
        if args.eligible:
            data["eligible"] = args.eligible
        if args.included:
            data["included"] = args.included
        if args.other:
            data["other"] = args.other
    else:
        data = {
            "identified": args.identified,
            "screened": args.screened,
            "eligible": args.eligible,
            "included": args.included,
            "other": args.other,
        }

    flow = generate_flow(**data)

    if args.output:
        output_path = Path(args.output)
    elif args.project:
        output_path = base_dir / "projects" / args.project / "02_acquire" / "prisma_flow.md"
    else:
        print(flow)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(flow, encoding="utf-8")
    print(f"PRISMA 流程圖已產生：{output_path}")


if __name__ == "__main__":
    main()
