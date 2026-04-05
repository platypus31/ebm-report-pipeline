"""Tests for build_search_query.py — PubMed query construction."""

from scripts.build_search_query import (
    PUB_FILTER_CHAIN,
    _expand_mesh_term,
    _resolve_pub_filter,
    _split_mesh_terms,
    build_eutils_url,
    build_query,
    build_query_chain,
    lookup_department_mesh,
    parse_departments,
)


class TestSplitMeshTerms:
    def test_single_term(self):
        result = _split_mesh_terms('"Hypertension"[MeSH]')
        assert result == ['"Hypertension"[MeSH]']

    def test_comma_separated(self):
        result = _split_mesh_terms('"GFR"[MeSH], "Kidney Failure"[MeSH]')
        assert len(result) == 2
        assert '"GFR"[MeSH]' in result
        assert '"Kidney Failure"[MeSH]' in result

    def test_with_and_operator(self):
        result = _split_mesh_terms('"Term A"[MeSH] AND "Term B"[MeSH]')
        assert len(result) == 1  # Keep as-is, user structured it

    def test_empty(self):
        assert _split_mesh_terms("") == []


class TestBuildQuery:
    def test_basic_pico(self):
        pico_data = {
            "pico": {
                "p": {"mesh": "Renal Insufficiency, Chronic[MeSH]"},
                "i": {"mesh": "Sodium-Glucose Transporter 2 Inhibitors[MeSH]"},
                "c": {"mesh": "Placebos[MeSH]"},
                "o": {"primary": {"mesh": "Glomerular Filtration Rate[MeSH]"}},
            }
        }
        query = build_query(pico_data)
        assert "Renal Insufficiency" in query
        assert "Sodium-Glucose" in query
        assert "Placebos" in query
        assert "Glomerular Filtration Rate" in query

    def test_with_type_filter(self):
        pico_data = {
            "pico": {
                "p": {"mesh": "Hypertension[MeSH]"},
                "i": {"mesh": "Drug X[MeSH]"},
                "c": {},
                "o": {},
            },
            "classification": {"type": "therapeutic"},
        }
        query = build_query(pico_data)
        assert "Randomized Controlled Trial" in query

    def test_empty_pico(self):
        pico_data = {"pico": {}}
        query = build_query(pico_data)
        assert query == ""

    def test_nested_outcome(self):
        pico_data = {
            "pico": {
                "p": {"mesh": "Test[MeSH]"},
                "i": {},
                "c": {},
                "o": {
                    "primary": {"mesh": "Primary Outcome[MeSH]"},
                    "secondary": {"mesh": "Secondary Outcome[MeSH]"},
                },
            }
        }
        query = build_query(pico_data, include_secondary=True)
        assert "Primary Outcome" in query
        assert "Secondary Outcome" in query

    def test_no_secondary(self):
        pico_data = {
            "pico": {
                "p": {"mesh": "Test[MeSH]"},
                "o": {
                    "primary": {"mesh": "Primary[MeSH]"},
                    "secondary": {"mesh": "Secondary[MeSH]"},
                },
            }
        }
        query = build_query(pico_data, include_secondary=False)
        assert "Primary" in query
        assert "Secondary" not in query

    def test_explicit_type_overrides_classification(self):
        pico_data = {
            "pico": {"p": {"mesh": "Test[MeSH]"}},
            "classification": {"type": "therapeutic"},
        }
        query = build_query(pico_data, q_type="diagnostic")
        assert "Sensitivity and Specificity" in query
        assert "Randomized Controlled Trial" not in query

    def test_comma_separated_mesh_becomes_or(self):
        pico_data = {
            "pico": {
                "p": {"mesh": "Test[MeSH]"},
                "o": {
                    "primary": {"mesh": '"GFR"[MeSH], "Kidney Failure"[MeSH]'},
                },
            }
        }
        query = build_query(pico_data)
        assert "OR" in query
        assert '"GFR"[MeSH]' in query
        assert '"Kidney Failure"[MeSH]' in query

    def test_years_filter(self):
        pico_data = {"pico": {"p": {"mesh": "Test[MeSH]"}}}
        query = build_query(pico_data, years=5)
        assert '"5 years"[dp]' in query

    def test_lang_filter_en(self):
        pico_data = {"pico": {"p": {"mesh": "Test[MeSH]"}}}
        query = build_query(pico_data, lang="en")
        assert "English[lang]" in query

    def test_lang_filter_zh(self):
        pico_data = {"pico": {"p": {"mesh": "Test[MeSH]"}}}
        query = build_query(pico_data, lang="zh")
        assert "Chinese[lang]" in query
        assert "English[lang]" in query

    def test_no_filters(self):
        pico_data = {"pico": {"p": {"mesh": "Test[MeSH]"}}}
        query = build_query(pico_data, years=0, lang="")
        assert "years" not in query
        assert "lang" not in query


class TestFallbackChain:
    """Verify the tier-based fallback chain for each question type."""

    def _query(self, q_type, tier=0):
        return build_query({"pico": {"p": {"mesh": "Test[MeSH]"}}}, q_type=q_type, tier=tier)

    # ── Tier 0: strictest (highest evidence) ──

    def test_therapeutic_tier0_has_rct_ma_sr(self):
        q = self._query("therapeutic", tier=0)
        assert "Randomized Controlled Trial[pt]" in q
        assert "Meta-Analysis[pt]" in q
        assert "Systematic Review[pt]" in q
        assert "Case-Control" not in q

    def test_preventive_tier0_has_rct_ma_sr(self):
        q = self._query("preventive", tier=0)
        assert "Randomized Controlled Trial[pt]" in q
        assert "Case-Control" not in q

    def test_diagnostic_tier0_has_prospective_gold_standard(self):
        q = self._query("diagnostic", tier=0)
        assert "Prospective Studies[MeSH]" in q
        assert "Reference Standards[MeSH]" in q
        assert "Sensitivity and Specificity[MeSH]" in q
        assert "Systematic Review[pt]" in q
        assert "Meta-Analysis[pt]" in q

    def test_prognostic_tier0_has_cohort(self):
        q = self._query("prognostic", tier=0)
        assert "Cohort Studies[MeSH]" in q
        assert "Systematic Review[pt]" in q
        assert "Case-Control" not in q

    def test_etiology_tier0_has_cohort(self):
        q = self._query("etiology_harm", tier=0)
        assert "Cohort Studies[MeSH]" in q
        assert "Systematic Review[pt]" in q
        assert "Case-Control" not in q

    # ── Tier 1: relaxed ──

    def test_therapeutic_tier1_adds_cohort(self):
        q = self._query("therapeutic", tier=1)
        assert "Randomized Controlled Trial[pt]" in q  # tier 0 included
        assert "Cohort Studies[MeSH]" in q  # tier 1 added

    def test_diagnostic_tier1_adds_cross_sectional(self):
        q = self._query("diagnostic", tier=1)
        assert "Cross-Sectional Studies[MeSH]" in q

    def test_prognostic_tier1_adds_case_control(self):
        q = self._query("prognostic", tier=1)
        assert "Cohort Studies[MeSH]" in q  # tier 0
        assert "Case-Control Studies[MeSH]" in q  # tier 1

    def test_etiology_tier1_adds_case_control(self):
        q = self._query("etiology_harm", tier=1)
        assert "Cohort Studies[MeSH]" in q  # tier 0
        assert "Case-Control Studies[MeSH]" in q  # tier 1
        assert "Risk Factors[MeSH]" in q

    # ── Tier 2: broadest ──

    def test_therapeutic_tier2_adds_case_control(self):
        q = self._query("therapeutic", tier=2)
        assert "Case-Control Studies[MeSH]" in q
        assert "Observational Study[pt]" in q

    def test_prognostic_tier2_adds_case_reports(self):
        q = self._query("prognostic", tier=2)
        assert "Case Reports[pt]" in q

    # ── Chain structure ──

    def test_all_types_have_3_tiers(self):
        for q_type in PUB_FILTER_CHAIN:
            assert len(PUB_FILTER_CHAIN[q_type]) == 3, f"{q_type} should have 3 tiers"

    def test_all_tier0_have_sr_and_ma(self):
        for q_type in PUB_FILTER_CHAIN:
            tier0 = PUB_FILTER_CHAIN[q_type][0]
            assert "Systematic Review[pt]" in tier0, f"{q_type} tier 0 missing SR"
            assert "Meta-Analysis[pt]" in tier0, f"{q_type} tier 0 missing MA"

    # ── _resolve_pub_filter ──

    def test_resolve_tier0(self):
        f = _resolve_pub_filter("therapeutic", 0)
        assert f == PUB_FILTER_CHAIN["therapeutic"][0]

    def test_resolve_tier1_merges(self):
        f = _resolve_pub_filter("therapeutic", 1)
        # Should contain both tier 0 and tier 1 content
        assert "Randomized Controlled Trial[pt]" in f
        assert "Cohort Studies[MeSH]" in f

    def test_resolve_unknown_type(self):
        assert _resolve_pub_filter("unknown_type", 0) == ""

    # ── build_query_chain ──

    def test_build_query_chain_returns_all_tiers(self):
        pico_data = {
            "pico": {"p": {"mesh": "Test[MeSH]"}},
            "classification": {"type": "therapeutic"},
        }
        chain = build_query_chain(pico_data)
        assert len(chain) == 3
        assert chain[0]["tier"] == 0
        assert chain[1]["tier"] == 1
        assert chain[2]["tier"] == 2
        assert all("label" in item for item in chain)
        assert all("query" in item for item in chain)

    def test_chain_tier0_is_strictest(self):
        pico_data = {
            "pico": {"p": {"mesh": "Test[MeSH]"}},
            "classification": {"type": "prognostic"},
        }
        chain = build_query_chain(pico_data)
        # Tier 0 should NOT contain Case-Control
        assert "Case-Control" not in chain[0]["query"]
        # Tier 1 should contain Case-Control
        assert "Case-Control" in chain[1]["query"]

    def test_chain_no_type_returns_single(self):
        pico_data = {"pico": {"p": {"mesh": "Test[MeSH]"}}}
        chain = build_query_chain(pico_data)
        assert len(chain) == 1  # no q_type → no filter chain, just base query


class TestExpandMeshTerm:
    def test_quoted_mesh(self):
        result = _expand_mesh_term('"Kidney Diseases"[MeSH]')
        assert '"Kidney Diseases"[MeSH]' in result
        assert '"Kidney Diseases"[tiab]' in result
        assert result.startswith("(")
        assert " OR " in result

    def test_unquoted_mesh(self):
        result = _expand_mesh_term("Kidney Diseases[MeSH]")
        assert '"Kidney Diseases"[MeSH]' in result
        assert '"Kidney Diseases"[tiab]' in result

    def test_non_mesh_unchanged(self):
        result = _expand_mesh_term("some free text")
        assert result == "some free text"

    def test_tiab_term_unchanged(self):
        result = _expand_mesh_term('"Test"[tiab]')
        assert result == '"Test"[tiab]'


class TestBuildQueryExpand:
    def test_expand_single_term(self):
        pico_data = {"pico": {"p": {"mesh": "Hypertension[MeSH]"}}}
        query = build_query(pico_data, expand=True)
        assert "[tiab]" in query
        assert "[MeSH]" in query

    def test_no_expand_by_default(self):
        pico_data = {"pico": {"p": {"mesh": "Hypertension[MeSH]"}}}
        query = build_query(pico_data)
        assert "[tiab]" not in query

    def test_expand_multiple_terms(self):
        pico_data = {
            "pico": {
                "p": {"mesh": '"Term A"[MeSH]'},
                "i": {"mesh": '"Term B"[MeSH]'},
            }
        }
        query = build_query(pico_data, expand=True)
        assert '"Term A"[tiab]' in query
        assert '"Term B"[tiab]' in query

    def test_expand_comma_separated(self):
        pico_data = {
            "pico": {
                "p": {"mesh": "Test[MeSH]"},
                "o": {"primary": {"mesh": '"GFR"[MeSH], "Kidney Failure"[MeSH]'}},
            }
        }
        query = build_query(pico_data, expand=True)
        assert '"GFR"[tiab]' in query
        assert '"Kidney Failure"[tiab]' in query


class TestDepartmentIntegration:
    def test_parse_departments(self):
        depts = parse_departments()
        assert "NEPH" in depts
        assert "腎臟內科" in depts
        assert "Nephrology" in depts
        assert depts["NEPH"]["zh"] == "腎臟內科"
        assert len(depts["NEPH"]["mesh_terms"]) >= 1

    def test_parse_departments_case_insensitive(self):
        depts = parse_departments()
        assert "neph" in depts
        assert "nephrology" in depts

    def test_lookup_by_abbr(self):
        terms = lookup_department_mesh("NEPH")
        assert len(terms) >= 1
        assert any("Kidney" in t for t in terms)

    def test_lookup_by_chinese(self):
        terms = lookup_department_mesh("腎臟內科")
        assert len(terms) >= 1

    def test_lookup_by_english(self):
        terms = lookup_department_mesh("Nephrology")
        assert len(terms) >= 1

    def test_lookup_not_found(self):
        terms = lookup_department_mesh("不存在的科別")
        assert terms == []

    def test_dept_mesh_in_query(self):
        pico_data = {"pico": {"p": {"mesh": "Test[MeSH]"}}}
        dept_mesh = ['"Kidney Diseases"[MeSH]', '"Renal Dialysis"[MeSH]']
        query = build_query(pico_data, dept_mesh=dept_mesh)
        assert "Kidney Diseases" in query
        assert "Renal Dialysis" in query
        assert "Test" in query

    def test_dept_mesh_from_pico_yaml(self):
        pico_data = {
            "department": {"mesh_terms": ["Kidney Diseases", "Renal Dialysis"]},
            "pico": {"p": {"mesh": "Test[MeSH]"}},
        }
        query = build_query(pico_data)
        assert "Kidney Diseases" in query
        assert "Renal Dialysis" in query

    def test_dept_mesh_with_expand(self):
        pico_data = {"pico": {}}
        dept_mesh = ['"Kidney Diseases"[MeSH]']
        query = build_query(pico_data, dept_mesh=dept_mesh, expand=True)
        assert '"Kidney Diseases"[tiab]' in query
        assert '"Kidney Diseases"[MeSH]' in query

    def test_explicit_dept_mesh_overrides_pico_yaml(self):
        pico_data = {
            "department": {"mesh_terms": ["Should Not Appear"]},
            "pico": {"p": {"mesh": "Test[MeSH]"}},
        }
        dept_mesh = ['"Actual Dept"[MeSH]']
        query = build_query(pico_data, dept_mesh=dept_mesh)
        assert "Actual Dept" in query
        assert "Should Not Appear" not in query

    def test_department_only_mode(self):
        """Department-only query without any PICO data."""
        dept_mesh = ['"Heart Diseases"[MeSH]', '"Cardiovascular Diseases"[MeSH]']
        query = build_query({}, dept_mesh=dept_mesh, years=3, lang="en")
        assert "Heart Diseases" in query
        assert "Cardiovascular Diseases" in query
        assert '"3 years"[dp]' in query
        assert "English[lang]" in query


class TestBuildEutilsUrl:
    def test_basic_url(self):
        url = build_eutils_url("Test[MeSH]")
        assert "eutils.ncbi.nlm.nih.gov" in url
        assert "Test" in url
        assert "retmax=100" in url

    def test_custom_retmax(self):
        url = build_eutils_url("Test[MeSH]", retmax=50)
        assert "retmax=50" in url

    def test_complex_query(self):
        query = '("Term A"[MeSH]) AND ("Term B"[MeSH])'
        url = build_eutils_url(query)
        assert "eutils.ncbi.nlm.nih.gov" in url
