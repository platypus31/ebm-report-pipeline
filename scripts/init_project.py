#!/usr/bin/env python3
"""
初始化 EBM 報告專案目錄結構。

用法：
    python3 scripts/init_project.py --name <project-name>
    python3 scripts/init_project.py --name sglt2i-ckd --department 腎臟內科

建立 projects/<project-name>/ 目錄，包含所有 5A 階段的子目錄與模板檔案。
"""

import argparse
import sys
from datetime import date
from pathlib import Path

STAGE_DIRS = [
    "01_ask",
    "02_acquire",
    "03_appraise",
    "04_apply",
    "05_audit",
    "06_slides",
    "assets/screenshots",
]

PICO_TEMPLATE = """\
# PICO 分析
# 由 /pico 或 /ebm 流程自動填寫

version: "1.0"
created: "{date}"
updated: "{date}"
current_step: "TOPIC"

department:
  name: ""
  name_en: ""
  mesh_terms: []

topic: ""

pico:
  p:
    zh: ""
    mesh: ""
  i:
    zh: ""
    mesh: ""
  c:
    zh: ""
    mesh: ""
  o:
    primary:
      zh: ""
      mesh: ""
    secondary:
      zh: ""
      mesh: ""

classification:
  type: ""          # therapeutic / preventive / diagnostic / prognostic / etiology_harm
  type_zh: ""
  reasoning: ""
  pubmed_filter: ""
"""

TOPIC_TEMPLATE = """\
# EBM 報告主題

請在此描述你的臨床問題或研究主題。

## 科別


## 臨床問題


## 備註

"""

README_TEMPLATE = """\
# {name}

**建立日期**: {date}
**目前步驟**: TOPIC

## 專案結構

```
{name}/
├── TOPIC.txt              # 主題描述
├── 01_ask/                # ASK — PICO、臨床情境、背景、分類
│   ├── pico.yaml          # PICO 結構化資料
│   ├── clinical_scenario.md
│   ├── introduction.md
│   └── classification.md
├── 02_acquire/            # ACQUIRE — 搜尋策略、PRISMA、選文
│   ├── search_strategy.md
│   ├── prisma_flow.md
│   ├── candidates.csv
│   └── selected_articles.md
├── 03_appraise/           # APPRAISE — 評讀結果
│   ├── tool_selection.md
│   ├── appraisal.csv
│   ├── coi_check.md
│   ├── results_summary.md
│   └── grade.md
├── 04_apply/              # APPLY — 臨床應用
│   ├── evidence_level.md
│   ├── local_considerations.md
│   └── clinical_reply.md
├── 05_audit/              # AUDIT — 自我評估
│   └── self_assessment.md
├── 06_slides/             # 簡報輸出
│   ├── slides.json
│   └── ebm-report.pptx
└── assets/                # 截圖與附件
    └── screenshots/       # Playwright 自動截圖
        └── screenshots.json
```
"""


def create_project(name: str, department: str = "") -> Path:
    """Create project directory structure."""
    project_root = Path(__file__).resolve().parent.parent / "projects" / name

    if project_root.exists():
        print(f"錯誤：專案 '{name}' 已存在於 {project_root}", file=sys.stderr)
        sys.exit(1)

    today = date.today().isoformat()

    # Create stage directories
    for stage_dir in STAGE_DIRS:
        (project_root / stage_dir).mkdir(parents=True, exist_ok=True)

    # Write TOPIC.txt
    topic_content = TOPIC_TEMPLATE
    if department:
        topic_content = topic_content.replace("## 科別\n\n", f"## 科別\n\n{department}\n")
    (project_root / "TOPIC.txt").write_text(topic_content, encoding="utf-8")

    # Write pico.yaml template
    pico_content = PICO_TEMPLATE.format(date=today)
    if department:
        # Escape quotes in department name for valid YAML
        safe_dept = department.replace("\\", "\\\\").replace('"', '\\"')
        pico_content = pico_content.replace('  name: ""', f'  name: "{safe_dept}"')
    (project_root / "01_ask" / "pico.yaml").write_text(pico_content, encoding="utf-8")

    # Write project README
    readme = README_TEMPLATE.format(name=name, date=today)
    (project_root / "README.md").write_text(readme, encoding="utf-8")

    # Write screenshots.json manifest
    import json

    manifest = {
        "project": name,
        "created": today,
        "screenshots": [],
    }
    (project_root / "assets" / "screenshots.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return project_root


def main():
    parser = argparse.ArgumentParser(
        description="初始化 EBM 報告專案目錄結構",
        epilog=(
            "範例：\n"
            "  python3 scripts/init_project.py --name sglt2i-ckd\n"
            "  python3 scripts/init_project.py --name hs-ctni-ami --department 急診醫學科\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--name", required=True, help="專案名稱（英文，用 - 連接）")
    parser.add_argument("--department", default="", help="科別名稱（繁體中文）")

    args = parser.parse_args()

    # Validate name
    if not args.name.replace("-", "").replace("_", "").isalnum():
        print("錯誤：專案名稱只能包含英文字母、數字、- 和 _。", file=sys.stderr)
        sys.exit(1)

    project_root = create_project(args.name, args.department)
    print(f"專案已建立：{project_root}")
    print("  TOPIC.txt  — 請填寫你的臨床問題")
    print("  01_ask/pico.yaml — PICO 模板已建立")
    print()
    print("下一步：啟動 Claude Code，輸入 /ebm 開始流程")


if __name__ == "__main__":
    main()
