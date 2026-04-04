# EBM Report Pipeline

PGY 住院醫師的 EBM (Evidence-Based Medicine) 報告互動式產生工具。

透過 Claude Code 的互動式引導，遵循 **5A 框架**（Ask → Acquire → Appraise → Apply → Audit），從選科別到產出簡報，完成完整的 EBM 報告。

## 功能

- **選科選題**：支援 24 個臨床科別，可自訂題目或從 PubMed 近期文獻中選題
- **PICO 分析**：自動拆解臨床問題為 P/I/C/O，附 MeSH Terms
- **6S 階層搜尋**：UpToDate → DynaMed → Cochrane → PubMed → Embase，含 PRISMA 流程
- **嚴格評讀**：自動選用 CASP / RoB 2.0 / AMSTAR 2 評讀工具，逐題評讀
- **臨床應用**：OCEBM 證據等級 + 台灣在地考量 + 去學術化臨床回覆
- **簡報產生**：4 種設計模板，透過 Canva 自動產生 50-70 張投影片

## 快速開始

### 需求
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)
- MCP 工具：PubMed、Playwright、Clinical Trials、Canva（透過 claude.ai 自動提供）

### 使用

```bash
git clone https://github.com/platypus31/ebm-report-pipeline.git
cd ebm-report-pipeline
claude
```

輸入 `/ebm` 開始完整流程，或使用子指令：

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

## 進度儲存

EBM 報告流程較長，支援中途儲存與續做：

- 每完成一個 5A 階段（ASK / ACQUIRE / APPRAISE / APPLY+AUDIT），系統自動儲存進度到 `output/` 目錄
- 也可以隨時使用 `/save-progress` 手動儲存
- 下次啟動 `/ebm` 時，系統會自動偵測已儲存的進度，詢問是否繼續
- 使用 `/load-progress` 可以直接列出並載入先前的進度

進度檔案格式為 JSON，檔名為 `ebm-{日期}-{主題關鍵字}.json`。

## 5A 框架流程

```
檢查已儲存的進度 → 選科 → 選題（或 Brainstorm）
         ↓
┌─── ASK ──────────────────────────┐
│  PICO 分析                        │
│  臨床情境 (Clinical Scenario)      │
│  背景資訊 (Introduction)           │
│  問題分類（治療/診斷/預後/傷害/預防）│
└──────────────────────────────────┘
         ↓ [自動儲存進度]
┌─── ACQUIRE ──────────────────────┐
│  6S 階層搜尋                      │
│  PRISMA 篩選流程                   │
│  選文理由                          │
└──────────────────────────────────┘
         ↓ [自動儲存進度]
┌─── APPRAISE ─────────────────────┐
│  評讀工具選擇                      │
│  逐題評讀（CASP / RoB 2 / AMSTAR）│
│  結果呈現 + GRADE（選擇性）        │
└──────────────────────────────────┘
         ↓ [自動儲存進度]
┌─── APPLY ────────────────────────┐
│  OCEBM 證據等級                    │
│  臨床應用 + 台灣在地考量           │
│  去學術化臨床回覆                   │
└──────────────────────────────────┘
         ↓
┌─── AUDIT ────────────────────────┐
│  五面向自我評估                    │
└──────────────────────────────────┘
         ↓ [自動儲存進度]
    產生簡報（Canva → python-pptx → Markdown）
```

## 簡報設計模板

| 模板 | 風格 | 張數 | 適合場合 |
|------|------|------|---------|
| A | 正式學術 — 側邊欄 5A 導航 | 45-55 | 科內正式報告 |
| B | 簡潔現代 — 大量留白、圖示化 | 40-50 | Journal club |
| C | 教學導向 — 6A 擴充、附教學提示 | 50-60 | EBM 初學者 |
| D | 競賽完整 — GRADE + SDM + 成本效益 | 55-70 | EBM 競賽 |

## 證據層級篩選

依問題類型自動套用最佳研究設計：

| 問題類型 | 最佳證據 | 評讀工具 |
|---------|---------|---------|
| 治療型 | RCT | CASP RCT / RoB 2.0 |
| 預防型 | RCT | CASP RCT / RoB 2.0 |
| 診斷型 | Prospective blind comparison | CASP Diagnostic |
| 預後型 | Cohort study | CASP Cohort |
| 病因傷害型 | Cohort study | CASP Cohort |

## License

MIT
