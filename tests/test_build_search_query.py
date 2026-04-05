"""Tests for build_search_query.py — PubMed query construction."""

from scripts.build_search_query import (
    _expand_mesh_term,
    _split_mesh_terms,
    build_eutils_url,
    build_query,
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
