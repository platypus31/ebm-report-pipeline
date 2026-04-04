#!/usr/bin/env python3
"""
從專��結構化檔案自動��裝簡報大綱 (slides.json)。

讀取 projects/<name>/ ���所有 5A 步驟產出，組合為 generate_pptx.py 可用的 JSON。

用法：
    python3 scripts/build_slide_outline.py --project <name>
    python3 scripts/build_slide_outline.py --project <name> --style formal
    python3 scripts/build_slide_outline.py --project <name> --author "王大明"
"""

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path


def read_md(filepath: Path) -> str:
    """Read markdown file, return empty string if not found."""
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return ""


def read_csv_rows(filepath: Path) -> list[dict]:
    """Read CSV file rows."""
    if not filepath.exists():
        return []
    with open(filepath, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def extract_yaml_field(content: str, field: str) -> str:
    """Simple extraction of a YAML field value."""
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith(f"{field}:"):
            val = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            return val
    return ""


def extract_bullets(md_content: str, max_bullets: int = 5) -> list[str]:
    """Extract bullet points from markdown content."""
    bullets = []
    for line in md_content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            bullet = stripped[2:].strip()
            if bullet and not bullet.startswith("["):  # skip checkbox markers
                bullets.append(bullet)
                if len(bullets) >= max_bullets:
                    break
    return bullets


def extract_table_data(md_content: str) -> tuple[list[str], list[list[str]]]:
    """Extract first markdown table from content."""
    headers = []
    rows = []
    in_table = False

    for line in md_content.split("\n"):
        stripped = line.strip()
        if "|" in stripped and not stripped.startswith("|-"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if not in_table:
                # Check if this is a separator line
                if all(re.match(r"^-+$", c.strip()) for c in cells):
                    continue
                headers = cells
                in_table = True
            elif all(re.match(r"^-+$", c.strip()) for c in cells):
                continue  # separator
            else:
                rows.append(cells)

    return headers, rows


def build_slides(project: Path, style: str, author: str) -> dict:
    """Build slides.json from project files."""
    ask_dir = project / "01_ask"
    acq_dir = project / "02_acquire"
    app_dir = project / "03_appraise"
    apply_dir = project / "04_apply"
    audit_dir = project / "05_audit"

    # Read pico.yaml
    pico_content = read_md(ask_dir / "pico.yaml")
    topic = extract_yaml_field(pico_content, "topic") or "EBM Report"
    department = extract_yaml_field(pico_content, "  name") or ""

    slides = []

    # ═══ ASK ═══
    slides.append({"type": "section", "title": "ASK", "subtitle": "問題"})

    # Clinical scenario
    scenario = read_md(ask_dir / "clinical_scenario.md")
    if scenario:
        bullets = extract_bullets(scenario)
        if not bullets:
            # Extract paragraphs as bullets
            paras = [p.strip() for p in scenario.split("\n\n") if p.strip() and not p.strip().startswith("#")]
            bullets = paras[:4]
        slides.append({"type": "content", "title": "臨床場景", "bullets": bullets[:5], "section": "ASK"})

    # Introduction
    intro = read_md(ask_dir / "introduction.md")
    if intro:
        bullets = extract_bullets(intro)
        if bullets:
            slides.append({"type": "content", "title": "��景資訊", "bullets": bullets[:5], "section": "ASK"})

    # PICO
    pico_bullets = []
    for elem, label in [("p", "P"), ("i", "I"), ("c", "C")]:
        zh = extract_yaml_field(pico_content, f"    zh")  # simplified
        if zh:
            pico_bullets.append(f"{label}: {zh}")
    if not pico_bullets:
        # Fallback: extract from raw content
        for line in pico_content.split("\n"):
            s = line.strip()
            if s.startswith("zh:"):
                val = s.split(":", 1)[1].strip().strip('"').strip("'")
                if val:
                    pico_bullets.append(val)
    if pico_bullets:
        slides.append({"type": "content", "title": "PICO 分析", "bullets": pico_bullets[:4], "section": "ASK"})

    # Classification
    classify = read_md(ask_dir / "classification.md")
    if classify:
        bullets = extract_bullets(classify)
        if not bullets:
            # Try to find type line
            for line in classify.split("\n"):
                if "治���型" in line or "診斷型" in line or "預後型" in line or "預防型" in line or "病因" in line:
                    bullets.append(line.strip().lstrip("#").strip())
                    break
        if bullets:
            slides.append({"type": "content", "title": "問題分類", "bullets": bullets[:4], "section": "ASK"})

    # ═══ ACQUIRE ═══
    slides.append({"type": "section", "title": "ACQUIRE", "subtitle": "檢索"})

    # Search strategy
    search = read_md(acq_dir / "search_strategy.md")
    if search:
        bullets = extract_bullets(search)
        if bullets:
            slides.append({"type": "content", "title": "搜尋策略", "bullets": bullets[:5], "section": "ACQUIRE"})

    # 6S results table
    headers, rows = extract_table_data(search)
    if headers and rows:
        slides.append({"type": "table", "title": "6S 搜尋結果", "headers": headers, "rows": rows[:6], "section": "ACQUIRE"})

    # PRISMA flow
    prisma = read_md(acq_dir / "prisma_flow.md")
    if prisma:
        # Extract summary table
        h, r = extract_table_data(prisma)
        if h and r:
            slides.append({"type": "table", "title": "PRISMA 篩選流程", "headers": h, "rows": r[:5], "section": "ACQUIRE"})

    # Candidates comparison
    candidates = read_csv_rows(acq_dir / "candidates.csv")
    if candidates:
        headers_csv = ["標題", "期刊", "年份", "研究類���"]
        rows_csv = []
        for c in candidates[:5]:
            rows_csv.append([
                c.get("title", "")[:40] + "...",
                c.get("journal", ""),
                c.get("year", ""),
                c.get("study_type", ""),
            ])
        slides.append({"type": "table", "title": "收納文獻比較", "headers": headers_csv, "rows": rows_csv, "section": "ACQUIRE"})

    # Selected articles
    selected = read_md(acq_dir / "selected_articles.md")
    if selected:
        bullets = extract_bullets(selected)
        if bullets:
            slides.append({"type": "content", "title": "選文理由", "bullets": bullets[:5], "section": "ACQUIRE"})

    # ═══ APPRAISE ═══
    slides.append({"type": "section", "title": "APPRAISE", "subtitle": "評讀"})

    # Tool selection
    tool_sel = read_md(app_dir / "tool_selection.md")
    if tool_sel:
        bullets = extract_bullets(tool_sel)
        if bullets:
            slides.append({"type": "content", "title": "評讀工具選擇", "bullets": bullets[:4], "section": "APPRAISE"})

    # Appraisal questions — group by section
    appraisal_rows = read_csv_rows(app_dir / "appraisal.csv")
    current_section = ""
    section_slides = []
    for row in appraisal_rows:
        section = row.get("section", "")
        q_zh = row.get("question_zh", row.get("question", ""))
        answer = row.get("answer", "")
        analysis = row.get("analysis", "")

        if section != current_section:
            current_section = section
            section_label = {
                "A-Validity": "Section A — Validity（效度）",
                "B-Results": "Section B — Results（結果）",
                "C-Applicability": "Section C — Applicability（適用性）",
            }.get(section, section)
            section_slides.append({
                "type": "content",
                "title": section_label,
                "bullets": [],
                "section": "APPRAISE",
            })

        if section_slides:
            bullet = f"Q{row.get('number', '?')}: {q_zh} → {answer}"
            section_slides[-1]["bullets"].append(bullet)

    # Add appraisal slides (max 3 bullets per slide, split if needed)
    for slide_data in section_slides:
        bs = slide_data["bullets"]
        if len(bs) <= 4:
            slides.append(slide_data)
        else:
            for i in range(0, len(bs), 3):
                chunk = bs[i:i+3]
                part = (i // 3) + 1
                slides.append({
                    "type": "content",
                    "title": f"{slide_data['title']} ({part})",
                    "bullets": chunk,
                    "section": "APPRAISE",
                })

    # COI check
    coi = read_md(app_dir / "coi_check.md")
    if coi:
        bullets = extract_bullets(coi)
        if not bullets:
            bullets = [line.strip() for line in coi.split("\n")
                      if line.strip().startswith("**") and ":" in line]
        if bullets:
            slides.append({"type": "content", "title": "利益衝突檢核", "bullets": bullets[:4], "section": "APPRAISE"})

    # Results summary
    results = read_md(app_dir / "results_summary.md")
    if results:
        headers_r, rows_r = extract_table_data(results)
        if headers_r and rows_r:
            slides.append({"type": "table", "title": "研究結果", "headers": headers_r, "rows": rows_r[:5], "section": "APPRAISE"})

    # ═══ APPLY ═══
    slides.append({"type": "section", "title": "APPLY", "subtitle": "應用"})

    # Evidence level
    evidence = read_md(apply_dir / "evidence_level.md")
    if evidence:
        bullets = extract_bullets(evidence)
        if bullets:
            slides.append({"type": "content", "title": "OCEBM 證據等級", "bullets": bullets[:4], "section": "APPLY"})

    # Local considerations
    local = read_md(apply_dir / "local_considerations.md")
    if local:
        bullets = extract_bullets(local)
        if bullets:
            slides.append({"type": "content", "title": "台灣在地化考量", "bullets": bullets[:5], "section": "APPLY"})

    # Clinical reply
    reply = read_md(apply_dir / "clinical_reply.md")
    if reply:
        # Extract the dialogue part
        bullets = []
        in_quote = False
        for line in reply.split("\n"):
            s = line.strip()
            if s.startswith(">"):
                text = s.lstrip(">").strip()
                if text:
                    bullets.append(text)
            elif s.startswith("- ") or s.startswith("* "):
                bullets.append(s[2:].strip())
        if bullets:
            # Split into 2 slides if long
            if len(bullets) > 5:
                slides.append({"type": "content", "title": "臨床回覆 (1/2)", "bullets": bullets[:4], "section": "APPLY"})
                slides.append({"type": "content", "title": "臨床回覆 (2/2)", "bullets": bullets[4:8], "section": "APPLY"})
            else:
                slides.append({"type": "content", "title": "臨床回覆", "bullets": bullets[:5], "section": "APPLY"})

    # ═══ AUDIT ═══
    slides.append({"type": "section", "title": "AUDIT", "subtitle": "評估"})

    audit = read_md(audit_dir / "self_assessment.md")
    if audit:
        bullets = extract_bullets(audit)
        if bullets:
            slides.append({"type": "content", "title": "自我評估", "bullets": bullets[:6], "section": "AUDIT"})

    # References
    slides.append({"type": "content", "title": "References", "bullets": ["（由評讀文獻自動產生）"], "section": "AUDIT"})

    return {
        "title": topic,
        "author": author,
        "department": department,
        "date": date.today().isoformat(),
        "style": style,
        "slides": slides,
    }


def main():
    parser = argparse.ArgumentParser(
        description="從專案檔案自動組裝簡報大綱 (slides.json)",
        epilog=(
            "範例：\n"
            "  python3 scripts/build_slide_outline.py --project sglt2i-ckd\n"
            "  python3 scripts/build_slide_outline.py --project sglt2i-ckd --style competition --author 王大明\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--project", required=True, help="專案名稱")
    parser.add_argument("--style", default="formal", choices=["formal", "clean", "teaching", "competition"],
                        help="簡報風格（預設 formal）")
    parser.add_argument("--author", default="", help="報告者姓名")
    parser.add_argument("--output", help="輸出路徑（預設寫入專�� 06_slides/）")

    args = parser.parse_args()
    base_dir = Path(__file__).resolve().parent.parent
    project = base_dir / "projects" / args.project

    if not project.exists():
        print(f"錯誤：找不到專案 '{args.project}'。", file=sys.stderr)
        sys.exit(1)

    data = build_slides(project, args.style, args.author)

    output_path = Path(args.output) if args.output else project / "06_slides" / "slides.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"簡報大綱已產生：{output_path}")
    print(f"  投影片數：{len(data['slides'])} 張")
    print(f"  風格：{args.style}")
    print()
    print("下一步：")
    print(f"  python3 scripts/generate_pptx.py {output_path} {project / '06_slides' / 'ebm-report.pptx'}")


if __name__ == "__main__":
    main()
