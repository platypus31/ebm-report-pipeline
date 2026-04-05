# 各問題類型的證據層級與搜尋策略

搜尋策略採用 **Fallback Chain**（逐層放寬）：先用最嚴格的 filter 搜尋最高證據等級，
結果不足時逐層放寬，納入較低證據等級的研究設計。

---

## 治療型 (Therapeutic)

**最佳證據層級：**
1. Systematic Review / Meta-analysis of RCTs
2. Individual RCT
3. Cohort study
4. Case-control study
5. Case series / Case report
6. Expert opinion

**Fallback Chain:**

| Tier | 證據等級 | PubMed filter |
|------|---------|---------------|
| 0 (優先) | SR/MA + RCT | `Meta-Analysis[pt] OR Systematic Review[pt] OR Randomized Controlled Trial[pt]` |
| 1 (放寬) | + Controlled Trial + Cohort | `Controlled Clinical Trial[pt] OR Cohort Studies[MeSH]` |
| 2 (最寬) | + Case-Control + Observational | `Case-Control Studies[MeSH] OR Observational Study[pt]` |

---

## 預防型 (Preventive)

**最佳證據層級：**
1. Systematic Review / Meta-analysis of RCTs
2. Individual RCT
3. Cohort study
4. Case-control study
5. Case series / Case report
6. Expert opinion

**Fallback Chain:**

| Tier | 證據等級 | PubMed filter |
|------|---------|---------------|
| 0 (優先) | SR/MA + RCT | `Meta-Analysis[pt] OR Systematic Review[pt] OR Randomized Controlled Trial[pt]` |
| 1 (放寬) | + Controlled Trial + Cohort | `Controlled Clinical Trial[pt] OR Cohort Studies[MeSH]` |
| 2 (最寬) | + Case-Control + Observational | `Case-Control Studies[MeSH] OR Observational Study[pt]` |

---

## 診斷型 (Diagnostic)

**最佳證據層級：**
1. Systematic Review / Meta-analysis of prospective blind comparison studies
2. Prospective, blind comparison with gold standard (reference standard)
3. Retrospective study with consistent reference standard
4. Case-control study
5. Case series

**Fallback Chain:**

| Tier | 證據等級 | PubMed filter |
|------|---------|---------------|
| 0 (優先) | SR/MA + Prospective Blind + Gold Standard | `Systematic Review[pt] OR Meta-Analysis[pt] OR ((Sensitivity and Specificity[MeSH]) AND (Prospective Studies[MeSH] OR Cross-Sectional Studies[MeSH]) AND (Reference Standards[MeSH]))` |
| 1 (放寬) | + Cross-Sectional + Sensitivity/Specificity | `(Sensitivity and Specificity[MeSH]) OR (Cross-Sectional Studies[MeSH])` |
| 2 (最寬) | + Case-Control + Observational | `Case-Control Studies[MeSH] OR Observational Study[pt]` |

---

## 預後型 (Prognostic)

**最佳證據層級：**
1. Systematic Review / Meta-analysis of inception cohort studies
2. Inception cohort study
3. Cohort study (non-inception)
4. Case-control study
5. Case series

**Fallback Chain:**

| Tier | 證據等級 | PubMed filter |
|------|---------|---------------|
| 0 (優先) | SR/MA + Cohort | `Systematic Review[pt] OR Meta-Analysis[pt] OR Cohort Studies[MeSH] OR Prognosis[MeSH]` |
| 1 (放寬) | + Case-Control | `Case-Control Studies[MeSH]` |
| 2 (最寬) | + Observational + Case Reports | `Observational Study[pt] OR Case Reports[pt]` |

---

## 病因傷害型 (Etiology/Harm)

**最佳證據層級：**
1. Systematic Review / Meta-analysis of cohort studies
2. Individual cohort study
3. Case-control study
4. Case series
5. Case report

**Fallback Chain:**

| Tier | 證據等級 | PubMed filter |
|------|---------|---------------|
| 0 (優先) | SR/MA + Cohort | `Systematic Review[pt] OR Meta-Analysis[pt] OR Cohort Studies[MeSH]` |
| 1 (放寬) | + Case-Control + Risk Factors | `Case-Control Studies[MeSH] OR Risk Factors[MeSH]` |
| 2 (最寬) | + Observational + Case Reports | `Observational Study[pt] OR Case Reports[pt]` |

---

## 使用方式

```bash
# 只用最高證據等級搜尋（預設）
python3 scripts/build_search_query.py --project my-topic

# 指定放寬層級
python3 scripts/build_search_query.py --project my-topic --tier 1

# 顯示完整 fallback chain（所有層級）
python3 scripts/build_search_query.py --project my-topic --chain
```

程式化呼叫：
```python
from scripts.build_search_query import build_query, build_query_chain

# 單一層級
query_strict = build_query(pico_data, tier=0)  # 最嚴格
query_relaxed = build_query(pico_data, tier=1)  # 放寬

# 取得完整 chain
chain = build_query_chain(pico_data)
for item in chain:
    print(f"Tier {item['tier']} ({item['label']}): {item['query']}")
```
