# EBM Report Pipeline

PGY 住院醫師的 EBM (Evidence-Based Medicine) 報告互動式產生工具。從選科別到產出簡報的完整 5A 流程。

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
| `scripts/validate_step.py` | 驗證各步驟產出是否完整 |
| `scripts/build_search_query.py` | 從 PICO YAML 自動建構 PubMed 搜尋式 |
| `scripts/generate_prisma_flow.py` | 產生 PRISMA 篩選流程圖 |
| `scripts/export_appraisal.py` | 將評讀 JSON 匯出為結構化 CSV |
| `scripts/generate_pptx.py` | python-pptx fallback 簡報產生器 |

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
| CASP RCT CSV | `data/references/casp-rct-template.csv` | RCT 評讀模板 |
| CASP SR CSV | `data/references/casp-sr-template.csv` | SR 評讀模板 |

## 範例專案

`projects/example-sglt2i-ckd/` — SGLT2i 在 CKD 合併糖尿病的完整 EBM 報告範例，展示每個步驟的結構化產出。

## MCP 工具

本專案使用以下 MCP 工具：
- **PubMed MCP** — search_articles, get_article_metadata, find_related_articles, get_full_text_article
- **Playwright MCP** — Cochrane Library 網站搜尋
- **Clinical Trials MCP** — ClinicalTrials.gov 進行中試驗搜尋
- **Canva MCP** — 簡報產生
- **ICD-10 MCP** — 輔助搜尋詞彙查詢

## 語言規則

- 使用者互動：繁體中文
- PubMed / API 搜尋：English
- MeSH terms：English
- 簡報內容：中文標題 + 英文引用

## 完整檔案結構

```
ebm-report-pipeline/
├── CLAUDE.md                          # 本檔案
├── README.md
├── skills/                            # 技能指令
│   ├── ebm.md                         # /ebm 主流程
│   ├── brainstorm.md                  # /brainstorm 選題
│   ├── pico.md                        # /pico 分析
│   ├── classify.md                    # /classify 問題分類
│   ├── lit-search.md                  # /lit-search 文獻搜尋
│   ├── appraise.md                    # /appraise 嚴格評讀
│   ├── ebm-slides.md                  # /ebm-slides 簡報
│   ├── save-progress.md               # /save-progress 儲存進度
│   └── load-progress.md               # /load-progress 載入進度
├── scripts/                           # 實體腳本
│   ├── init_project.py                # 初始化專案
│   ├── validate_step.py               # 驗證步驟產出
│   ├── build_search_query.py          # 建構搜尋策略
│   ├── generate_prisma_flow.py        # PRISMA 流程圖
│   ├── export_appraisal.py            # 匯出評讀 CSV
│   └── generate_pptx.py              # PowerPoint 產生器
├── data/                              # 參考資料
│   ├── departments.md                 # 科別 MeSH 對照表
│   ├── study-type-hierarchy.md        # 證據層級
│   ├── appraisal-tools.md             # 評讀工具對照表
│   ├── ebm-slide-template.md          # 簡報結構範本
│   ├── progress-schema.md             # 進度 JSON schema
│   ├── references/                    # 結構化模板
│   │   ├── pico-template.yaml         # PICO YAML 模板
│   │   ├── casp-rct-template.csv      # CASP RCT 評讀模板
│   │   └── casp-sr-template.csv       # CASP SR 評讀模板
│   └── templates/                     # 簡報設計模板
│       ├── style-a-formal.md
│       ├── style-b-clean.md
│       ├── style-c-teaching.md
│       └── style-d-competition.md
├── projects/                          # 專案目錄（每個報告一個）
│   └── example-sglt2i-ckd/            # 範例專案
└── output/                            # 舊版進度（向下相容）
```
