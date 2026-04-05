#!/usr/bin/env python3
"""
從專案結構化檔案自動組裝簡報大綱 (slides.json)。

讀取 projects/<name>/ 中所有 5A 步驟產出，組合為 generate_pptx.py 可用的 JSON。
對齊 data/ebm-slide-template.md 定義的 50-60 張投影片結構。

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


# ── Helper functions ──

def read_md(filepath: Path) -> str:
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return ""


def read_csv_rows(filepath: Path) -> list[dict]:
    if not filepath.exists():
        return []
    try:
        with open(filepath, encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except (UnicodeDecodeError, csv.Error):
        return []


def extract_yaml_field(content: str, field: str) -> str:
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith(f"{field}:"):
            val = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            return val
    return ""


def extract_bullets(md_content: str, max_bullets: int = 5) -> list[str]:
    bullets = []
    for line in md_content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            bullet = stripped[2:].strip()
            if bullet and not bullet.startswith("["):
                bullets.append(bullet)
                if len(bullets) >= max_bullets:
                    break
    return bullets


def extract_checkboxes(md_content: str) -> list[dict]:
    """Extract checkbox items: - [x] text or - [ ] text."""
    items = []
    for line in md_content.split("\n"):
        stripped = line.strip()
        m = re.match(r'^- \[(x| )\]\s+(.+)$', stripped)
        if m:
            items.append({
                "checked": m.group(1) == "x",
                "text": m.group(2).strip(),
            })
    return items


def extract_table_data(md_content: str) -> tuple[list[str], list[list[str]]]:
    headers = []
    rows = []
    in_table = False
    for line in md_content.split("\n"):
        stripped = line.strip()
        if "|" in stripped and not stripped.startswith("|-"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if not in_table:
                if all(re.match(r'^-+$', c.strip()) for c in cells):
                    continue
                headers = cells
                in_table = True
            elif all(re.match(r'^-+$', c.strip()) for c in cells):
                continue
            else:
                rows.append(cells)
    return headers, rows


def extract_paragraphs(md_content: str, max_chars: int = 300) -> list[str]:
    """Extract non-header paragraphs as narrative text."""
    paragraphs = []
    current = []
    for line in md_content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("| ") or stripped.startswith("|-"):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if stripped == "":
            if current:
                paragraphs.append(" ".join(current))
                current = []
        elif not stripped.startswith("- ") and not stripped.startswith("* ") and not stripped.startswith("```"):
            current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))
    return [p for p in paragraphs if len(p) > 10]


def find_screenshots(project: Path, stage: str = None, category: str = None) -> list[dict]:
    """Find screenshot records from screenshots.json."""
    manifest = project / "assets" / "screenshots.json"
    if not manifest.exists():
        return []
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []
    screenshots = data.get("screenshots", [])
    result = []
    for s in screenshots:
        if stage and s.get("stage") != stage:
            continue
        if category and s.get("category") != category:
            continue
        result.append(s)
    return result


def find_screenshot_files(project: Path, pattern: str) -> list[str]:
    """Find actual screenshot files matching a glob pattern."""
    ss_dir = project / "assets" / "screenshots"
    if not ss_dir.exists():
        return []
    matches = sorted(ss_dir.glob(pattern))
    return [str(m.relative_to(project)) for m in matches]


def parse_pico_yaml(ask_dir: Path) -> dict:
    """Parse pico.yaml into structured dict."""
    try:
        # Try with PyYAML first
        import yaml
        with open(ask_dir / "pico.yaml", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        pass
    # Fallback: manual parse
    content = read_md(ask_dir / "pico.yaml")
    if not content:
        return {}
    result = {"pico": {}}
    for elem in ["p", "i", "c"]:
        zh = ""
        keywords = []
        mesh = ""
        in_elem = False
        for line in content.split("\n"):
            if re.match(rf'^\s+{elem}:\s*$', line):
                in_elem = True
                continue
            if in_elem:
                if re.match(r'^\s+[a-z]:\s*$', line) and not line.strip().startswith("zh") and not line.strip().startswith("mesh") and not line.strip().startswith("key") and not line.strip().startswith("det"):
                    in_elem = False
                    continue
                s = line.strip()
                if s.startswith("zh:"):
                    zh = s.split(":", 1)[1].strip().strip('"').strip("'")
                elif s.startswith("mesh:"):
                    mesh = s.split(":", 1)[1].strip().strip("'").strip('"')
                elif s.startswith("- ") and "keywords" not in s:
                    keywords.append(s[2:].strip().strip('"').strip("'"))
        result["pico"][elem] = {"zh": zh, "mesh": mesh, "keywords": keywords}
    # Outcome
    result["pico"]["o"] = {}
    o_zh = ""
    for line in content.split("\n"):
        s = line.strip()
        if "primary:" in line or (s.startswith("zh:") and o_zh == ""):
            pass
        if s.startswith("zh:") and "primary" not in s:
            o_zh = s.split(":", 1)[1].strip().strip('"').strip("'")
    result["pico"]["o"]["zh"] = o_zh

    result["topic"] = extract_yaml_field(content, "topic")
    result["clinical_scenario"] = extract_yaml_field(content, "clinical_scenario")

    # Extract keywords from content
    kw_section = False
    current_keywords = []
    for line in content.split("\n"):
        s = line.strip()
        if s == "keywords:":
            kw_section = True
            continue
        if kw_section:
            if s.startswith("- "):
                current_keywords.append(s[2:].strip().strip('"').strip("'"))
            else:
                kw_section = False

    return result


# ── Section builders ──

def build_ask_slides(project: Path, pico_content: str) -> list[dict]:
    """Build ASK section slides (8-12 slides)."""
    ask_dir = project / "01_ask"
    slides = []

    slides.append({"type": "section", "title": "ASK", "subtitle": "問題"})

    # 1. Clinical scenario as narrative (full text, not just bullets)
    scenario = read_md(ask_dir / "clinical_scenario.md")
    if scenario:
        # First slide: patient narrative
        paras = extract_paragraphs(scenario)
        # Combine into narrative bullets (each paragraph = 1 bullet)
        narrative = []
        for p in paras:
            if len(p) > 10:
                narrative.append(p)
        if narrative:
            # Split across slides if too long
            for i in range(0, len(narrative), 3):
                chunk = narrative[i:i+3]
                suffix = f" ({i//3 + 1}/{(len(narrative)-1)//3 + 1})" if len(narrative) > 3 else ""
                slides.append({
                    "type": "content",
                    "title": f"臨床場景{suffix}",
                    "bullets": chunk,
                    "section": "ASK",
                })

        # Lab data table if present
        h, r = extract_table_data(scenario)
        if h and r:
            slides.append({
                "type": "table",
                "title": "最新檢驗數據",
                "headers": h,
                "rows": r,
                "section": "ASK",
            })

    # 2. Background / Introduction (split into multiple slides)
    intro = read_md(ask_dir / "introduction.md")
    if intro:
        # Extract section-by-section
        current_title = "背景資訊"
        current_bullets = []
        for line in intro.split("\n"):
            stripped = line.strip()
            if stripped.startswith("## "):
                if current_bullets:
                    slides.append({
                        "type": "content",
                        "title": current_title,
                        "bullets": current_bullets[:5],
                        "section": "ASK",
                    })
                    current_bullets = []
                current_title = stripped.lstrip("#").strip()
            elif stripped.startswith("- ") or stripped.startswith("* "):
                current_bullets.append(stripped[2:].strip())
            elif stripped and not stripped.startswith("#") and not stripped.startswith("|") and not stripped.startswith("```") and len(stripped) > 15:
                current_bullets.append(stripped)
        if current_bullets:
            slides.append({
                "type": "content",
                "title": current_title,
                "bullets": current_bullets[:5],
                "section": "ASK",
            })

    # 3. Classification / Clinical Question
    classify = read_md(ask_dir / "classification.md")
    if classify:
        bullets = []
        for line in classify.split("\n"):
            s = line.strip()
            if s.startswith("**") and s.endswith("**"):
                bullets.append(s.strip("*").strip())
            elif s.startswith("- ") and "首選" in s or "替代" in s:
                bullets.append(s[2:].strip())
            elif "治療型" in s or "診斷型" in s or "預後型" in s or "預防型" in s or "病因" in s:
                if not s.startswith("#"):
                    bullets.append(s)
        # Add reasoning
        for line in classify.split("\n"):
            s = line.strip()
            if s.startswith("1.") or s.startswith("2.") or s.startswith("3."):
                bullets.append(s)
        if bullets:
            slides.append({
                "type": "content",
                "title": "臨床問題分類",
                "bullets": bullets[:6],
                "section": "ASK",
            })

        # Best evidence hierarchy
        h, r = extract_table_data(classify)
        if not h:
            # Build from numbered list
            ev_bullets = []
            for line in classify.split("\n"):
                s = line.strip()
                if re.match(r'^\d+\.', s):
                    ev_bullets.append(s)
            if ev_bullets:
                slides.append({
                    "type": "content",
                    "title": "最佳證據層級",
                    "bullets": ev_bullets[:5],
                    "section": "ASK",
                })

    # 4. PICO as table with keywords
    pico_data = parse_pico_yaml(ask_dir)
    pico_section = pico_data.get("pico", {})
    if pico_section:
        headers = ["PICO", "定義", "臨床情境關鍵字", "MeSH Terms"]
        rows = []
        labels = {"p": "P (Population)", "i": "I (Intervention)", "c": "C (Comparison)"}
        for elem, label in labels.items():
            d = pico_section.get(elem, {})
            if isinstance(d, dict):
                zh = d.get("zh", "")
                kw = ", ".join(d.get("keywords", []))
                mesh = d.get("mesh", "")
                if zh:
                    rows.append([label, zh, kw, mesh[:40]])
        # Outcome
        o_data = pico_section.get("o", {})
        if isinstance(o_data, dict):
            primary = o_data.get("primary", o_data)
            if isinstance(primary, dict):
                zh = primary.get("zh", "")
                kw = ", ".join(primary.get("keywords", []))
                mesh = primary.get("mesh", "")
            else:
                zh = o_data.get("zh", "")
                kw = ""
                mesh = ""
            if zh:
                rows.append(["O (Outcome)", zh, kw, mesh[:40] if mesh else ""])
        if rows:
            slides.append({
                "type": "table",
                "title": "PICO 分析",
                "headers": headers,
                "rows": rows,
                "section": "ASK",
            })
    else:
        # Fallback: bullets
        pico_bullets = []
        for line in pico_content.split("\n"):
            s = line.strip()
            if s.startswith("zh:"):
                val = s.split(":", 1)[1].strip().strip('"').strip("'")
                if val:
                    pico_bullets.append(val)
        if pico_bullets:
            slides.append({
                "type": "content",
                "title": "PICO 分析",
                "bullets": pico_bullets[:4],
                "section": "ASK",
            })

    return slides


def build_acquire_slides(project: Path) -> list[dict]:
    """Build ACQUIRE section slides (8-16 slides)."""
    acq_dir = project / "02_acquire"
    slides = []

    slides.append({"type": "section", "title": "ACQUIRE", "subtitle": "檢索"})

    search = read_md(acq_dir / "search_strategy.md")

    # 1. Search strategy explanation
    if search:
        strategy_bullets = []
        for line in search.split("\n"):
            s = line.strip()
            if s.startswith("**") and ":" in s:
                strategy_bullets.append(s.strip("*").strip())
            elif s.startswith("```") or s == "":
                continue
        # Extract PubMed query block
        in_code = False
        query_lines = []
        for line in search.split("\n"):
            if line.strip().startswith("```") and not in_code:
                in_code = True
                continue
            elif line.strip().startswith("```") and in_code:
                in_code = False
                break
            elif in_code:
                query_lines.append(line.strip())
        if query_lines:
            slides.append({
                "type": "content",
                "title": "PubMed 搜尋策略",
                "bullets": query_lines[:6],
                "section": "ACQUIRE",
            })
        if strategy_bullets:
            slides.append({
                "type": "content",
                "title": "搜尋條件",
                "bullets": strategy_bullets[:5],
                "section": "ACQUIRE",
            })

    # 2. 6S results - try screenshot first, fallback to table
    ss_6s = find_screenshot_files(project, "6s-search-*.png")
    if ss_6s:
        for img in ss_6s[:2]:
            slides.append({
                "type": "image",
                "title": "6S 搜尋結果",
                "image_path": img,
                "caption": "6S 階層搜尋結果截圖",
                "section": "ACQUIRE",
            })
    # Always include text table too
    if search:
        headers, rows = extract_table_data(search)
        if headers and rows:
            slides.append({
                "type": "table",
                "title": "6S 搜尋結果摘要",
                "headers": headers,
                "rows": rows[:6],
                "section": "ACQUIRE",
            })

    # 3. Per-database screenshots
    db_screenshots = {
        "pubmed-search": "PubMed 搜尋結果",
        "cochrane-search": "Cochrane Library 搜尋結果",
        "uptodate-search": "UpToDate 搜尋結果",
        "embase-search": "Embase 搜尋結果",
    }
    for pattern, title in db_screenshots.items():
        imgs = find_screenshot_files(project, f"{pattern}-*.png")
        for img in imgs[:1]:
            slides.append({
                "type": "image",
                "title": title,
                "image_path": img,
                "caption": f"{title}截圖",
                "section": "ACQUIRE",
            })

    # 4. PRISMA flow - screenshot first, fallback to table
    prisma = read_md(acq_dir / "prisma_flow.md")
    ss_prisma = find_screenshot_files(project, "prisma-*.png")
    if ss_prisma:
        slides.append({
            "type": "image",
            "title": "PRISMA 篩選流程圖",
            "image_path": ss_prisma[0],
            "caption": "PRISMA 2020 Flow Diagram",
            "section": "ACQUIRE",
        })
    if prisma:
        h, r = extract_table_data(prisma)
        if h and r:
            slides.append({
                "type": "table",
                "title": "PRISMA 篩選流程",
                "headers": h,
                "rows": r[:5],
                "section": "ACQUIRE",
            })

    # 5. Candidates comparison
    candidates = read_csv_rows(acq_dir / "candidates.csv")
    if candidates:
        headers_csv = ["標題", "期刊", "年份", "研究類型"]
        rows_csv = []
        for c in candidates[:5]:
            rows_csv.append([
                c.get("title", "")[:40] + ("..." if len(c.get("title", "")) > 40 else ""),
                c.get("journal", ""),
                c.get("year", ""),
                c.get("study_type", ""),
            ])
        slides.append({
            "type": "table",
            "title": "候選文獻比較",
            "headers": headers_csv,
            "rows": rows_csv,
            "section": "ACQUIRE",
        })

    # 6. Selected articles & rationale
    selected = read_md(acq_dir / "selected_articles.md")
    if selected:
        # Article info table
        h, r = extract_table_data(selected)
        if h and r:
            slides.append({
                "type": "table",
                "title": "選定文獻",
                "headers": h,
                "rows": r[:5],
                "section": "ACQUIRE",
            })

        # Selection rationale
        bullets = extract_bullets(selected, max_bullets=6)
        if bullets:
            slides.append({
                "type": "content",
                "title": "選文理由",
                "bullets": bullets,
                "section": "ACQUIRE",
            })

        # Excluded articles table
        tables_found = 0
        for line in selected.split("\n"):
            if "排除" in line and "#" in line:
                # Find the exclusion table
                rest = selected[selected.index(line):]
                h2, r2 = extract_table_data(rest)
                if h2 and r2:
                    slides.append({
                        "type": "table",
                        "title": "排除文獻與理由",
                        "headers": h2,
                        "rows": r2[:5],
                        "section": "ACQUIRE",
                    })
                break

    return slides


def build_appraise_slides(project: Path) -> list[dict]:
    """Build APPRAISE section slides (15-25 slides)."""
    app_dir = project / "03_appraise"
    slides = []

    slides.append({"type": "section", "title": "APPRAISE", "subtitle": "評讀"})

    # 1. Tool selection
    tool_sel = read_md(app_dir / "tool_selection.md")
    if tool_sel:
        bullets = extract_bullets(tool_sel)
        if not bullets:
            bullets = extract_paragraphs(tool_sel)
        if bullets:
            slides.append({
                "type": "content",
                "title": "評讀工具選擇",
                "bullets": bullets[:4],
                "section": "APPRAISE",
            })

    # 2. Appraisal questions - grouped by section, using appraisal type with colors
    appraisal_rows = read_csv_rows(app_dir / "appraisal.csv")

    # Map CASP questions to screenshot categories
    q_to_screenshot = {
        "1": "article-objective",
        "2": "article-methods",
        "3": "article-flowchart",
        "4": "article-methods",
        "5": "table-baseline",
        "6": "article-methods",
        "7": "article-results",
        "8": "article-results",
        "9": "article-methods",
        "10": "table-outcomes",
        "11": "article-safety",
    }

    current_section = ""
    section_questions = []

    for row in appraisal_rows:
        section = row.get("section", "")
        q_num = row.get("number", "?")
        q_zh = row.get("question_zh", row.get("question", ""))
        answer = row.get("answer", "")
        evidence = row.get("evidence", "")
        analysis = row.get("analysis", "")

        if section != current_section:
            # Flush previous section
            if section_questions:
                _add_appraisal_group(slides, current_section, section_questions, project, q_to_screenshot)
            current_section = section
            section_questions = []

        section_questions.append({
            "number": f"Q{q_num}",
            "text": q_zh,
            "answer": answer,
            "evidence": evidence[:80] if evidence else "",
            "analysis": analysis,
            "q_num": str(q_num),
        })

    # Flush last section
    if section_questions:
        _add_appraisal_group(slides, current_section, section_questions, project, q_to_screenshot)

    # 3. COI check
    coi = read_md(app_dir / "coi_check.md")
    if coi:
        bullets = extract_bullets(coi)
        if not bullets:
            bullets = extract_paragraphs(coi)
        if bullets:
            slides.append({
                "type": "content",
                "title": "利益衝突檢核",
                "bullets": bullets[:4],
                "section": "APPRAISE",
            })

    # 4. Results summary
    results = read_md(app_dir / "results_summary.md")
    if results:
        # Primary outcome table
        _add_results_tables(slides, results, project)

    # 5. GRADE assessment (extract from results_summary if present)
    if results and "GRADE" in results:
        grade_start = results.index("GRADE")
        grade_section = results[grade_start:]
        h, r = extract_table_data(grade_section)
        if h and r:
            slides.append({
                "type": "table",
                "title": "GRADE 證據品質評定",
                "headers": h,
                "rows": r,
                "section": "APPRAISE",
            })

    return slides


def _add_appraisal_group(slides, section_name, questions, project, q_to_screenshot):
    """Add appraisal slides for one section, pairing with article screenshots."""
    section_label = {
        "A-Validity": "Section A — Validity（效度）",
        "B-Results": "Section B — Results（結果）",
        "C-Applicability": "Section C — Applicability（適用性）",
    }.get(section_name, section_name)

    # Split into chunks of max 4 questions per appraisal slide
    for i in range(0, len(questions), 4):
        chunk = questions[i:i+4]
        part_suffix = f" ({i//4 + 1})" if len(questions) > 4 else ""

        slides.append({
            "type": "appraisal",
            "title": f"{section_label}{part_suffix}",
            "questions": [{
                "number": q["number"],
                "text": q["text"],
                "answer": q["answer"],
                "evidence": q["evidence"],
            } for q in chunk],
            "section": "APPRAISE",
        })

        # For each question, try to add corresponding article screenshot
        for q in chunk:
            q_num = q["q_num"]
            ss_category = q_to_screenshot.get(q_num, "")
            if ss_category:
                imgs = find_screenshot_files(project, f"{ss_category}-*.png")
                if imgs:
                    slides.append({
                        "type": "image_content",
                        "title": f"{q['number']}: {q['text'][:30]}...",
                        "image_path": imgs[0],
                        "bullets": [
                            f"判定：{q['answer']}",
                            q.get("analysis", q["evidence"]) or q["evidence"],
                        ],
                        "section": "APPRAISE",
                    })


def _add_results_tables(slides, results_md, project):
    """Extract all tables from results summary and add as slides."""
    sections = re.split(r'^## ', results_md, flags=re.MULTILINE)

    for section in sections:
        if not section.strip():
            continue
        title_line = section.split("\n")[0].strip()
        h, r = extract_table_data(section)

        # Skip GRADE table (handled separately)
        if "GRADE" in title_line:
            continue

        if h and r:
            slides.append({
                "type": "table",
                "title": title_line or "研究結果",
                "headers": h,
                "rows": r[:6],
                "section": "APPRAISE",
            })

    # Article result screenshots (forest plot, KM curve, etc.)
    result_screenshots = {
        "forest-plot": "Forest Plot",
        "kaplan-meier": "Kaplan-Meier 存活曲線",
        "roc-curve": "ROC Curve",
        "article-results": "研究結果圖表",
    }
    for pattern, title in result_screenshots.items():
        imgs = find_screenshot_files(project, f"{pattern}-*.png")
        for img in imgs[:2]:
            slides.append({
                "type": "image",
                "title": title,
                "image_path": img,
                "caption": title,
                "section": "APPRAISE",
            })


def build_apply_slides(project: Path) -> list[dict]:
    """Build APPLY section slides (5-8 slides)."""
    apply_dir = project / "04_apply"
    slides = []

    slides.append({"type": "section", "title": "APPLY", "subtitle": "應用"})

    # 1. OCEBM Evidence Level
    evidence = read_md(apply_dir / "evidence_level.md")
    if evidence:
        # Extract level info
        level_bullets = []
        for line in evidence.split("\n"):
            s = line.strip()
            if s.startswith("**Level") or s.startswith("**level"):
                level_bullets.insert(0, s.strip("*").strip())
            elif s.startswith("- ") or s.startswith("* "):
                level_bullets.append(s[2:].strip())
        if level_bullets:
            slides.append({
                "type": "content",
                "title": "OCEBM 證據等級",
                "bullets": level_bullets[:5],
                "section": "APPLY",
            })

        # OCEBM level table
        h, r = extract_table_data(evidence)
        if h and r:
            # Find the OCEBM hierarchy table (has Level column)
            all_tables = []
            for section in evidence.split("## "):
                th, tr = extract_table_data(section)
                if th and tr:
                    all_tables.append((th, tr))
            for th, tr in all_tables:
                if any("Level" in str(c) or "level" in str(c) for c in th):
                    slides.append({
                        "type": "table",
                        "title": "OCEBM 2011 證據層級",
                        "headers": th,
                        "rows": tr,
                        "section": "APPLY",
                    })
                    break

    # 2. Local considerations
    local = read_md(apply_dir / "local_considerations.md")
    if local:
        bullets = extract_bullets(local)
        if bullets:
            slides.append({
                "type": "content",
                "title": "台灣在地化考量",
                "bullets": bullets[:6],
                "section": "APPLY",
            })

    # 3. Cost-benefit (optional)
    cost = read_md(apply_dir / "cost_benefit.md")
    if cost:
        h, r = extract_table_data(cost)
        if h and r:
            slides.append({
                "type": "table",
                "title": "成本效益分析",
                "headers": h,
                "rows": r[:5],
                "section": "APPLY",
            })
        else:
            bullets = extract_bullets(cost)
            if bullets:
                slides.append({
                    "type": "content",
                    "title": "成本效益分析",
                    "bullets": bullets[:5],
                    "section": "APPLY",
                })

    # 4. SDM (optional)
    sdm = read_md(apply_dir / "sdm.md")
    if sdm:
        bullets = extract_bullets(sdm)
        if bullets:
            slides.append({
                "type": "content",
                "title": "醫病共享決策 (SDM)",
                "bullets": bullets[:5],
                "section": "APPLY",
            })

    # 5. Clinical reply
    reply = read_md(apply_dir / "clinical_reply.md")
    if reply:
        bullets = []
        for line in reply.split("\n"):
            s = line.strip()
            if s.startswith(">"):
                text = s.lstrip(">").strip()
                if text:
                    bullets.append(text)
            elif s.startswith("- ") or s.startswith("* "):
                bullets.append(s[2:].strip())
        if not bullets:
            bullets = extract_paragraphs(reply)
        if bullets:
            if len(bullets) > 5:
                mid = (len(bullets) + 1) // 2
                slides.append({
                    "type": "content",
                    "title": "臨床回覆 (1/2)",
                    "bullets": bullets[:mid],
                    "section": "APPLY",
                })
                slides.append({
                    "type": "content",
                    "title": "臨床回覆 (2/2)",
                    "bullets": bullets[mid:mid+5],
                    "section": "APPLY",
                })
            else:
                slides.append({
                    "type": "content",
                    "title": "臨床回覆",
                    "bullets": bullets[:5],
                    "section": "APPLY",
                })

    return slides


def build_audit_slides(project: Path) -> list[dict]:
    """Build AUDIT section slides (3-5 slides) with full 5-dimension checklist."""
    audit_dir = project / "05_audit"
    slides = []

    slides.append({"type": "section", "title": "AUDIT", "subtitle": "評估"})

    audit = read_md(audit_dir / "self_assessment.md")
    if audit:
        # Parse by ## sections (5 dimensions)
        dimensions = re.split(r'^## ', audit, flags=re.MULTILINE)

        for dim in dimensions:
            if not dim.strip():
                continue
            lines = dim.strip().split("\n")
            title = lines[0].strip().rstrip("#").strip()

            if not title or title.startswith("#"):
                continue

            # Extract checkboxes
            checkboxes = extract_checkboxes(dim)
            if checkboxes:
                bullets = []
                for cb in checkboxes:
                    mark = "✓" if cb["checked"] else "✗"
                    bullets.append(f"[{mark}] {cb['text']}")
                slides.append({
                    "type": "content",
                    "title": f"自我評估：{title}",
                    "bullets": bullets[:6],
                    "section": "AUDIT",
                })
            else:
                # Extract bullets or paragraphs
                bs = extract_bullets(dim)
                if bs:
                    slides.append({
                        "type": "content",
                        "title": f"自我評估：{title}",
                        "bullets": bs[:5],
                        "section": "AUDIT",
                    })

        # Time spent (usually at end)
        for line in audit.split("\n"):
            if "花費時間" in line or "時間" in line:
                time_text = line.strip().lstrip("- ").strip()
                if time_text and "花費" in time_text:
                    # Add to last slide if exists, or create new one
                    if slides and slides[-1].get("section") == "AUDIT":
                        slides[-1].get("bullets", []).append(time_text)
                    break
    else:
        slides.append({
            "type": "content",
            "title": "自我評估",
            "bullets": ["（尚未完成自我評估）"],
            "section": "AUDIT",
        })

    return slides


def build_references_slide(project: Path) -> list[dict]:
    """Build references slide from appraisal and introduction."""
    slides = []
    refs = []

    # Extract from introduction
    intro = read_md(project / "01_ask" / "introduction.md")
    if intro and "參考文獻" in intro:
        ref_section = intro[intro.index("參考文獻"):]
        for line in ref_section.split("\n"):
            s = line.strip()
            if re.match(r'^\d+\.', s):
                refs.append(s)

    # Extract from selected articles (PMID)
    selected = read_md(project / "02_acquire" / "selected_articles.md")
    if selected:
        for line in selected.split("\n"):
            if "PMID" in line:
                s = line.strip().lstrip("| ").strip()
                if s:
                    refs.append(s)

    if refs:
        # Split across slides if many refs
        for i in range(0, len(refs), 5):
            chunk = refs[i:i+5]
            suffix = f" ({i//5 + 1})" if len(refs) > 5 else ""
            slides.append({
                "type": "content",
                "title": f"References{suffix}",
                "bullets": chunk,
                "section": "AUDIT",
            })
    else:
        slides.append({
            "type": "content",
            "title": "References",
            "bullets": ["（由評讀文獻自動產生）"],
            "section": "AUDIT",
        })

    return slides


# ── Main builder ──

def build_slides(project: Path, style: str, author: str) -> dict:
    """Build slides.json from project files. Target: 50-60 slides."""
    ask_dir = project / "01_ask"

    pico_content = read_md(ask_dir / "pico.yaml")
    topic = extract_yaml_field(pico_content, "topic") or "EBM Report"
    department = extract_yaml_field(pico_content, "  name") or ""

    slides = []

    # TOC / 5A overview
    slides.append({
        "type": "toc",
        "title": "目錄 / 5A 流程",
        "items": [
            "ASK — 提出臨床問題、PICO 分析",
            "ACQUIRE — 6S 搜尋、PRISMA 篩選",
            "APPRAISE — 嚴格評讀、研究結果",
            "APPLY — 證據等級、在地化、臨床回覆",
            "AUDIT — 五面向自我評估",
        ],
    })

    # Build each section
    slides.extend(build_ask_slides(project, pico_content))
    slides.extend(build_acquire_slides(project))
    slides.extend(build_appraise_slides(project))
    slides.extend(build_apply_slides(project))
    slides.extend(build_audit_slides(project))
    slides.extend(build_references_slide(project))

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
    parser.add_argument("--output", help="輸出路徑（預設寫入專案 06_slides/）")

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
    print(f"  投影片數：{len(data['slides'])} 張（+ 封面 = {len(data['slides']) + 1} 張）")
    print(f"  風格：{args.style}")
    print()
    print("下一步：")
    print(f"  python3 scripts/generate_pptx.py {output_path} {project / '06_slides' / 'ebm-report.pptx'} --project {project}")


if __name__ == "__main__":
    main()
