# EBM Report Pipeline

PGY 住院醫師的 EBM (Evidence-Based Medicine) 報告互動式產生工具。從選科別到產出簡報的完整 5A 流程。

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

## 參考模板

| 模板 | 路徑 | 用途 |
|------|------|------|
| PICO YAML | `data/references/pico-template.yaml` | PICO 結構化模板 |
| CASP RCT | `data/references/casp-rct-template.csv` | RCT 評讀 11 題 |
| CASP SR | `data/references/casp-sr-template.csv` | Systematic Review 評讀 10 題 |
| CASP Cohort | `data/references/casp-cohort-template.csv` | Cohort 評讀 12 題 |
| CASP Case-Control | `data/references/casp-case-control-template.csv` | Case-Control 評讀 11 題 |
| CASP Diagnostic | `data/references/casp-diagnostic-template.csv` | Diagnostic 評讀 11 題 |

## 範例專案

`projects/example-sglt2i-ckd/` — SGLT2i 在 CKD 合併糖尿病的完整 EBM 報告範例，展示每個步驟的結構化產出。

## 外部工具（MCP / API）

本專案的技能指令支援以下外部工具，如不可用會自動 fallback 到 WebSearch / E-utilities API：

- **PubMed** — 文獻搜尋、metadata 取得、全文取得
- **Playwright** — Cochrane Library 網站搜尋
- **Clinical Trials** — ClinicalTrials.gov 進行中試驗搜尋
- **Canva** — 簡報產生
- **ICD-10** — 輔助搜尋詞彙查詢

各工具的 fallback 機制詳見 `skills/brainstorm.md` 和 `skills/lit-search.md`。

## 語言規則

- 使用者互動：繁體中文
- PubMed / API 搜尋：English
- MeSH terms：English
- 簡報內容：中文標題 + 英文引用
