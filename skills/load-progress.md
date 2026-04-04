---
description: 載入已儲存的 EBM 報告進度並繼續
triggers:
  - /load-progress
---

# 載入進度

載入先前儲存的 EBM 報告進度，從上次完成的步驟繼續。

## 執行流程

### 1. 列出已儲存的進度檔案

從兩個來源掃描已儲存的進度：

**來源 A — Project-based（主要）：**
- 掃描 `projects/` 目錄中的所有子目錄
- 讀取每個專案的 `progress.json`（若存在）取得 `current_step` 和 `updated`
- 讀取 `01_ask/pico.yaml`（若存在）取得主題和 PICO 資訊

**來源 B — Legacy（backward compat）：**
- 掃描 `output/` 目錄中所有符合 `ebm-*.json` 的檔案

將兩個來源合併，以表格呈現：

```
══════════════════════════════════════════
  已儲存的 EBM 報告進度
══════════════════════════════════════════

 #  | 來源    | 專案/檔案名稱                          | 主題                    | 目前步驟  | 更新日期
----|---------|---------------------------------------|------------------------|----------|----------
 1  | project | projects/sglt2i-ckd-diabetes/          | SGLT2i 在 CKD 合併糖尿病 | ACQUIRE  | 2026-04-04
 2  | project | projects/hs-ctni-ami/                  | hs-cTnI 診斷 AMI        | APPRAISE | 2026-03-28
 3  | legacy  | output/ebm-2026-03-15-aspirin-cad.json | Aspirin 在 CAD 預防      | ASK      | 2026-03-15

══════════════════════════════════════════
請選擇要載入的進度（輸入編號），或輸入 0 開始新報告：
```

如果沒有任何進度檔案，顯示：「目前沒有已儲存的進度。將開始新的 EBM 報告。」

### 2. 載入選定的檔案

**Project-based 來源：**
- 設定 `PROJECT_DIR` 為選定的專案目錄（例如 `projects/sglt2i-ckd-diabetes/`）
- 讀取 `PROJECT_DIR/progress.json`
- 讀取各步驟子目錄中的結構化檔案（`01_ask/pico.yaml`、`02_acquire/search_strategy.md` 等）
- 將所有已儲存的資料載入到對話 context 中

**Legacy 來源：**
- 讀取 JSON 檔案
- 驗證 `version` 欄位是否相容
- 將所有已儲存的資料載入到對話 context 中

### 3. 顯示已載入的摘要

```
══════════════════════════════════════════
  進度已載入
══════════════════════════════════════════

主題: SGLT2 抑制劑在 CKD 合併糖尿病的腎臟保護效果
科別: 腎臟內科
目前步驟: ACQUIRE

已完成的步驟:
  - 科別選擇: 腎臟內科
  - 主題: SGLT2 抑制劑在 CKD 合併糖尿病的腎臟保護效果
  - PICO: P=65 歲以上 T2DM+CKD / I=Dapagliflozin / C=Placebo / O=eGFR 下降
  - 問題分類: 治療型

下一步: 文獻搜尋（ACQUIRE Step 8）

══════════════════════════════════════════
繼續？(Y/N)
```

### 4. 繼續流程

- 確認後，從 `current_step` 對應的步驟繼續執行 `/ebm` 的流程
- 已完成的步驟不再重複，但使用者可以要求回到任何步驟修改

## 注意事項
- 所有使用者互動用**繁體中文**
- 如果 JSON 檔案格式損壞，顯示友善的錯誤訊息並建議開始新報告
- 載入後更新 `updated` 日期
