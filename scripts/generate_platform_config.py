#!/usr/bin/env python3
"""
跨平台 AI 工具設定檔產生器。

從共用內容模板產生各平台的專案設定檔：
  - Claude Code  → CLAUDE.md
  - Gemini CLI   → GEMINI.md
  - Cursor       → .cursorrules
  - GitHub Copilot → .github/copilot-instructions.md
  - OpenAI Codex CLI → AGENTS.md

用法：
    python3 scripts/generate_platform_config.py                    # 產生全部平台
    python3 scripts/generate_platform_config.py --platform gemini  # 只產生 Gemini
    python3 scripts/generate_platform_config.py --platform all     # 產生全部平台
"""

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ── 共用內容區塊 ──

HEADER = """\
# EBM Report Pipeline

PGY 住院醫師的 EBM (Evidence-Based Medicine) 報告互動式產生工具。從選科別到產出簡報的完整 5A 流程。
"""

SKILLS_TABLE = """\
## 技能指令

| 指令 | 檔案 | 說明 |
|------|------|------|
| `ebm` | `skills/ebm.md` | 主進入點 — 完整 5A 框架 EBM 報告流程 |
| `brainstorm` | `skills/brainstorm.md` | 搜尋 PubMed 近期文獻，激發選題靈感 |
| `pico` | `skills/pico.md` | PICO 框架分析 |
| `classify` | `skills/classify.md` | 臨床問題分類（診斷/預後/治療/預防/病因傷害） |
| `lit-search` | `skills/lit-search.md` | 6S 階層文獻搜尋（PubMed + Cochrane + Embase） |
| `appraise` | `skills/appraise.md` | 嚴格評讀（CASP / RoB 2 / AMSTAR 2） |
| `ebm-slides` | `skills/ebm-slides.md` | 產生 EBM 簡報（Canva） |
| `save-progress` | `skills/save-progress.md` | 儲存目前 EBM 報告進度 |
| `load-progress` | `skills/load-progress.md` | 載入已儲存的進度並繼續 |
"""

QUICK_START_GENERIC = """\
## 使用方式

### 手動建立專案

```bash
python3 scripts/init_project.py --name my-topic --department 腎臟內科
```

### 執行技能

請載入 `skills/` 目錄下對應的 markdown 檔案作為上下文，然後依照指示操作：
- `skills/ebm.md` — 完整 5A 流程
- `skills/brainstorm.md` — 只做選題
- `skills/pico.md` — 只做 PICO 分析
- `skills/lit-search.md` — 只做文獻搜尋
"""

PROJECT_STRUCTURE = """\
## 專案結構

每個 EBM 報告都是一個獨立專案，位於 `projects/<name>/`：

```
projects/<name>/
├── TOPIC.txt                  # 主題描述
├── README.md                  # 專案摘要
├── 01_ask/                    # ASK — PICO、臨床情境、背景、分類
│   ├── pico.yaml              # PICO 結構化資料（YAML）
│   ├── clinical_scenario.md   # 臨床情境
│   ├── introduction.md        # 背景資訊
│   └── classification.md      # 問題分類與證據層級
├── 02_acquire/                # ACQUIRE — 搜尋策略、PRISMA、選文
│   ├── search_strategy.md     # 完整搜尋策略
│   ├── prisma_flow.md         # PRISMA 篩選流程圖
│   ├── candidates.csv         # 候選文獻列表（CSV）
│   └── selected_articles.md   # 選定文獻與理由
├── 03_appraise/               # APPRAISE — 評讀結果
│   ├── tool_selection.md      # 評讀工具選擇理由
│   ├── appraisal.csv          # 逐題評讀結果（CSV）
│   ├── coi_check.md           # 利益衝突檢核
│   ├── results_summary.md     # 研究結果摘要
│   └── grade.md               # GRADE 評定（選擇性）
├── 04_apply/                  # APPLY — 臨床應用
│   ├── evidence_level.md      # OCEBM 證據等級
│   ├── local_considerations.md # 台灣在地化考量
│   └── clinical_reply.md      # 去學術化臨床回覆
├── 05_audit/                  # AUDIT — 自我評估
│   └── self_assessment.md     # 五面向自我評估
└── 06_slides/                 # 簡報輸出
    ├── slides.json            # 簡報資料（JSON）
    └── ebm-report.pptx        # PowerPoint 檔案
```
"""

SCRIPTS_TABLE = """\
## 實體腳本

| 腳本 | 用途 |
|------|------|
| `scripts/init_project.py` | 初始化專案目錄結構 |
| `scripts/validate_step.py` | 驗證各步驟產出是否完整（檔案層級） |
| `scripts/quality_gate.py` | 5A 品質門檻驗證（內容層級，檢查 PICO 欄位、CSV 品質等） |
| `scripts/build_search_query.py` | 從 PICO YAML 自動建構 PubMed 搜尋式 |
| `scripts/generate_prisma_flow.py` | 產生 PRISMA 篩選流程圖 |
| `scripts/dedupe_results.py` | 候選文獻去重（依 PMID → DOI → 標題相似度） |
| `scripts/export_appraisal.py` | 將評讀 JSON 匯出為結構化 CSV |
| `scripts/build_slide_outline.py` | 從專案檔案自動組裝 slides.json |
| `scripts/generate_pptx.py` | python-pptx fallback 簡報產生器 |
| `scripts/status.py` | 專案進度儀表板 |
"""

QUALITY_GATES = """\
## 品質門檻

每個 5A 階段完成時會自動驗證：

| 階段 | 驗證內容 |
|------|---------|
| ASK | pico.yaml 中 P/I/C/O MeSH 不為空 |
| ACQUIRE | 至少選定 1 篇文獻，candidates.csv 不為空 |
| APPRAISE | appraisal.csv 每題有 answer；Can't tell > 2 題則警告 |
| APPLY | evidence_level.md 和 clinical_reply.md 存在 |
| AUDIT | self_assessment.md 存在 |

可隨時用 `python3 scripts/validate_step.py --project <name>` 驗證全部步驟。
"""

TEMPLATES = """\
## 參考模板

| 模板 | 路徑 | 用途 |
|------|------|------|
| PICO YAML | `data/references/pico-template.yaml` | PICO 結構化模板 |
| CASP RCT | `data/references/casp-rct-template.csv` | RCT 評讀 11 題 |
| CASP SR | `data/references/casp-sr-template.csv` | Systematic Review 評讀 10 題 |
| CASP Cohort | `data/references/casp-cohort-template.csv` | Cohort 評讀 12 題 |
| CASP Case-Control | `data/references/casp-case-control-template.csv` | Case-Control 評讀 11 題 |
| CASP Diagnostic | `data/references/casp-diagnostic-template.csv` | Diagnostic 評讀 11 題 |
"""

EXAMPLE_PROJECT = """\
## 範例專案

`projects/example-sglt2i-ckd/` — SGLT2i 在 CKD 合併糖尿病的完整 EBM 報告範例，展示每個步驟的結構化產出。
"""

EXTERNAL_TOOLS = """\
## 外部工具（MCP / API）

本專案的技能指令支援以下外部工具，如不可用會自動 fallback 到 WebSearch / E-utilities API：

- **PubMed** — 文獻搜尋、metadata 取得、全文取得
- **Playwright** — Cochrane Library 網站搜尋
- **Clinical Trials** — ClinicalTrials.gov 進行中試驗搜尋
- **Canva** — 簡報產生
- **ICD-10** — 輔助搜尋詞彙查詢

各工具的 fallback 機制詳見 `skills/brainstorm.md` 和 `skills/lit-search.md`。
"""

LANGUAGE_RULES = """\
## 語言規則

- 使用者互動：繁體中文
- PubMed / API 搜尋：English
- MeSH terms：English
- 簡報內容：中文標題 + 英文引用
"""

# ── 平台特定區塊 ──


def _claude_skills_section():
    """Claude Code 的 skills table 使用 /command trigger 格式。"""
    return """\
## Skills

| Command | File | 說明 |
|---------|------|------|
| `/ebm` | `skills/ebm.md` | 主進入點 — 完整 5A 框架 EBM 報告流程 |
| `/brainstorm` | `skills/brainstorm.md` | 搜尋 PubMed 近期文獻，激發選題靈感 |
| `/pico` | `skills/pico.md` | PICO 框架分析 |
| `/classify` | `skills/classify.md` | 臨床問題分類（診斷/預後/治療/預防/病因傷害） |
| `/lit-search` | `skills/lit-search.md` | 6S 階層文獻搜尋（PubMed + Cochrane + Embase） |
| `/appraise` | `skills/appraise.md` | 嚴格評讀（CASP / RoB 2 / AMSTAR 2） |
| `/ebm-slides` | `skills/ebm-slides.md` | 產生 EBM 簡報（Canva） |
| `/save-progress` | `skills/save-progress.md` | 儲存目前 EBM 報告進度 |
| `/load-progress` | `skills/load-progress.md` | 載入已儲存的進度並繼續 |
"""


def _claude_quick_start():
    return """\
## 使用方式

### 快速開始

```bash
cd ebm-report-pipeline
claude
> /ebm
```

系統會自動建立專案目錄、引導完成 5A 流程、每個步驟產出結構化檔案。

### 手動建立專案

```bash
python3 scripts/init_project.py --name my-topic --department 腎臟內科
```

### 單獨使用子技能

```
> /brainstorm    # 只做選題
> /pico          # 只做 PICO 分析
> /lit-search    # 只做文獻搜尋
```
"""


def _claude_mcp_section():
    return """\
## MCP 工具

本專案使用以下 MCP 工具：
- **PubMed MCP** — search_articles, get_article_metadata, find_related_articles, get_full_text_article
- **Playwright MCP** — Cochrane Library 網站搜尋
- **Clinical Trials MCP** — ClinicalTrials.gov 進行中試驗搜尋
- **Canva MCP** — 簡報產生
- **ICD-10 MCP** — 輔助搜尋詞彙查詢
"""


def _gemini_quick_start():
    return """\
## 使用方式

### 快速開始

```bash
cd ebm-report-pipeline
gemini
```

然後請 Gemini 讀取 `skills/ebm.md` 來啟動完整 5A 流程：

```
> 請讀取 skills/ebm.md 並依照指示引導我完成 EBM 報告
```

### 手動建立專案

```bash
python3 scripts/init_project.py --name my-topic --department 腎臟內科
```

### 單獨使用技能

請直接告訴 Gemini 讀取對應的 skill 檔案：

```
> 請讀取 skills/brainstorm.md 並幫我選題
> 請讀取 skills/pico.md 並幫我做 PICO 分析
> 請讀取 skills/lit-search.md 並幫我搜尋文獻
```

### 使用 /memory 管理上下文

Gemini CLI 會自動載入本檔案。可用 `/memory show` 查看目前載入的上下文。
"""


def _cursor_quick_start():
    return """\
## 使用方式

### 快速開始

1. 用 Cursor 開啟本專案目錄
2. 本檔案 (`.cursorrules`) 會自動載入為專案規則
3. 在 Chat 中使用 `@` 引用 skill 檔案來執行對應流程

### 執行技能

在 Cursor Chat 中：

```
@skills/ebm.md 請引導我完成完整 EBM 報告流程
@skills/brainstorm.md 我是腎臟內科，請幫我選題
@skills/pico.md 請幫我做 PICO 分析
@skills/lit-search.md 請幫我搜尋文獻
```

### 手動建立專案

在 Terminal 中：
```bash
python3 scripts/init_project.py --name my-topic --department 腎臟內科
```

### MCP 工具

Cursor 支援 MCP。如已設定 PubMed MCP server，技能中的文獻搜尋會自動使用。
未設定時會自動 fallback 到 WebSearch。
"""


def _copilot_quick_start():
    return """\
## 使用方式

### 快速開始

1. 在 VS Code 中開啟本專案
2. 本檔案會自動載入為 Copilot 自訂指令
3. 在 Copilot Chat 中引用 skill 檔案來執行對應流程

### 執行技能

在 Copilot Chat 中：

```
#file:skills/ebm.md 請引導我完成完整 EBM 報告流程
#file:skills/brainstorm.md 我是腎臟內科，請幫我選題
#file:skills/pico.md 請幫我做 PICO 分析
```

### 手動建立專案

```bash
python3 scripts/init_project.py --name my-topic --department 腎臟內科
```
"""


def _codex_quick_start():
    return """\
## 使用方式

### 快速開始

```bash
cd ebm-report-pipeline
codex
```

Codex CLI 會自動載入本檔案 (AGENTS.md) 作為上下文。

### 執行技能

請直接告訴 Codex 讀取對應的 skill 檔案：

```
> 請讀取 skills/ebm.md 並依照指示引導我完成 EBM 報告
> 請讀取 skills/brainstorm.md 並幫我選題
> 請讀取 skills/lit-search.md 並幫我搜尋文獻
```

### 手動建立專案

```bash
python3 scripts/init_project.py --name my-topic --department 腎臟內科
```
"""


# ── 檔案結構 ──

FILE_TREE = """\
## 完整檔案結構

```
ebm-report-pipeline/
├── CLAUDE.md                          # Claude Code 設定
├── GEMINI.md                          # Gemini CLI 設定
├── AGENTS.md                          # OpenAI Codex CLI 設定
├── .cursorrules                       # Cursor 設定
├── .github/copilot-instructions.md    # GitHub Copilot 設定
├── README.md
├── skills/                            # 技能指令（所有平台共用）
│   ├── ebm.md                         # 完整 5A 流程
│   ├── brainstorm.md                  # 選題
│   ├── pico.md                        # PICO 分析
│   ├── classify.md                    # 問題分類
│   ├── lit-search.md                  # 文獻搜尋
│   ├── appraise.md                    # 嚴格評讀
│   ├── ebm-slides.md                  # 簡報
│   ├── save-progress.md               # 儲存進度
│   └── load-progress.md               # 載入進度
├── scripts/                           # 實體腳本（所有平台共用）
│   ├── init_project.py                # 初始化專案
│   ├── validate_step.py               # 驗證步驟產出
│   ├── quality_gate.py                # 品質門檻驗證
│   ├── build_search_query.py          # 建構搜尋策略
│   ├── generate_prisma_flow.py        # PRISMA 流程圖
│   ├── dedupe_results.py              # 文獻去重
│   ├── export_appraisal.py            # 匯出評讀 CSV
│   ├── build_slide_outline.py         # 自動組裝簡報大綱
│   ├── generate_pptx.py              # PowerPoint 產生器
│   ├── generate_platform_config.py    # 跨平台設定產生器
│   └── status.py                      # 專案進度儀表板
├── data/                              # 參考資料（所有平台共用）
│   ├── departments.md                 # 科別 MeSH 對照表
│   ├── study-type-hierarchy.md        # 證據層級
│   ├── appraisal-tools.md             # 評讀工具對照表
│   ├── ebm-slide-template.md          # 簡報結構範本
│   ├── progress-schema.md             # 進度 JSON schema
│   ├── references/                    # 結構化模板
│   └── templates/                     # 簡報設計模板
├── projects/                          # 專案目錄
│   └── example-sglt2i-ckd/            # 範例專案
└── tests/                             # 測試
```
"""

# ── 平台定義 ──

PLATFORMS = {
    "claude": {
        "filename": "CLAUDE.md",
        "display_name": "Claude Code",
        "sections": [
            HEADER,
            _claude_skills_section,
            _claude_quick_start,
            PROJECT_STRUCTURE,
            SCRIPTS_TABLE,
            QUALITY_GATES,
            TEMPLATES,
            EXAMPLE_PROJECT,
            _claude_mcp_section,
            LANGUAGE_RULES,
            FILE_TREE,
        ],
    },
    "gemini": {
        "filename": "GEMINI.md",
        "display_name": "Gemini CLI",
        "sections": [
            HEADER,
            SKILLS_TABLE,
            _gemini_quick_start,
            PROJECT_STRUCTURE,
            SCRIPTS_TABLE,
            QUALITY_GATES,
            TEMPLATES,
            EXAMPLE_PROJECT,
            EXTERNAL_TOOLS,
            LANGUAGE_RULES,
            FILE_TREE,
        ],
    },
    "cursor": {
        "filename": ".cursorrules",
        "display_name": "Cursor",
        "sections": [
            HEADER,
            SKILLS_TABLE,
            _cursor_quick_start,
            PROJECT_STRUCTURE,
            SCRIPTS_TABLE,
            QUALITY_GATES,
            TEMPLATES,
            EXAMPLE_PROJECT,
            EXTERNAL_TOOLS,
            LANGUAGE_RULES,
        ],
    },
    "copilot": {
        "filename": ".github/copilot-instructions.md",
        "display_name": "GitHub Copilot",
        "sections": [
            HEADER,
            SKILLS_TABLE,
            _copilot_quick_start,
            PROJECT_STRUCTURE,
            SCRIPTS_TABLE,
            QUALITY_GATES,
            TEMPLATES,
            EXAMPLE_PROJECT,
            EXTERNAL_TOOLS,
            LANGUAGE_RULES,
        ],
    },
    "codex": {
        "filename": "AGENTS.md",
        "display_name": "OpenAI Codex CLI",
        "sections": [
            HEADER,
            SKILLS_TABLE,
            _codex_quick_start,
            PROJECT_STRUCTURE,
            SCRIPTS_TABLE,
            QUALITY_GATES,
            TEMPLATES,
            EXAMPLE_PROJECT,
            EXTERNAL_TOOLS,
            LANGUAGE_RULES,
        ],
    },
}


def generate_config(platform: str) -> str:
    """Generate the config content for a given platform."""
    config = PLATFORMS[platform]
    parts = []
    for section in config["sections"]:
        if callable(section):
            parts.append(section())
        else:
            parts.append(section)
    return "\n".join(parts)


def write_config(platform: str, dry_run: bool = False) -> Path:
    """Write the config file for a platform. Returns the output path."""
    config = PLATFORMS[platform]
    content = generate_config(platform)
    output_path = BASE_DIR / config["filename"]
    if dry_run:
        print(f"[DRY RUN] 會產生：{output_path}")
        return output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="跨平台 AI 工具設定檔產生器",
        epilog=(
            "範例：\n"
            "  python3 scripts/generate_platform_config.py                    # 全部平台\n"
            "  python3 scripts/generate_platform_config.py --platform gemini  # 只產生 Gemini\n"
            "  python3 scripts/generate_platform_config.py --list             # 列出支援的平台\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--platform",
        choices=list(PLATFORMS.keys()) + ["all"],
        default="all",
        help="要產生的平台設定（預設：all）",
    )
    parser.add_argument("--list", action="store_true", help="列出所有支援的平台")
    parser.add_argument("--dry-run", action="store_true", help="只顯示會產生哪些檔案")

    args = parser.parse_args()

    if args.list:
        print("支援的平台：\n")
        for key, config in PLATFORMS.items():
            print(f"  {key:10s} → {config['filename']:40s} ({config['display_name']})")
        sys.exit(0)

    platforms = list(PLATFORMS.keys()) if args.platform == "all" else [args.platform]

    print("═══ 跨平台設定檔產生器 ═══\n")
    for platform in platforms:
        path = write_config(platform, dry_run=args.dry_run)
        display = PLATFORMS[platform]["display_name"]
        print(f"  ✓ {display:20s} → {path.relative_to(BASE_DIR)}")

    if not args.dry_run:
        print(f"\n已產生 {len(platforms)} 個平台設定檔。")


if __name__ == "__main__":
    main()
