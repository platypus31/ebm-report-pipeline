# EBM Report Pipeline

PGY 住院醫師的 EBM (Evidence-Based Medicine) 報告互動式產生工具。

透過 Claude Code 的互動式引導，遵循 **5A 框架**（Ask → Acquire → Appraise → Apply → Audit），從選科別到產出簡報，完成完整的 EBM 報告。**每個步驟都產出結構化檔案**，確保可追蹤、可驗證。

## 功能

- **專案化管理**：每個 EBM 報告獨立一個專案目錄，結構清晰
- **結構化產出**：PICO 存為 YAML、評讀結果存為 CSV、搜尋策略完整記錄
- **品質門檻**：每個 5A 階段完成時自動驗證產出完整性
- **實體腳本**：6 支 Python 腳本，搜尋策略建構、PRISMA 流程圖、步驟驗證均可獨立執行
- **24 科別支援**：完整科別 MeSH 對照表，自動建構搜尋策略
- **嚴格評讀**：CASP / RoB 2.0 / AMSTAR 2，結構化 CSV 匯出
- **簡報產生**：4 種設計模板，Canva → python-pptx → Markdown 三層 fallback
- **範例專案**：`projects/example-sglt2i-ckd/` 展示完整產出

## 快速開始

### 需求
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)
- Python 3.8+（腳本用）
- MCP 工具：PubMed、Playwright、Clinical Trials、Canva（透過 claude.ai 自動提供）

### 使用

```bash
git clone https://github.com/platypus31/ebm-report-pipeline.git
cd ebm-report-pipeline
claude
```

輸入 `/ebm` 開始完整流程。Claude 會：
1. 建立 `projects/<name>/` 專案目錄
2. 引導完成 5A 每個步驟
3. 每步產出結構化檔案（YAML、CSV、MD）
4. 每個階段完成時驗證品質
5. 最終產出 PowerPoint 簡報

### 手動建立專案

```bash
python3 scripts/init_project.py --name my-topic --department 腎臟內科
```

### 子指令

| 指令 | 功能 |
|------|------|
| `/ebm` | 完整 5A 框架流程 |
| `/brainstorm` | PubMed 近期文獻選題 |
| `/pico` | PICO 分析 |
| `/classify` | 問題分類 |
| `/lit-search` | 6S 文獻搜尋 |
| `/appraise` | 嚴格評讀 |
| `/ebm-slides` | 選模板 + 產生簡報 |
| `/save-progress` | 儲存目前報告進度 |
| `/load-progress` | 載入已儲存的進度 |

## 專案目錄結構

```
projects/<name>/
├── TOPIC.txt              # 主題描述
├── 01_ask/                # PICO、臨床情境、分類
│   ├── pico.yaml          # 結構化 PICO（YAML）
│   ├── clinical_scenario.md
│   └── classification.md
├── 02_acquire/            # 搜尋策略、PRISMA、選文
│   ├── search_strategy.md
│   ├── prisma_flow.md
│   ├── candidates.csv     # 候選文獻（CSV）
│   └── selected_articles.md
├── 03_appraise/           # 評讀結果
│   ├── appraisal.csv      # 逐題評讀（CSV）
│   ├── coi_check.md
│   └── results_summary.md
├── 04_apply/              # 證據等級、臨床應用
│   ├── evidence_level.md
│   └── clinical_reply.md
├── 05_audit/              # 自我評估
│   └── self_assessment.md
└── 06_slides/             # 簡報
    └── slides.json
```

## 實體腳本

| 腳本 | 用途 | 範例 |
|------|------|------|
| `init_project.py` | 初始化專案 | `python3 scripts/init_project.py --name sglt2i-ckd` |
| `validate_step.py` | 驗證步驟產出 | `python3 scripts/validate_step.py --project sglt2i-ckd` |
| `build_search_query.py` | 建構搜尋策略 | `python3 scripts/build_search_query.py --project sglt2i-ckd` |
| `generate_prisma_flow.py` | PRISMA 流程圖 | `python3 scripts/generate_prisma_flow.py --project sglt2i-ckd` |
| `export_appraisal.py` | 匯出評讀 CSV | `python3 scripts/export_appraisal.py --project sglt2i-ckd` |
| `generate_pptx.py` | 產生 PowerPoint | `python3 scripts/generate_pptx.py slides.json output.pptx` |

## 5A 框架流程

```
初始化專案 → 選科 → 選題（或 Brainstorm）
         ↓
┌─── ASK ──────────────────────────────┐
│  PICO 分析 → pico.yaml               │
│  臨床情境 → clinical_scenario.md      │
│  背景資訊 → introduction.md           │
│  問題分類 → classification.md         │
└───────── [品質門檻驗證] ─────────────┘
         ↓
┌─── ACQUIRE ──────────────────────────┐
│  搜尋策略 → search_strategy.md        │
│  PRISMA 篩選 → prisma_flow.md        │
│  選文理由 → candidates.csv            │
└───────── [品質門檻驗證] ─────────────┘
         ↓
┌─── APPRAISE ─────────────────────────┐
│  評讀工具選擇 → tool_selection.md     │
│  逐題評讀 → appraisal.csv            │
│  COI 檢核 → coi_check.md             │
│  結果呈現 → results_summary.md        │
└───────── [品質門檻驗證] ─────────────┘
         ↓
┌─── APPLY ────────────────────────────┐
│  OCEBM 證據等級 → evidence_level.md   │
│  臨床應用 → local_considerations.md   │
│  臨床回覆 → clinical_reply.md         │
└──────────────────────────────────────┘
         ↓
┌─── AUDIT ────────────────────────────┐
│  自我評估 → self_assessment.md        │
└───────── [品質門檻驗證] ─────────────┘
         ↓
    產生簡報 → slides.json / ebm-report.pptx
```

## 範例專案

`projects/example-sglt2i-ckd/` 展示完整的 SGLT2i 在 CKD 合併糖尿病的 EBM 報告：

- **5 RCT 候選文獻**，最終選定 DAPA-CKD Trial
- **CASP RCT 11 題完整評讀**（結構化 CSV）
- **GRADE: High (⊕⊕⊕⊕)**
- **OCEBM Level 2**
- 完整台灣在地化考量（健保給付、用藥可取得性）

## 簡報設計模板

| 模板 | 風格 | 張數 | 適合場合 |
|------|------|------|---------|
| A | 正式學術 — 側邊欄 5A 導航 | 45-55 | 科內正式報告 |
| B | 簡潔現代 — 大量留白、圖示化 | 40-50 | Journal club |
| C | 教學導向 — 6A 擴充、附教學提示 | 50-60 | EBM 初學者 |
| D | 競賽完整 — GRADE + SDM + 成本效益 | 55-70 | EBM 競賽 |

## License

MIT
