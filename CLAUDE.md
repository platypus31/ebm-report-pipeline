# EBM Report Pipeline

PGY 住院醫師的 EBM (Evidence-Based Medicine) 報告互動式產生工具。從選科別到產出簡報的完整 12 步驟流程。

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

## 使用方式

```bash
cd ebm-report-pipeline
claude
> /ebm
```

也可以單獨使用子技能：
```
> /brainstorm    # 只做選題
> /pico          # 只做 PICO 分析
> /lit-search    # 只做文獻搜尋
```

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

## 專案結構

```
ebm-report-pipeline/
├── CLAUDE.md                  # 本檔案
├── README.md
├── skills/
│   ├── ebm.md                 # /ebm 主流程
│   ├── brainstorm.md          # /brainstorm 選題
│   ├── pico.md                # /pico 分析
│   ├── classify.md            # /classify 問題分類
│   ├── lit-search.md          # /lit-search 文獻搜尋
│   ├── appraise.md            # /appraise 嚴格評讀
│   └── ebm-slides.md         # /ebm-slides 簡報
└── data/
    ├── departments.md         # 科別 MeSH 對照表
    ├── study-type-hierarchy.md # 證據層級
    ├── appraisal-tools.md     # 評讀工具對照表 (CASP/AMSTAR/CEBM)
    ├── ebm-slide-template.md  # 簡報結構範本 (5A)
    └── templates/             # 簡報設計模板
        ├── style-a-formal.md      # 正式學術風格
        ├── style-b-clean.md       # 簡潔現代風格
        ├── style-c-teaching.md    # 教學導向風格
        └── style-d-competition.md # 競賽完整風格
```
