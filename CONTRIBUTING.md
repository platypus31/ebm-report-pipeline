# Contributing 貢獻指南

感謝你有興趣改善 EBM Report Pipeline！

## 如何貢獻

### 1. Fork 此 repo
點擊右上角的 **Fork** 按鈕，複製一份到你自己的 GitHub 帳號。

### 2. 修改
- 可以直接在 GitHub 網頁上編輯檔案
- 或 clone 到本地修改：
  ```bash
  git clone https://github.com/<你的帳號>/ebm-report-pipeline.git
  cd ebm-report-pipeline
  git checkout -b my-improvement
  # 修改檔案...
  git add . && git commit -m "描述你的改動"
  git push origin my-improvement
  ```

### 3. 發送 Pull Request
- 回到 GitHub，點 **「Contribute」→「Open pull request」**
- 標題簡述改動（例：「新增放射科 MeSH terms」）
- 描述中說明：
  - 改了什麼
  - 為什麼要改
  - 如果是新增科別或評讀工具，附上參考來源

### 4. 等待審核
維護者會審查你的 PR，可能會提出修改建議。

## 適合貢獻的方向

- 擴充 `data/departments.md` 的 MeSH terms（特別是子專科）
- 新增或修正 `data/appraisal-tools.md` 的評讀工具
- 改善 skill 的 prompt 品質（更好的範例、更精確的指引）
- 修正 `scripts/generate_pptx.py` 的 bug 或新增投影片版型
- 翻譯或多語言支援
- 新增台灣本土指引參考資料

## 注意事項

- 請勿提交含有個人資訊的檔案（姓名、病歷、醫院名稱）
- 所有使用者面向文字請使用繁體中文
- PubMed 搜尋相關內容請使用英文
- 提交前請確認 JSON 格式正確（如修改 progress-schema 等）
