"""Tests for build_search_query.py — PubMed query construction."""

from scripts.build_search_query import build_query


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
        query = build_query(pico_data)
        assert "Primary Outcome" in query

    def test_explicit_type_overrides_classification(self):
        pico_data = {
            "pico": {"p": {"mesh": "Test[MeSH]"}},
            "classification": {"type": "therapeutic"},
        }
        query = build_query(pico_data, q_type="diagnostic")
        assert "Sensitivity and Specificity" in query
        assert "Randomized Controlled Trial" not in query
