#!/usr/bin/env python3
"""
EBM 報告截圖工具 — 提供 Playwright MCP 截圖的標準化流程指引。

本模組不直接執行截圖（截圖由 Playwright MCP 在 AI 對話中完成），
而是提供：
1. 截圖命名規範與路徑管理
2. 截圖清單追蹤（screenshots.json）
3. 截圖類型定義
4. 輔助腳本：列出已截圖、檢查缺漏

用法：
    # 列出專案的所有截圖
    python3 scripts/screenshot.py --project <name> --list

    # 檢查截圖完整性
    python3 scripts/screenshot.py --project <name> --check

    # 初始化 assets 目錄
    python3 scripts/screenshot.py --project <name> --init
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# ── 截圖類型定義 ──
# 每個類型對應 EBM 流程中需要截圖的場景
SCREENSHOT_TYPES = {
    # ── ACQUIRE 階段 ──
    "pubmed_search": {
        "stage": "02_acquire",
        "description": "PubMed 搜尋結果頁面",
        "required": True,
        "naming": "pubmed-search-{timestamp}.png",
        "casp_questions": [],
    },
    "pubmed_filters": {
        "stage": "02_acquire",
        "description": "PubMed 篩選器設定",
        "required": False,
        "naming": "pubmed-filters-{timestamp}.png",
        "casp_questions": [],
    },
    "cochrane_search": {
        "stage": "02_acquire",
        "description": "Cochrane Library 搜尋結果",
        "required": False,
        "naming": "cochrane-search-{timestamp}.png",
        "casp_questions": [],
    },
    "prisma_flow": {
        "stage": "02_acquire",
        "description": "PRISMA 篩選流程圖",
        "required": False,
        "naming": "prisma-flow-{timestamp}.png",
        "casp_questions": [],
    },
    "article_abstract": {
        "stage": "02_acquire",
        "description": "選定文獻的摘要頁面",
        "required": True,
        "naming": "article-abstract-{n}-{timestamp}.png",
        "casp_questions": [],
    },
    # ── APPRAISE 階段 — 對應 CASP 題目 ──
    "article_objective": {
        "stage": "03_appraise",
        "description": "研究目的段落（Abstract Objective / Introduction 末段）",
        "required": True,
        "naming": "article-objective-{n}-{timestamp}.png",
        "casp_questions": ["Q1"],
        "location_hint": "Abstract → Objective，或 Introduction 最後一段",
    },
    "article_methods": {
        "stage": "03_appraise",
        "description": "Methods 章節（隨機化、盲化、程序）",
        "required": True,
        "naming": "article-methods-{n}-{timestamp}.png",
        "casp_questions": ["Q2", "Q4", "Q6", "Q9"],
        "location_hint": "Methods → Randomization / Blinding / Procedures / Eligibility criteria",
    },
    "article_flowchart": {
        "stage": "03_appraise",
        "description": "CONSORT 流程圖 / 參與者流程",
        "required": True,
        "naming": "article-flowchart-{n}-{timestamp}.png",
        "casp_questions": ["Q3"],
        "location_hint": "Results → Figure 1 (participant flow / CONSORT diagram)",
    },
    "table_baseline": {
        "stage": "03_appraise",
        "description": "Table 1 — 基線特徵比較",
        "required": True,
        "naming": "table-baseline-{n}-{timestamp}.png",
        "casp_questions": ["Q5"],
        "location_hint": "Results → Table 1 (Baseline characteristics)",
    },
    "article_results": {
        "stage": "03_appraise",
        "description": "Results 章節（Primary outcome 數據）",
        "required": True,
        "naming": "article-results-{n}-{timestamp}.png",
        "casp_questions": ["Q7", "Q8"],
        "location_hint": "Results → Primary outcome 段落，含 HR/OR/RR + 95% CI + p-value",
    },
    "table_outcomes": {
        "stage": "03_appraise",
        "description": "結果數據表格（Primary/Secondary outcomes）",
        "required": False,
        "naming": "table-outcomes-{n}-{timestamp}.png",
        "casp_questions": ["Q10"],
        "location_hint": "Results → 結果彙整表格（所有 outcomes）",
    },
    "article_safety": {
        "stage": "03_appraise",
        "description": "安全性 / 副作用段落",
        "required": False,
        "naming": "article-safety-{n}-{timestamp}.png",
        "casp_questions": ["Q11"],
        "location_hint": "Results → Adverse events / Safety",
    },
    "forest_plot": {
        "stage": "03_appraise",
        "description": "Forest Plot（Meta-Analysis / SR）",
        "required": False,
        "naming": "forest-plot-{n}-{timestamp}.png",
        "casp_questions": ["Q7"],
        "location_hint": "Results → Forest Plot（主要結局的 meta-analysis 圖）",
    },
    "kaplan_meier": {
        "stage": "03_appraise",
        "description": "Kaplan-Meier 存活曲線",
        "required": False,
        "naming": "kaplan-meier-{n}-{timestamp}.png",
        "casp_questions": ["Q7"],
        "location_hint": "Results → Kaplan-Meier curve（主要結局的存活曲線）",
    },
    "roc_curve": {
        "stage": "03_appraise",
        "description": "ROC 曲線（診斷型）",
        "required": False,
        "naming": "roc-curve-{n}-{timestamp}.png",
        "casp_questions": ["Q7"],
        "location_hint": "Results → ROC curve + AUC 值",
    },
    "funnel_plot": {
        "stage": "03_appraise",
        "description": "Funnel Plot（發表偏差，SR/MA）",
        "required": False,
        "naming": "funnel-plot-{n}-{timestamp}.png",
        "casp_questions": [],
        "location_hint": "Results → Funnel plot（評估發表偏差）",
    },
    "sr_prisma": {
        "stage": "03_appraise",
        "description": "SR 文獻的 PRISMA 流程圖",
        "required": False,
        "naming": "sr-prisma-{n}-{timestamp}.png",
        "casp_questions": [],
        "location_hint": "Methods/Results → PRISMA flow diagram（SR 自身的篩選流程）",
    },
    "rob_summary": {
        "stage": "03_appraise",
        "description": "Risk of Bias 整體摘要圖",
        "required": False,
        "naming": "rob-summary-{n}-{timestamp}.png",
        "casp_questions": [],
        "location_hint": "Results → Risk of bias summary / traffic light plot",
    },
    "diagnostic_table": {
        "stage": "03_appraise",
        "description": "診斷 2x2 表格（TP/FP/TN/FN）",
        "required": False,
        "naming": "diagnostic-table-{n}-{timestamp}.png",
        "casp_questions": ["Q7"],
        "location_hint": "Results → 2x2 contingency table / sensitivity-specificity data",
    },
    "adjusted_analysis": {
        "stage": "03_appraise",
        "description": "多變量校正分析表格",
        "required": False,
        "naming": "adjusted-analysis-{n}-{timestamp}.png",
        "casp_questions": [],
        "location_hint": "Results → Multivariable / adjusted analysis table",
    },
    "coi_disclosure": {
        "stage": "03_appraise",
        "description": "利益衝突揭露聲明",
        "required": True,
        "naming": "coi-disclosure-{n}-{timestamp}.png",
        "casp_questions": [],
        "location_hint": "文末 → Conflict of Interest / Disclosures 聲明",
    },
    "funding_source": {
        "stage": "03_appraise",
        "description": "經費來源聲明",
        "required": True,
        "naming": "funding-source-{n}-{timestamp}.png",
        "casp_questions": [],
        "location_hint": "文末 → Funding / Acknowledgments",
    },
}

# 各階段必要截圖
REQUIRED_BY_STAGE = {
    "02_acquire": ["pubmed_search", "article_abstract"],
    "03_appraise": [
        "article_objective",
        "article_methods",
        "article_flowchart",
        "table_baseline",
        "article_results",
        "coi_disclosure",
        "funding_source",
    ],
}


def get_assets_dir(project_path: Path) -> Path:
    """Get the assets directory for a project."""
    return project_path / "assets" / "screenshots"


def init_assets(project_path: Path) -> Path:
    """Initialize assets/screenshots directory and screenshots.json."""
    assets_dir = get_assets_dir(project_path)
    assets_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = project_path / "assets" / "screenshots.json"
    if not manifest_path.exists():
        manifest = {
            "project": project_path.name,
            "created": datetime.now().isoformat(),
            "screenshots": [],
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return assets_dir


def generate_filename(screenshot_type: str, article_num: int = 1) -> str:
    """Generate a standardized filename for a screenshot."""
    type_info = SCREENSHOT_TYPES.get(screenshot_type)
    if not type_info:
        return f"screenshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = type_info["naming"].format(timestamp=timestamp, n=article_num)
    return name


def add_screenshot_record(
    project_path: Path,
    screenshot_type: str,
    filename: str,
    url: str = "",
    article_pmid: str = "",
    description: str = "",
) -> None:
    """Add a screenshot record to the manifest."""
    manifest_path = project_path / "assets" / "screenshots.json"
    if not manifest_path.exists():
        init_assets(project_path)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    type_info = SCREENSHOT_TYPES.get(screenshot_type, {})

    record = {
        "type": screenshot_type,
        "stage": type_info.get("stage", ""),
        "filename": filename,
        "url": url,
        "article_pmid": article_pmid,
        "description": description or type_info.get("description", ""),
        "timestamp": datetime.now().isoformat(),
    }
    manifest["screenshots"].append(record)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_screenshots(project_path: Path) -> list[dict]:
    """List all screenshots for a project."""
    manifest_path = project_path / "assets" / "screenshots.json"
    if not manifest_path.exists():
        return []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest.get("screenshots", [])


def generate_screenshot_guide(
    study_type: str = "RCT",
    article_num: int = 1,
    article_title: str = "",
    pmid: str = "",
    pmc_id: str = "",
) -> str:
    """Generate a screenshot guide for when Playwright is unavailable.

    Returns a Markdown string telling the reporter exactly where to
    take each screenshot in the article.
    """
    lines = [
        "# 截圖指引 (Screenshot Guide)",
        "",
        f"**文獻 #{article_num}**" + (f": {article_title}" if article_title else ""),
    ]
    if pmid:
        lines.append(f"- PubMed: https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
    if pmc_id:
        lines.append(f"- PMC 全文: https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/")
    lines.append("")
    lines.append("請依照以下指引，到全文中截取對應段落，作為簡報佐證素材。")
    lines.append("")

    # Determine which types are relevant for this study type
    study_type_upper = study_type.upper()
    extra_types = set()
    if study_type_upper in ("SR", "MA", "META-ANALYSIS", "SYSTEMATIC REVIEW"):
        extra_types = {"forest_plot", "funnel_plot", "sr_prisma", "rob_summary"}
    elif study_type_upper in ("RCT", "RANDOMIZED CONTROLLED TRIAL"):
        extra_types = {"kaplan_meier"}
    elif study_type_upper in ("DIAGNOSTIC", "DIAGNOSTIC STUDY"):
        extra_types = {"roc_curve", "diagnostic_table"}
    elif study_type_upper in ("COHORT", "CASE-CONTROL"):
        extra_types = {"adjusted_analysis"}

    # Required screenshots
    lines.append("## 必要截圖")
    lines.append("")
    idx = 1
    for type_id, info in SCREENSHOT_TYPES.items():
        if info["stage"] != "03_appraise":
            continue
        if not info.get("required") and type_id not in extra_types:
            continue
        hint = info.get("location_hint", "")
        casp = ", ".join(info.get("casp_questions", []))
        casp_str = f"（對應 {casp}）" if casp else ""
        suggested_name = info["naming"].format(n=article_num, timestamp="YYYYMMDD-HHMMSS")
        lines.append(f"### {idx}. {info['description']}{casp_str}")
        lines.append("")
        if hint:
            lines.append(f"**位置：** {hint}")
            lines.append("")
        lines.append(f"**建議檔名：** `{suggested_name}`")
        lines.append("")
        idx += 1

    # Optional screenshots
    optional = []
    for type_id, info in SCREENSHOT_TYPES.items():
        if info["stage"] != "03_appraise":
            continue
        if info.get("required") or type_id in extra_types:
            continue
        optional.append((type_id, info))

    if optional:
        lines.append("## 選擇性截圖（如文獻中有相關內容）")
        lines.append("")
        for type_id, info in optional:
            hint = info.get("location_hint", "")
            lines.append(f"- **{info['description']}**：{hint}")
        lines.append("")

    return "\n".join(lines)


def check_completeness(project_path: Path) -> dict[str, list[str]]:
    """Check which required screenshots are missing.

    Returns {"missing": [...], "present": [...]}.
    """
    screenshots = list_screenshots(project_path)
    present_types = {s["type"] for s in screenshots}

    missing = []
    present = []
    for stage, required_types in REQUIRED_BY_STAGE.items():
        stage_dir = project_path / stage
        if not stage_dir.exists():
            continue
        for req_type in required_types:
            if req_type in present_types:
                present.append(req_type)
            else:
                missing.append(req_type)

    return {"missing": missing, "present": present}


def main():
    parser = argparse.ArgumentParser(
        description="EBM 報告截圖管理工具",
        epilog=(
            "範例：\n"
            "  python3 scripts/screenshot.py --project sglt2i-ckd --init\n"
            "  python3 scripts/screenshot.py --project sglt2i-ckd --list\n"
            "  python3 scripts/screenshot.py --project sglt2i-ckd --check\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--project", default="", help="專案名稱")
    parser.add_argument("--init", action="store_true", help="初始化截圖目錄")
    parser.add_argument("--list", action="store_true", help="列出已有截圖")
    parser.add_argument("--check", action="store_true", help="檢查截圖完整性")
    parser.add_argument("--types", action="store_true", help="列出所有截圖類型")
    parser.add_argument("--guide", default="", metavar="STUDY_TYPE",
                        help="產生截圖指引（RCT/SR/MA/Diagnostic/Cohort/Case-Control）")

    args = parser.parse_args()
    base_dir = Path(__file__).resolve().parent.parent
    project_path = base_dir / "projects" / args.project

    if args.types:
        print("═══ 截圖類型一覽 ═══\n")
        for type_id, info in SCREENSHOT_TYPES.items():
            req = "★ 必要" if info["required"] else "  選擇性"
            casp = ", ".join(info.get("casp_questions", []))
            casp_str = f"  ← {casp}" if casp else ""
            print(f"  {req}  {type_id:<25s} {info['description']}{casp_str}")
        return

    if not args.project:
        if not args.types and not args.guide:
            parser.print_help()
            sys.exit(1)

    if args.project and not project_path.exists():
        print(f"錯誤：找不到專案 '{args.project}'。", file=sys.stderr)
        sys.exit(1)

    if args.init:
        assets_dir = init_assets(project_path)
        print(f"截圖目錄已建立：{assets_dir}")
        print(f"清單檔案：{project_path / 'assets' / 'screenshots.json'}")
        return

    if args.list:
        screenshots = list_screenshots(project_path)
        if not screenshots:
            print("目前沒有截圖記錄。")
            return
        print(f"═══ 截圖記錄（共 {len(screenshots)} 張）═══\n")
        for s in screenshots:
            pmid = f" [PMID:{s['article_pmid']}]" if s.get("article_pmid") else ""
            print(f"  [{s['stage']}] {s['filename']}{pmid}")
            print(f"           {s['description']}")
        return

    if args.check:
        result = check_completeness(project_path)
        if result["missing"]:
            print("⚠ 缺少以下必要截圖：\n")
            for m in result["missing"]:
                info = SCREENSHOT_TYPES[m]
                print(f"  ✗ {m:<25s} {info['description']}")
        if result["present"]:
            print("\n✓ 已完成的必要截圖：\n")
            for p in result["present"]:
                info = SCREENSHOT_TYPES[p]
                print(f"  ✓ {p:<25s} {info['description']}")
        if not result["missing"] and not result["present"]:
            print("尚未開始截圖（或相關階段目錄不存在）。")
        return

    if args.guide:
        guide = generate_screenshot_guide(study_type=args.guide)
        if args.project:
            guide_path = project_path / "03_appraise" / "screenshot_guide.md"
            guide_path.parent.mkdir(parents=True, exist_ok=True)
            guide_path.write_text(guide, encoding="utf-8")
            print(f"截圖指引已產生：{guide_path}")
        else:
            print(guide)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
