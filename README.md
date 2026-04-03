# 📋 EBM Report Pipeline

PGY 醫師的 EBM (Evidence-Based Medicine) 報告自動產生工具。

## 功能
- PubMed API 自動搜尋相關文獻
- Claude AI 分析文獻產出結構化報告
- PICO 框架（Patient/Intervention/Comparison/Outcome）
- Oxford CEBM 證據等級評估
- 台灣本土臨床指引提示

## 用法
```bash
bash ebm-report.sh "肺炎的抗生素選擇"
bash ebm-report.sh "第二型糖尿病的 SGLT2 抑制劑"
```

## 輸出格式
- Markdown 格式報告
- 包含：PICO 框架 / 文獻摘要 / 證據等級 / 臨床建議 / PGY 實務應用

## 需求
- Claude Code CLI
- curl（PubMed API）
- bash
