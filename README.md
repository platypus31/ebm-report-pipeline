# EBM Report Pipeline

PGY 住院醫師的 EBM (Evidence-Based Medicine) 報告互動式產生工具。

透過 Claude Code 的互動式引導，從選科別到產出簡報，完成完整的 EBM 報告流程。

## 功能

- **選科選題**：支援 24 個臨床科別，可自訂題目或從 PubMed 近期文獻中選題
- **PICO 分析**：自動拆解臨床問題為 Population / Intervention / Comparison / Outcome
- **問題分類**：判斷診斷型、預後型、治療型、預防型、病因傷害型
- **文獻搜尋**：PubMed + Cochrane Library，依問題類型自動套用最佳證據篩選
- **簡報產生**：透過 Canva 自動產生 EBM 簡報

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
| `/ebm` | 完整 7 步驟流程 |
| `/brainstorm` | PubMed 近期文獻選題 |
| `/pico` | PICO 分析 |
| `/classify` | 問題分類 |
| `/lit-search` | 文獻搜尋 |
| `/ebm-slides` | 產生簡報 |

## 完整流程

```
Step 1:  選擇科別（NEPH, CV, GU...）
    ↓
Step 2:  有題目？ ──Y──→ Step 4
    ↓ N
Step 3:  Brainstorm（PubMed 近 1 月文獻）
    ↓
Step 4:  PICO 分析
    ↓
Step 5:  建立臨床情境 (Clinical Scenario)
    ↓
Step 6:  問題分類（診斷/預後/治療/預防/病因傷害）
    ↓
Step 7:  文獻搜尋（PubMed + Embase + Cochrane + UpToDate + DynaMed）
    ↓
Step 8:  說明選文理由
    ↓
Step 9:  Critical Appraisal（CASP / AMSTAR 2 / CEBM 評讀）
    ↓
Step 10: 臨床應用 (Applying)
    ↓
Step 11: 自我評估 (Self-Assessment)
    ↓
Step 12: 產生簡報（Canva）
```

## 證據層級篩選

依問題類型自動套用最佳研究設計：

| 問題類型 | 最佳證據 |
|---------|---------|
| 治療型 | RCT |
| 預防型 | RCT |
| 診斷型 | Prospective blind comparison with gold standard |
| 預後型 | Cohort study |
| 病因傷害型 | Cohort study |

## License

MIT
