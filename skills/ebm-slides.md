---
description: 選擇設計模板並使用 Canva MCP 產生 EBM 簡報
triggers:
  - /ebm-slides
---

# EBM 簡報產生

你是一位擅長製作 EBM 簡報的教學醫師，將所有蒐集到的資料整理成結構清晰的簡報。

## 輸入

- 科別、臨床問題
- 臨床情境 (Clinical Scenario)
- 背景資訊 (Introduction)
- PICO 分析
- 問題分類與證據層級
- 搜尋策略（6S 結果 + PRISMA 流程）
- 選文理由
- Critical Appraisal 結果（評讀工具、逐題結果、總結）
- 研究結果（關鍵數據）
- 臨床應用（OCEBM Level + 台灣在地考量 + 去學術化回覆）
- 自我評估

## 執行流程

### 1. 選擇設計模板

讀取 `data/templates/` 下的所有模板，呈現選項：

```
══════════════════════════════════════════
  選擇簡報設計風格
══════════════════════════════════════════

A. 正式學術風格 — 側邊欄 5A 導航，深藍配色，適合科內正式報告
B. 簡潔現代風格 — 大量留白，圖示化，適合 Journal club
C. 教學導向風格 — 6A 擴充，附教學提示，適合 EBM 初學者
D. 競賽完整風格 — 最完整版本（GRADE + SDM + 成本效益），適合 EBM 競賽

請選擇（A/B/C/D）：
```

### 2. 整理簡報大綱

根據選定模板的段落配置和 `data/ebm-slide-template.md` 的結構，整理所有資料為投影片大綱。

**讀取專案結構化檔案：** 從 `PROJECT_DIR` 讀取各步驟產出的檔案作為簡報素材：
- `01_ask/pico.yaml` — PICO 分析與問題分類
- `01_ask/classification.md` — 問題分類與證據層級
- `02_acquire/search_strategy.md` — 搜尋策略
- `02_acquire/prisma_flow.md` — PRISMA 篩選流程
- `02_acquire/selected_articles.md` — 選定文獻
- `03_appraise/results_summary.md` — 評讀結果總結
- `03_appraise/coi_check.md` — 利益衝突檢核
- `04_apply/` — 臨床應用相關檔案（若存在）
- `05_audit/` — 自我評估相關檔案（若存在）
- `assets/screenshots.json` — 截圖清單（引用截圖到對應投影片）

**截圖整合到投影片：** 讀取 `assets/screenshots.json`，將截圖按階段對應到投影片：

| 截圖類型 | 對應投影片 | 用途 |
|---------|----------|------|
| `pubmed-search-*.png` | ACQUIRE — 搜尋策略 | 證明搜尋過程 |
| `pubmed-filters-*.png` | ACQUIRE — 搜尋策略 | 展示篩選器設定 |
| `cochrane-search-*.png` | ACQUIRE — Cochrane 結果 | 6S 階層搜尋 |
| `article-abstract-*.png` | ACQUIRE — 選文 | 文獻摘要概覽 |
| `article-methods-*.png` | APPRAISE — 評讀 Section A | 研究方法佐證 |
| `article-results-*.png` | APPRAISE — 評讀 Section B | 結果數據佐證 |
| `forest-plot-*.png` | APPRAISE — 結果呈現 | Forest Plot 圖表 |
| `kaplan-meier-*.png` | APPRAISE — 結果呈現 | 存活曲線圖表 |
| `roc-curve-*.png` | APPRAISE — 結果呈現（診斷型）| ROC 曲線圖表 |
| `table-baseline-*.png` | APPRAISE — 基線特徵 | Table 1 |
| `table-outcomes-*.png` | APPRAISE — 結果呈現 | 結果數據表格 |

在簡報大綱中，為每張有截圖的投影片加入 `image` 欄位，指向截圖檔案路徑。

關鍵要素：
- 每個 5A 階段之間插入**導航過場頁**（依模板風格）
- 評讀段落佔最大篇幅（約 35%）
- 投影片張數依模板而異（Style B: 40-50 張, Style D: 55-70 張）

向使用者展示完整大���，確認內容和順序。

### 3. 產生 Canva 簡報

使用 Canva MCP 的三步驟流程：

**Step A — 提交大綱審核:**
呼叫 `mcp__claude_ai_Canva__request-outline-review`:
- topic: EBM 報告標題（繁體中文，150 字以內）
- pages: 每張投影片的標題和內容要點
- 依模板風格描述設計需求（配色、排版、導航方式）

**Step B — 生成設計:**
呼叫 `mcp__claude_ai_Canva__generate-design-structured`:
- design_type: "presentation"
- 使用經過確認的大綱
- 融入模板風格描述

**Step C — 建立設計:**
呼叫 `mcp__claude_ai_Canva__create-design-from-candidate`:
- 使用者選擇喜歡的設計方案
- 取得最終 Canva 設計連結

### 4. 交付

提供 Canva 設計連結，提醒使用者：
- 可以在 Canva 編輯器中進一步調整
- 截圖已自動存入 `PROJECT_DIR/assets/screenshots/`，可直接拖入簡報
- 檢查截圖完整性：`python3 scripts/screenshot.py --project <name> --check`
- 可以匯出為 PDF 或 PPTX

## 投影片內容指引

每張投影片的文字要精簡：
- 標題：1 行
- 內容：3-5 ��重點，每點 1-2 行
- 數據用粗體標示
- 參考文獻用小字
- 評讀題目中英對照

## 簡報產生 Fallback 鏈

簡報產生依照以下順序自動嘗試，每一層失敗時自動進入下一層：

```
1. Canva MCP（首選）
   ├── 成功 → 交付 Canva 設計連結
   └── 失敗 → 進入第 2 層
2. python-pptx 產生 .pptx
   ├── 成功 → 交付 .pptx 檔案到桌面
   └── 失敗（缺少套件等）→ 進入第 3 層
3. Markdown 格式輸出
   └── 將完整簡報大綱以 Markdown 格式輸出，使用者可自行貼入簡報工具
```

每次 fallback 時，告知使用者：「[上一層方法] 無法使用（原因：[錯誤訊息]），已自動切換到 [下一層方法]。」

## Fallback 第 2 層 — python-pptx 產生 .pptx

使用 `scripts/generate_pptx.py` 產生可編輯的 PowerPoint 檔案：

1. 將所有投影片資料整理成 JSON 格式（參考 `scripts/generate_pptx.py` 頂部的格式說明）
2. 每張投影片的 `type` 可以是：`title`、`section`、`content`、`two_column`、`table`
3. 依照使用者選擇的模板風格設定 `style`：`formal`、`clean`、`teaching`、`competition`
4. 每張內容投影片的 `section` 欄位設定為當前 5A 階段（ASK/ACQUIRE/APPRAISE/APPLY/AUDIT），自動顯示側邊欄導航
5. 將 JSON 寫入暫存檔，執行：
   ```bash
   python3 scripts/generate_pptx.py slides.json PROJECT_DIR/06_slides/ebm-report.pptx
   ```
6. 告知使用者檔案位置，可用 PowerPoint / Keynote / Google Slides 開啟編輯

### JSON 範例

```json
{
    "title": "SGLT2 抑制劑在 CKD 合併糖尿病的腎臟保護效果",
    "author": "王大明",
    "department": "腎臟內科",
    "date": "2026-04-04",
    "style": "formal",
    "slides": [
        {"type": "section", "title": "ASK", "subtitle": "問題"},
        {"type": "content", "title": "臨床場景", "bullets": ["68歲男性...", "..."], "section": "ASK"},
        {"type": "content", "title": "PICO", "bullets": ["P: ...", "I: ...", "C: ...", "O: ..."], "section": "ASK"},
        {"type": "section", "title": "ACQUIRE", "subtitle": "檢索"},
        {"type": "table", "title": "搜尋結果", "headers": ["資料庫", "結果數"], "rows": [["PubMed", "15"], ["Cochrane", "3"]], "section": "ACQUIRE"}
    ]
}
```

## Fallback 第 3 層 — Markdown 格式輸出

如果 python-pptx 也無法使用（例如缺少 python-pptx 套件），將完整簡報以 Markdown 格式輸出：

1. 輸出檔案路徑：`PROJECT_DIR/06_slides/ebm-slides.md`（若無 PROJECT_DIR 則 fallback 到 `output/ebm-slides-{date}.md`）
2. 格式：每張投影片以 `---` 分隔，標題用 `## `，重點用 `- `
3. 告知使用者可將 Markdown 匯入 Google Slides、Marp、或手動製作簡報

## 注意事項
- 投影片標題用**繁體中文**
- 文獻引用保持**英文**（作者、期刊名）
- 數據（HR, OR, CI, p-value）保持原文呈現
- **依照 Fallback 鏈順序**自動選擇產生方式（Canva → python-pptx → Markdown）
- python-pptx 產出的 .pptx 可在 PowerPoint / Keynote / Google Slides 中自由編輯

## 檔案產出

- **從 `/ebm` 流程呼叫時：** 將以下檔案寫入 `PROJECT_DIR/06_slides/`：
  - `slides.json` — 投影片結構化資料（JSON 格式，含每張投影片的 type、title、bullets、section 等）
  - `ebm-report.pptx` — python-pptx 產生的 PowerPoint 檔案（Fallback 第 2 層時）
- **獨立呼叫 `/ebm-slides` 時：** 先詢問使用者專案名稱（或使用 `projects/` 下最近修改的專案），設定 `PROJECT_DIR` 後再執行。如果目錄不存在，先建立 `projects/<name>/06_slides/`。
- Markdown fallback 輸出路徑也更新為 `PROJECT_DIR/06_slides/ebm-slides.md`（取代原先的 `output/ebm-slides-{date}.md`）
