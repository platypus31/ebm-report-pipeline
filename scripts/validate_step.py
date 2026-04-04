#!/usr/bin/env python3
"""
驗證 EBM 報告各步驟的產出檔案是否完整。

用法：
    python3 scripts/validate_step.py --project <name> --step ask
    python3 scripts/validate_step.py --project <name> --step all
    python3 scripts/validate_step.py --project <name>  # 等同 --step all
"""

import argparse
import csv
import sys
from pathlib import Path

# 每個步驟需要的檔案（required=必要, optional=選擇性）
STEP_REQUIREMENTS = {
    "ask": {
        "dir": "01_ask",
        "required": [
            ("pico.yaml", "PICO 結構化分析"),
            ("clinical_scenario.md", "臨床情境"),
            ("classification.md", "問題分類"),
        ],
        "optional": [
            ("introduction.md", "背景資訊"),
        ],
    },
    "acquire": {
        "dir": "02_acquire",
        "required": [
            ("search_strategy.md", "搜尋策略"),
            ("selected_articles.md", "選定文獻"),
        ],
        "optional": [
            ("prisma_flow.md", "PRISMA 流程圖"),
            ("candidates.csv", "候選文獻列表"),
        ],
    },
    "appraise": {
        "dir": "03_appraise",
        "required": [
            ("tool_selection.md", "評讀工具選擇"),
            ("appraisal.csv", "評讀結果（結構化）"),
            ("results_summary.md", "研究結果摘要"),
        ],
        "optional": [
            ("coi_check.md", "利益衝突檢核"),
            ("grade.md", "GRADE 評定"),
        ],
    },
    "apply": {
        "dir": "04_apply",
        "required": [
            ("evidence_level.md", "證據等級"),
            ("clinical_reply.md", "臨床回覆"),
        ],
        "optional": [
            ("local_considerations.md", "在地化考量"),
        ],
    },
    "audit": {
        "dir": "05_audit",
        "required": [
            ("self_assessment.md", "自我評估"),
        ],
        "optional": [],
    },
    "slides": {
        "dir": "06_slides",
        "required": [
            ("slides.json", "簡報資料 JSON"),
        ],
        "optional": [
            ("ebm-report.pptx", "PowerPoint 檔案"),
        ],
    },
}


def validate_file(filepath: Path) -> dict:
    """Check if file exists and is non-empty."""
    result = {"exists": False, "non_empty": False, "size": 0}
    if filepath.exists():
        result["exists"] = True
        result["size"] = filepath.stat().st_size
        result["non_empty"] = result["size"] > 10  # more than just whitespace
    return result


def validate_csv(filepath: Path) -> dict:
    """Validate CSV has headers and at least one data row."""
    result = validate_file(filepath)
    if result["non_empty"]:
        try:
            with open(filepath, encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                first_row = next(reader, None)
                result["has_headers"] = headers is not None and len(headers) > 0
                result["has_data"] = first_row is not None
        except Exception:
            result["has_headers"] = False
            result["has_data"] = False
    return result


def validate_step(project_path: Path, step: str) -> tuple[int, int, list]:
    """Validate a single step. Returns (pass_count, fail_count, messages)."""
    req = STEP_REQUIREMENTS[step]
    step_dir = project_path / req["dir"]
    passes = 0
    fails = 0
    messages = []

    if not step_dir.exists():
        messages.append(f"  目錄不存在：{req['dir']}/")
        return 0, len(req["required"]), messages

    for filename, desc in req["required"]:
        filepath = step_dir / filename
        if filename.endswith(".csv"):
            result = validate_csv(filepath)
            if result["exists"] and result.get("has_data", result["non_empty"]):
                passes += 1
                messages.append(f"  ✓ {filename} — {desc}")
            else:
                fails += 1
                messages.append(f"  ✗ {filename} — {desc}（缺少或為空）")
        else:
            result = validate_file(filepath)
            if result["non_empty"]:
                passes += 1
                messages.append(f"  ✓ {filename} — {desc}")
            else:
                fails += 1
                messages.append(f"  ✗ {filename} — {desc}（缺少或為空）")

    for filename, desc in req["optional"]:
        filepath = step_dir / filename
        result = validate_file(filepath)
        if result["non_empty"]:
            messages.append(f"  ○ {filename} — {desc}")
        else:
            messages.append(f"  - {filename} — {desc}（未產出，選擇性）")

    return passes, fails, messages


def main():
    parser = argparse.ArgumentParser(
        description="驗證 EBM 報告步驟產出是否完整",
    )
    parser.add_argument("--project", required=True, help="專案名稱")
    parser.add_argument(
        "--step",
        default="all",
        choices=["ask", "acquire", "appraise", "apply", "audit", "slides", "all"],
        help="要驗證的步驟（預設：all）",
    )

    args = parser.parse_args()
    project_path = Path(__file__).resolve().parent.parent / "projects" / args.project

    if not project_path.exists():
        print(f"錯誤：找不到專案 '{args.project}'。", file=sys.stderr)
        print(f"路徑：{project_path}", file=sys.stderr)
        sys.exit(1)

    steps = list(STEP_REQUIREMENTS.keys()) if args.step == "all" else [args.step]
    total_pass = 0
    total_fail = 0

    print(f"═══ 驗證 EBM 專案：{args.project} ═══\n")

    for step in steps:
        step_label = {
            "ask": "ASK（問題）",
            "acquire": "ACQUIRE（檢索）",
            "appraise": "APPRAISE（評讀）",
            "apply": "APPLY（應用）",
            "audit": "AUDIT（評估）",
            "slides": "SLIDES（簡報）",
        }[step]

        passes, fails, messages = validate_step(project_path, step)
        total_pass += passes
        total_fail += fails

        status = "✓ 通過" if fails == 0 else f"✗ 缺少 {fails} 項"
        print(f"【{step_label}】{status}")
        for msg in messages:
            print(msg)
        print()

    print("═══ 總結 ═══")
    print(f"通過：{total_pass} 項 | 缺少：{total_fail} 項")

    if total_fail > 0:
        print(f"\n提示：使用 /ebm 繼續完成缺少的步驟。")
        sys.exit(1)
    else:
        print(f"\n所有必要產出已完成，可以產生簡報！")
        sys.exit(0)


if __name__ == "__main__":
    main()
