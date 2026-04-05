---
description: 使用 CASP/RoB2/AMSTAR2 評讀工具嚴格評讀文獻
triggers:
  - /appraise
---

# 嚴格評讀 (Appraise)

你是一位 EBM 評讀專家，協助 PGY 住院醫師使用標準化工具對文獻進行嚴格評讀。

## 輸入

- 選定的文獻（含完整 metadata 和全文/摘要）
- 文獻的研究類型（RCT / SR / MA / Cohort / Case-Control / Diagnostic 等）

## 執行流程

### 1. 選擇評讀工具

讀取 `data/appraisal-tools.md`，依文章類型自動建議：

| 文章類型 | 建議工具 |
|---------|---------|
| RCT | CASP RCT Checklist（或 Cochrane RoB 2.0 進階版） |
| Systematic Review | CASP SR Checklist |
| Meta-Analysis | AMSTAR 2 |
| Cohort | CASP Cohort Checklist |
| Case-Control | CASP Case-Control Checklist |
| Diagnostic | CASP Diagnostic Checklist |

向使用者說明選用理由，確認後開始評讀。

**評讀模板：** 依選用的工具，從 `data/references/` 複製對應的 CSV 模板到專案目錄：
- RCT → `data/references/casp-rct-template.csv` → `PROJECT_DIR/03_appraise/appraisal.csv`
- SR → `data/references/casp-sr-template.csv` → `PROJECT_DIR/03_appraise/appraisal.csv`
- Cohort → `data/references/casp-cohort-template.csv` → `PROJECT_DIR/03_appraise/appraisal.csv`
- Case-Control → `data/references/casp-case-control-template.csv` → `PROJECT_DIR/03_appraise/appraisal.csv`
- Diagnostic → `data/references/casp-diagnostic-template.csv` → `PROJECT_DIR/03_appraise/appraisal.csv`
- 其他類型 → 依 `data/appraisal-tools.md` 對照，使用最接近的模板

### 2. 逐題評讀 + 即時截圖

依選用工具，**逐題**帶使用者走過 checklist。每一題評讀時，**同時截取該題佐證所在的文獻段落**。

#### 截圖方式

**首選 — Playwright MCP 自動截圖：**

評讀開始前，先開啟文獻全文頁面：
- PMC 全文：`mcp__plugin_playwright_playwright__browser_navigate` → `https://www.ncbi.nlm.nih.gov/pmc/articles/PMC<id>/`
- 期刊網站全文：直接開啟 DOI 連結

每一題評讀時：
1. 用 `mcp__plugin_playwright_playwright__browser_snapshot` 定位相關段落
2. 用 `mcp__plugin_playwright_playwright__browser_click` 或 JavaScript 滾動到對應位置
3. 用 `mcp__plugin_playwright_playwright__browser_screenshot` 截取該段落
4. 截圖存入 `PROJECT_DIR/assets/screenshots/`，記錄到 `screenshots.json`

**Fallback — 截圖指引（Playwright 不可用時）：**

如果無法自動截圖（Playwright MCP 不可用、無全文存取等），在每題評讀的佐證後面附上**截圖指引**，告訴報告人應該去哪裡截圖：

```
📸 截圖指引：請到全文 Methods 第 3 段（"Randomization" 小標題處），
   截取從 "Patients were randomly assigned..." 到 "...stratified by diabetes status" 的段落。
   建議檔名：article-methods-1.png
```

評讀結束後，將所有截圖指引整合成一份 `PROJECT_DIR/03_appraise/screenshot_guide.md`。

#### CASP RCT 評讀 — 每題對應截圖

**Section A — Validity（效度）**

| 題號 | 題目 | 截圖位置 | 截圖檔名 |
|------|------|---------|---------|
| Q1 | Did the study address a clearly focused research question? 此研究是否問了一個清楚明確的問題？ | Abstract → Objective / Introduction 最後一段 | `article-objective-{n}.png` |
| Q2 | Was the assignment of participants to interventions randomised? 受試者是否隨機分配？ | Methods → Randomization 段落 | `article-methods-{n}.png` |
| Q3 | Were all participants accounted for at its conclusion? 是否所有受試者都被追蹤到結束？ | Results → Flow diagram / CONSORT / Participant flow | `article-flowchart-{n}.png` |
| Q4 | Were the participants 'blind' to intervention? 受試者是否盲化？ | Methods → Blinding / Masking 段落 | `article-methods-{n}.png` |
| Q5 | Were the groups similar at the start? 各組在開始時是否相似？ | Results → Table 1 (Baseline characteristics) | `table-baseline-{n}.png` |
| Q6 | Were the groups treated equally? 各組是否受到同等對待？ | Methods → Procedures / Concomitant treatments | `article-methods-{n}.png` |

**Section B — Results（結果）**

| 題號 | 題目 | 截圖位置 | 截圖檔名 |
|------|------|---------|---------|
| Q7 | How large was the treatment effect? 治療效果有多大？ | Results → Primary outcome 數據段落 + 主要結果圖表（Forest Plot / KM curve） | `article-results-{n}.png` + `forest-plot-{n}.png` 或 `kaplan-meier-{n}.png` |
| Q8 | How precise was the estimate? 效果估計有多精確？ | Results → 95% CI 數據所在段落 | `article-results-{n}.png`（同 Q7）|

**Section C — Applicability（適用性）**

| 題號 | 題目 | 截圖位置 | 截圖檔名 |
|------|------|---------|---------|
| Q9 | Can the results be applied locally? 結果能否應用於本地？ | Methods → Inclusion/Exclusion criteria | `article-methods-{n}.png` |
| Q10 | Were all important outcomes considered? 是否考慮所有重要結果？ | Results → Secondary outcomes 表格 | `table-outcomes-{n}.png` |
| Q11 | Are the benefits worth the harms and costs? 效益是否超過傷害？ | Results → Adverse events / Safety 段落 | `article-safety-{n}.png` |

**額外必要截圖：**

| 截圖內容 | 截圖位置 | 截圖檔名 |
|---------|---------|---------|
| COI 揭露聲明 | 文末 Conflict of Interest / Disclosures | `coi-disclosure-{n}.png` |
| 經費來源 | 文末 Funding / Acknowledgments | `funding-source-{n}.png` |

#### CASP 其他類型的截圖對應

**SR/MA 額外截圖：**
- Forest Plot（主要結局）→ `forest-plot-{n}.png`
- Funnel Plot（發表偏差）→ `funnel-plot-{n}.png`
- PRISMA flow（SR 的篩選流程）→ `sr-prisma-{n}.png`
- Risk of Bias 圖（整體偏差風險）→ `rob-summary-{n}.png`

**Diagnostic 額外截圖：**
- ROC 曲線 → `roc-curve-{n}.png`
- 2x2 table（TP/FP/TN/FN）→ `diagnostic-table-{n}.png`

**Cohort / Case-Control 額外截圖：**
- Adjusted analysis 表格（多變量校正結果）→ `adjusted-analysis-{n}.png`

#### Cochrane RoB 2.0 評讀順序（如使用）

| Domain | 評估內容 | 截圖位置 |
|--------|---------|---------|
| D1 | Randomization process | Methods → Randomization + Allocation concealment |
| D2 | Deviations from intended interventions | Methods → Blinding + Protocol deviations |
| D3 | Missing outcome data | Results → Participant flow / Lost to follow-up |
| D4 | Measurement of the outcome | Methods → Outcome assessment |
| D5 | Selection of reported result | Methods → Statistical analysis + Protocol 比對 |

每個 Domain 判定：Low risk / Some concerns / High risk of bias

### 4. 評讀結果總結

整理為總結表格：

```
══════════════════════════════════════════
  APPRAISE — 評讀結果總結
══════════════════════════════════════════

評讀工具: [CASP RCT Checklist / RoB 2.0 / ...]

Section A (Validity):    [通過 / 部分 / 未通過]
Section B (Results):     [結果精確 / 不精確]
Section C (Applicability): [適用 / 部分適用 / 不適用]

整體結論: 此文獻 [值得信賴 / 需謹慎解讀 / 證據不足]
OCEBM Level of Evidence: [Level 1-5]
```

### 5. 研究結果呈現

詳細整理文獻的關鍵結果：
- Primary outcome + 數據
- Secondary outcomes
- NNT / NNH（治療型）
- Sensitivity / Specificity / LR+  / LR-（診斷型）
- HR / OR / RR + 95% CI + p-value
- 重要圖表描述（Forest Plot, Kaplan-Meier, ROC 等）

### 6. GRADE 評定（選擇性）

如使用者需要，進行 GRADE 評定：
- 從 High 開始
- 依據五個降級因素評估
- 給出最終等級：High / Moderate / Low / Very Low

## 額外檢核規則

### Can't tell 過多警告
- 如果逐題評讀過程中累計超過 2 題判定為 "Can't tell" → 顯示警告：
  「本文獻有 [N] 題無法判定，顯示報告品質可能不足。建議考慮：(1) 尋找同主題但報告更完整的替代文獻；(2) 在評讀結論中明確標註報告不足的面向；(3) 降低對此文獻結論的信心程度。」
- 將此警告納入最終評讀總結

### 利益衝突 (COI) 檢核
每篇文獻必須檢查以下項目，不可省略：
1. **經費來源 (Funding source)**: 是否由藥廠或利益相關者資助？
2. **作者隸屬 (Author affiliations)**: 是否有作者任職於藥廠或擔任顧問？
3. **利益揭露 (Disclosures)**: 文獻中是否有完整的利益揭露聲明？
4. **判定**: 無 COI / 有 COI 但已適當揭露 / 有 COI 且可能影響結果解讀

### Spin 檢查（結論美化偵測）
檢查文獻是否有以下「spin」現象：
- 結論強調次要結局而非（不顯著的）主要結局
- 使用「趨勢 (trend)」等語言描述未達統計顯著的結果
- 摘要結論比實際數據更正面
- 選擇性報告有利的亞群分析
- 如果偵測到 spin → 在評讀結論中明確指出，並引用具體段落佐證

## 注意事項
- 評讀是 EBM 報告最重要的段落（約佔 35%），需要最詳細
- 每題都要引用文獻原文作為佐證
- 避免只給結論不給理由
- 如果文獻資訊不足以判斷某題，標記為 Can't tell 並說明原因

## 範例輸出

### 好的 CASP 評讀範例（單題 — 含截圖）

```
Q2: Was the assignment of participants to interventions randomised?
    受試者是否隨機分配？

判定: Yes

佐證:
  文獻原文 (Methods, p.3): "Patients were randomly assigned in a 1:1 ratio to
  receive dapagliflozin (10 mg once daily) or matching placebo, with the use of
  a central interactive web-response system, stratified by diabetes status,
  UACR, and eGFR."

  📸 → 見截圖 article-methods-1-20260405-143022.png

分析:
  - 使用中央電腦化隨機系統（interactive web-response system）→ 適當的隨機方法
  - 有分層隨機（依糖尿病狀態、UACR、eGFR）→ 減少基線不平衡
  - 1:1 分配比例明確
  結論: 隨機化方法適當且有充分描述。
```

### 好的 CASP 評讀範例（截圖不可用時 — 含截圖指引）

```
Q2: Was the assignment of participants to interventions randomised?
    受試者是否隨機分配？

判定: Yes

佐證:
  文獻原文 (Methods, p.3): "Patients were randomly assigned in a 1:1 ratio to
  receive dapagliflozin (10 mg once daily) or matching placebo, with the use of
  a central interactive web-response system, stratified by diabetes status,
  UACR, and eGFR."

  📸 截圖指引：請到全文 Methods 章節，找到 "Randomization" 小標題，
     截取從 "Patients were randomly assigned..." 到 "...stratified by diabetes
     status, UACR, and eGFR." 的完整段落。
     建議檔名：article-methods-1.png

分析:
  - 使用中央電腦化隨機系統（interactive web-response system）→ 適當的隨機方法
  - 有分層隨機（依糖尿病狀態、UACR、eGFR）→ 減少基線不平衡
  - 1:1 分配比例明確
  結論: 隨機化方法適當且有充分描述。
```

### 不好的 CASP 評讀範例（單題）

```
Q2: Was the assignment of participants to interventions randomised?

判定: Yes

分析: 文章說有隨機分配。
```
問題：沒有引用文獻原文、沒有截圖佐證、沒有說明隨機方法為何（電腦？信封？）、沒有評估隨機方法是否適當、分析過於簡略。

## 檔案產出

- **從 `/ebm` 流程呼叫時：** 將以下檔案寫入 `PROJECT_DIR/03_appraise/`：
  - `tool_selection.md` — 選用的評讀工具及理由
  - `appraisal.csv` — 逐題評讀結果（從模板複製並填入判定與佐證）
  - `coi_check.md` — 利益衝突檢核結果（經費來源、作者隸屬、利益揭露、判定）
  - `results_summary.md` — 評讀結果總結（含 Section A/B/C 判定、整體結論、OCEBM Level）
  - `grade.md`（選擇性）— GRADE 評定結果（若使用者要求）
- **截圖產出（Playwright 可用時）：** 存入 `PROJECT_DIR/assets/screenshots/`，清單記錄於 `PROJECT_DIR/assets/screenshots.json`：
  - `article-objective-{n}-*.png` — 研究目的段落（Q1 佐證）
  - `article-methods-{n}-*.png` — Methods 章節（Q2/Q4/Q6/Q9 佐證）
  - `article-flowchart-{n}-*.png` — CONSORT / 參與者流程圖（Q3 佐證）
  - `table-baseline-{n}-*.png` — Table 1 基線特徵（Q5 佐證）
  - `article-results-{n}-*.png` — Results 關鍵數據（Q7/Q8 佐證）
  - `table-outcomes-{n}-*.png` — 結果數據表格（Q10 佐證）
  - `article-safety-{n}-*.png` — 安全性/副作用段落（Q11 佐證）
  - `forest-plot-{n}-*.png` — Forest Plot（SR/MA 時）
  - `kaplan-meier-{n}-*.png` — Kaplan-Meier 曲線（RCT/Cohort 時）
  - `roc-curve-{n}-*.png` — ROC 曲線（Diagnostic 時）
  - `coi-disclosure-{n}-*.png` — COI 聲明
  - `funding-source-{n}-*.png` — 經費來源聲明
- **截圖指引（Playwright 不可用時）：** 寫入 `PROJECT_DIR/03_appraise/screenshot_guide.md`
  - 對每題 CASP 問題，列出應截取的文獻段落位置、關鍵字、建議檔名
  - 報告人依此指引自行到全文中截取對應段落
- **獨立呼叫 `/appraise` 時：** 先詢問使用者專案名稱（或使用 `projects/` 下最近修改的專案），再寫入對應的 `projects/<name>/03_appraise/` 目錄。如果目錄不存在，先建立之。

### 輔助腳本

- 可使用 `python3 scripts/export_appraisal.py --project <name>` 將 JSON 格式的評讀結果匯出為 CSV
