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

### 2. 產生檔案名稱

格式：`ebm-{YYYY-MM-DD}-{slug}.json`
- `{slug}` 從主題自動產生：取前 3-4 個關鍵英文字，用 `-` 連接，全部小寫
- 範例：`ebm-2026-04-04-sglt2i-ckd-diabetes.json`

### 3. 寫入檔案

- 將 JSON 寫入 `output/` 目錄
- 格式化為易讀的 JSON（indent=2）
- JSON schema 參見 `data/progress-schema.md`

### 4. 確認

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
