---
description: 儲存目前 EBM 報告進度到 JSON 檔案
triggers:
  - /save-progress
---

# 儲存進度

將目前 EBM 報告的所有累積資料儲存為 JSON 檔案，方便下次繼續。

## 執行流程

### 1. 收集目前所有已完成的資料

從對話中收集以下已完成的項目（未完成的項目留空或設為 null）：

- `version`: 固定為 "1.0"
- `created`: 首次建立日期（若為新檔案，使用今天日期）
- `updated`: 更新日期（使用今天日期）
- `current_step`: 目前所在步驟（TOPIC / ASK / ACQUIRE / APPRAISE / APPLY / AUDIT / SLIDES）
- `department`: 科別資訊（名稱、MeSH terms）
- `topic`: 使用者選定的主題
- `clinical_scenario`: 臨床情境
- `pico`: PICO 分析結果（P/I/C/O 各含中文和 MeSH）
- `classification`: 問題分類結果（類型、理由、證據層級）
- `search_strategy`: 搜尋策略（搜尋式、各資料庫結果數）
- `selected_articles`: 選定文獻（PMID、標題、期刊、選文理由）
- `appraisal`: 評讀結果（工具、逐題結果、總結）
- `application`: 臨床應用（證據等級、在地考量、臨床回覆）
- `self_assessment`: 自我評估結果
- `template_style`: 選定的簡報風格

### 2. 決定儲存路徑

**主要路徑（project-based）：**
- 如果 `PROJECT_DIR` 已設定（從 `/ebm` 流程中建立），直接儲存到 `PROJECT_DIR/progress.json`
- JSON 中額外包含 `project_dir` 欄位，記錄專案路徑（例如 `"project_dir": "projects/sglt2i-ckd-diabetes"`）

**備用路徑（backward compat）：**
- 如果沒有 `PROJECT_DIR`（例如獨立呼叫 `/save-progress`），則使用舊格式：
  - 產生檔案名稱：`ebm-{YYYY-MM-DD}-{slug}.json`
  - `{slug}` 從主題自動產生：取前 3-4 個關鍵英文字，用 `-` 連接，全部小寫
  - 範例：`ebm-2026-04-04-sglt2i-ckd-diabetes.json`
  - 儲存至 `output/` 目錄

### 3. 寫入檔案

- 如果目標目錄不存在，先建立目錄（`mkdir -p`）
- 格式化為易讀的 JSON（indent=2）
- JSON schema 參見 `data/progress-schema.md`
- JSON 中必須包含 `project_dir` 欄位（若為 project-based 路徑則為專案路徑，若為 output/ 路徑則為 null）

### 4. 確認

**Project-based 範例：**
```
進度已儲存：projects/sglt2i-ckd-diabetes/progress.json
目前步驟：ACQUIRE（文獻搜尋）
已完成：科別、主題、PICO、問題分類、搜尋策略
未完成：評讀、應用、自我評估、簡報

下次使用 /load-progress 即可繼續。
```

**Backward compat 範例：**
```
進度已儲存：output/ebm-2026-04-04-sglt2i-ckd-diabetes.json
目前步驟：ACQUIRE（文獻搜尋）
已完成：科別、主題、PICO、問題分類、搜尋策略
未完成：評讀、應用、自我評估、簡報

下次使用 /load-progress 即可繼續。
```

## 注意事項
- 如果同名檔案已存在，更新 `updated` 日期並覆寫
- 所有使用者互動用**繁體中文**
- JSON 中的中文欄位值用繁體中文，欄位名稱用英文
- 寫入前務必確認目標目錄存在，若不存在則自動建立（`output/` 或 `PROJECT_DIR/`）
