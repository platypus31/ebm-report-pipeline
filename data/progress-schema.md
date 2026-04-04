# EBM 進度檔案 JSON Schema

`output/ebm-{date}-{slug}.json` 的資料結構定義。

## Schema

```json
{
  "version": "1.0",
  "created": "2026-04-04",
  "updated": "2026-04-04",
  "current_step": "ACQUIRE",

  "department": {
    "name": "腎臟內科",
    "name_en": "Nephrology",
    "mesh_terms": ["Nephrology", "Kidney Diseases"]
  },

  "topic": "SGLT2 抑制劑在 CKD 合併糖尿病的腎臟保護效果",

  "clinical_scenario": "68 歲男性，糖尿病病史 15 年，目前使用 Metformin + Glimepiride 控制血糖，最近抽血發現 eGFR 下降至 38 mL/min/1.73m2...",

  "pico": {
    "p": {
      "zh": "65 歲以上第二型糖尿病合併慢性腎臟病（eGFR 25-60）患者",
      "mesh": "\"Diabetes Mellitus, Type 2\"[MeSH] AND \"Renal Insufficiency, Chronic\"[MeSH] AND \"Aged\"[MeSH]"
    },
    "i": {
      "zh": "Dapagliflozin 10mg 每日一次",
      "mesh": "\"Sodium-Glucose Transporter 2 Inhibitors\"[MeSH]"
    },
    "c": {
      "zh": "安慰劑（加上標準糖尿病照護）",
      "mesh": "\"Placebos\"[MeSH]"
    },
    "o": {
      "zh": "腎功能惡化（eGFR 持續下降 >= 50%、末期腎病或腎臟相關死亡之複合結局）",
      "mesh": "\"Glomerular Filtration Rate\"[MeSH], \"Kidney Failure, Chronic\"[MeSH]"
    }
  },

  "classification": {
    "type": "therapeutic",
    "type_zh": "治療型",
    "reasoning": "I 為藥物治療（SGLT2 inhibitor），比較兩種方案的臨床結果",
    "evidence_hierarchy": [
      "Systematic Review / Meta-analysis of RCTs",
      "Individual RCT",
      "Cohort study"
    ],
    "pubmed_filter": "Randomized Controlled Trial[pt] OR Meta-Analysis[pt] OR Systematic Review[pt]"
  },

  "search_strategy": {
    "pubmed_query": "(\"Diabetes Mellitus, Type 2\"[MeSH] OR \"T2DM\") AND (\"Sodium-Glucose Transporter 2 Inhibitors\"[MeSH] OR \"SGLT2\") AND ...",
    "cochrane_query": "SGLT2 inhibitor AND chronic kidney disease AND diabetes",
    "results_summary": {
      "uptodate": "有相關建議",
      "cochrane": 2,
      "pubmed": 15,
      "embase": "策略已建構"
    },
    "prisma": {
      "identification": 20,
      "screening": 15,
      "eligibility": 8,
      "included": 3
    }
  },

  "selected_articles": [
    {
      "pmid": "38901234",
      "title": "DAPA-CKD: Dapagliflozin in Patients with CKD...",
      "journal": "NEJM",
      "year": 2024,
      "study_type": "RCT",
      "sample_size": 4304,
      "selection_reason": "最大型的 SGLT2i 在 CKD 的 RCT，PICO 完全符合"
    }
  ],

  "appraisal": {
    "tool": "CASP RCT Checklist",
    "questions": [
      {
        "number": 1,
        "question": "Did the study address a clearly focused research question?",
        "answer": "Yes",
        "evidence": "Methods, p.2: The study aimed to evaluate...",
        "analysis": "研究問題明確，以 PICO 結構呈現"
      }
    ],
    "summary": {
      "validity": "通過",
      "results": "結果精確",
      "applicability": "適用",
      "overall": "值得信賴",
      "ocebm_level": "Level 2"
    },
    "coi_check": {
      "funding": "AstraZeneca 資助",
      "author_affiliations": "部分作者為 AstraZeneca 員工",
      "disclosure": "完整揭露",
      "judgment": "有 COI 但已適當揭露"
    }
  },

  "application": {
    "ocebm_level": "Level 2",
    "local_considerations": "台灣健保已給付 Dapagliflozin 用於 CKD...",
    "clinical_reply": "根據目前最好的證據，使用 Dapagliflozin 可以...",
    "sdm_notes": null,
    "cost_analysis": null
  },

  "self_assessment": {
    "clinical_question": "問題明確且與臨床直接相關",
    "search_quality": "使用多資料庫搜尋，搜尋策略完整",
    "search_skills": "正確使用 MeSH terms 和布林邏輯",
    "clinical_application": "已考慮台灣在地因素",
    "behavior_change": "計畫在後續照護中考慮使用 SGLT2i"
  },

  "template_style": "formal"
}
```

## 欄位說明

| 欄位 | 類型 | 必要 | 說明 |
|------|------|------|------|
| `version` | string | 是 | Schema 版本，目前為 "1.0" |
| `created` | string | 是 | 首次建立日期（YYYY-MM-DD） |
| `updated` | string | 是 | 最後更新日期（YYYY-MM-DD） |
| `current_step` | string | 是 | 目前步驟：TOPIC / ASK / ACQUIRE / APPRAISE / APPLY / AUDIT / SLIDES |
| `department` | object / null | 否 | 科別資訊 |
| `topic` | string / null | 否 | 報告主題 |
| `clinical_scenario` | string / null | 否 | 臨床情境描述 |
| `pico` | object / null | 否 | PICO 各元素 |
| `classification` | object / null | 否 | 問題分類結果 |
| `search_strategy` | object / null | 否 | 搜尋策略與結果 |
| `selected_articles` | array / null | 否 | 選定文獻列表 |
| `appraisal` | object / null | 否 | 評讀結果 |
| `application` | object / null | 否 | 臨床應用 |
| `self_assessment` | object / null | 否 | 自我評估 |
| `template_style` | string / null | 否 | 簡報風格：formal / clean / teaching / competition |

## 步驟對應

| `current_step` 值 | 對應 `/ebm` 的步驟 | 說明 |
|---|---|---|
| `TOPIC` | Step 1-3 | 選科選題階段 |
| `ASK` | Step 4-7 | PICO、情境、背景、分類 |
| `ACQUIRE` | Step 8-9 | 文獻搜尋、選文 |
| `APPRAISE` | Step 10-12 | 評讀工具、逐題評讀、結果 |
| `APPLY` | Step 13-15 | 證據等級、應用、回覆 |
| `AUDIT` | Step 16 | 自我評估 |
| `SLIDES` | Step 17 | 簡報產生 |
