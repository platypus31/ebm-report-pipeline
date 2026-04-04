#!/usr/bin/env python3
"""
文獻搜尋結果去重工具。

依 PMID → DOI → 標題相似度，移除重複文獻。

用法：
    python3 scripts/dedupe_results.py --project <name>
    python3 scripts/dedupe_results.py --input results.csv --output deduped.csv

輸入 CSV 欄位（至少需要 title，其餘選填）：
    pmid, doi, title, journal, year, study_type, ...

輸出：
    去重後的 CSV + 去重報告
"""

import argparse
import csv
import re
import sys
from pathlib import Path


def normalize_title(title: str) -> str:
    """Normalize title for fuzzy matching."""
    t = title.lower().strip()
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t


def title_similarity(a: str, b: str) -> float:
    """Simple word-overlap similarity (Jaccard)."""
    words_a = set(normalize_title(a).split())
    words_b = set(normalize_title(b).split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def dedupe(rows: list[dict], threshold: float = 0.85) -> tuple[list[dict], list[dict]]:
    """
    Deduplicate rows by PMID, DOI, then title similarity.
    Returns (kept, removed) tuples.
    """
    kept = []
    removed = []
    seen_pmids = set()
    seen_dois = set()
    kept_titles = []

    for row in rows:
        pmid = row.get("pmid", "").strip()
        doi = row.get("doi", "").strip().lower()
        title = row.get("title", "").strip()

        # Check PMID duplicate
        if pmid and pmid in seen_pmids:
            row["_dedupe_reason"] = f"PMID 重複: {pmid}"
            removed.append(row)
            continue

        # Check DOI duplicate
        if doi and doi in seen_dois:
            row["_dedupe_reason"] = f"DOI 重複: {doi}"
            removed.append(row)
            continue

        # Check title similarity
        is_dup = False
        for kept_title in kept_titles:
            sim = title_similarity(title, kept_title)
            if sim >= threshold:
                row["_dedupe_reason"] = f"標題相似 ({sim:.0%}): {kept_title[:60]}..."
                removed.append(row)
                is_dup = True
                break

        if is_dup:
            continue

        # Keep this row
        if pmid:
            seen_pmids.add(pmid)
        if doi:
            seen_dois.add(doi)
        kept_titles.append(title)
        kept.append(row)

    return kept, removed


def main():
    parser = argparse.ArgumentParser(
        description="文獻搜尋結果去重",
        epilog=(
            "範例：\n"
            "  python3 scripts/dedupe_results.py --project sglt2i-ckd\n"
            "  python3 scripts/dedupe_results.py --input results.csv --output deduped.csv\n"
            "  python3 scripts/dedupe_results.py --input results.csv --threshold 0.80\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--project", help="專案名稱")
    parser.add_argument("--input", help="輸入 CSV 檔案")
    parser.add_argument("--output", help="輸出 CSV 檔案")
    parser.add_argument(
        "--threshold", type=float, default=0.85,
        help="標題相似度閾值（預設 0.85）",
    )

    args = parser.parse_args()
    base_dir = Path(__file__).resolve().parent.parent

    if args.project:
        input_path = base_dir / "projects" / args.project / "02_acquire" / "candidates.csv"
        output_path = base_dir / "projects" / args.project / "02_acquire" / "candidates_deduped.csv"
        report_path = base_dir / "projects" / args.project / "02_acquire" / "dedupe_report.md"
    elif args.input:
        input_path = Path(args.input)
        output_path = Path(args.output) if args.output else input_path.with_name("deduped_" + input_path.name)
        report_path = input_path.with_name("dedupe_report.md")
    else:
        parser.print_help()
        sys.exit(1)

    if not input_path.exists():
        print(f"錯誤：找不到輸入檔案 '{input_path}'。", file=sys.stderr)
        sys.exit(1)

    # Read CSV
    with open(input_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if not rows:
        print("輸入檔案為空，無需去重。")
        sys.exit(0)

    print(f"讀取 {len(rows)} 篇文獻...")

    # Deduplicate
    kept, removed = dedupe(rows, args.threshold)

    # Write deduped CSV
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(kept)

    # Write report
    lines = [
        "# 去重報告\n",
        f"- 輸入文獻數：{len(rows)}",
        f"- 去重後文獻數：{len(kept)}",
        f"- 移除重複數：{len(removed)}",
        f"- 相似度閾值：{args.threshold:.0%}",
        "",
    ]

    if removed:
        lines.append("## 移除的重複文獻\n")
        lines.append("| # | 標題 | 移除原因 |")
        lines.append("|---|------|---------|")
        for i, row in enumerate(removed, 1):
            title = row.get("title", "N/A")[:50]
            reason = row.get("_dedupe_reason", "N/A")
            lines.append(f"| {i} | {title}... | {reason} |")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"去重完成：{len(rows)} → {len(kept)} 篇（移除 {len(removed)} 篇）")
    print(f"結果：{output_path}")
    print(f"報告：{report_path}")


if __name__ == "__main__":
    main()
