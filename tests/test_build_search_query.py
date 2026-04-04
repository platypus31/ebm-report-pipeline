"""Tests for build_search_query.py — PubMed query construction."""

from scripts.build_search_query import (
    _split_mesh_terms,
    build_eutils_url,
    build_query,
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
