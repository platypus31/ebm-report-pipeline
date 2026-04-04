#!/usr/bin/env python3
"""
將評讀結果轉換為結構化 CSV，方便製作簡報表格與追蹤。

用法：
    python3 scripts/export_appraisal.py --input appraisal.json --output appraisal.csv
    python3 scripts/export_appraisal.py --project <name>

輸入 JSON 格式（由 /appraise 流程產出）：
{
  "tool": "CASP RCT Checklist",
  "article": {"pmid": "12345", "title": "..."},
  "questions": [
    {"number": 1, "question": "...", "answer": "Yes", "evidence": "...", "analysis": "..."}
  ],
  "summary": {"validity": "通過", "results": "精確", "applicability": "適用"},
  "coi_check": {"funding": "...", "judgment": "..."}
}
"""

import argparse
import csv
import json
import sys
from pathlib import Path


def export_csv(data: dict, output_path: Path) -> None:
    """Export appraisal data to CSV."""
    questions = data.get("questions", [])
    if not questions:
        print("警告：沒有評讀問題資料可匯出。", file=sys.stderr)
        return

    fieldnames = ["number", "section", "question", "question_zh", "answer", "evidence", "analysis"]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for q in questions:
            writer.writerow({
                "number": q.get("number", ""),
                "section": q.get("section", ""),
                "question": q.get("question", ""),
                "question_zh": q.get("question_zh", ""),
                "answer": q.get("answer", ""),
                "evidence": q.get("evidence", ""),
                "analysis": q.get("analysis", ""),
            })

    print(f"評讀結果已匯出：{output_path}")
    print(f"  共 {len(questions)} 題")

    # Summary
    yes_count = sum(1 for q in questions if q.get("answer", "").lower() == "yes")
    no_count = sum(1 for q in questions if q.get("answer", "").lower() == "no")
    ct_count = sum(1 for q in questions if q.get("answer", "").lower() == "can't tell")
    print(f"  Yes: {yes_count} | No: {no_count} | Can't tell: {ct_count}")

    if ct_count > 2:
        print("  ⚠ 警告：Can't tell 超過 2 題，報告品質可能不足。")


def export_coi_md(data: dict, output_path: Path) -> None:
    """Export COI check to markdown."""
    coi = data.get("coi_check")
    if not coi:
        return

    lines = [
        "# 利益衝突檢核 (COI Check)\n",
        f"**經費來源**: {coi.get('funding', 'N/A')}",
        f"**作者隸屬**: {coi.get('author_affiliations', 'N/A')}",
        f"**利益揭露**: {coi.get('disclosure', 'N/A')}",
        f"**判定**: {coi.get('judgment', 'N/A')}",
    ]

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"COI 檢核已匯出：{output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="匯出評讀結果為結構化 CSV",
    )
    parser.add_argument("--input", help="輸入的 JSON 檔案路徑")
    parser.add_argument("--output", help="輸出的 CSV 檔案路徑")
    parser.add_argument("--project", help="專案名稱（自動定位檔案）")

    args = parser.parse_args()
    base_dir = Path(__file__).resolve().parent.parent

    if args.project:
        appraise_dir = base_dir / "projects" / args.project / "03_appraise"
        # Prefer appraisal.json if it exists; fall back to appraisal.csv
        json_path = appraise_dir / "appraisal.json"
        csv_existing = appraise_dir / "appraisal.csv"
        if json_path.exists():
            input_path = json_path
        elif csv_existing.exists():
            print(f"appraisal.csv 已存在於 {csv_existing}，無需從 JSON 匯出。")
            sys.exit(0)
        else:
            input_path = json_path  # will fail with a clear error below
        csv_output = appraise_dir / "appraisal.csv"
        coi_output = appraise_dir / "coi_check.md"
    elif args.input:
        input_path = Path(args.input)
        csv_output = Path(args.output) if args.output else input_path.with_suffix(".csv")
        coi_output = input_path.parent / "coi_check.md"
    else:
        parser.print_help()
        sys.exit(1)

    if not input_path.exists():
        print(f"錯誤：找不到輸入檔案 '{input_path}'。", file=sys.stderr)
        sys.exit(1)

    try:
        with open(input_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"錯誤：JSON 格式不正確。{e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict):
        print("錯誤：JSON 內容必須是物件（字典），不是陣列或純值。", file=sys.stderr)
        sys.exit(1)

    export_csv(data, csv_output)
    export_coi_md(data, coi_output)


if __name__ == "__main__":
    main()
