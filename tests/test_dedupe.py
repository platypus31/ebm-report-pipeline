"""Tests for dedupe_results.py — deduplication logic."""

from scripts.dedupe_results import _tokenize, dedupe, normalize_title, title_similarity


class TestNormalizeTitle:
    def test_basic_normalization(self):
        assert normalize_title("  Hello World!  ") == "hello world"

    def test_preserves_cjk(self):
        result = normalize_title("SGLT2抑制劑對慢性腎臟病的療效")
        assert "sglt2" in result
        assert "慢性腎臟病" in result

    def test_empty_string(self):
        assert normalize_title("") == ""


class TestTokenize:
    def test_english_words(self):
        tokens = _tokenize("hello world test")
        assert "hello" in tokens
        assert "world" in tokens

    def test_cjk_bigrams(self):
        tokens = _tokenize("慢性腎臟病")
        assert "慢性" in tokens
        assert "性腎" in tokens
        assert "腎臟" in tokens
        assert "臟病" in tokens

    def test_mixed_content(self):
        tokens = _tokenize("SGLT2i 在 CKD 合併糖尿病")
        assert "sglt2i" in tokens
        assert "ckd" in tokens
        assert "糖尿" in tokens


class TestTitleSimilarity:
    def test_identical(self):
        assert title_similarity("hello world", "hello world") == 1.0

    def test_completely_different(self):
        assert title_similarity("hello", "goodbye") == 0.0

    def test_partial_overlap(self):
        sim = title_similarity("hello world test", "hello world foo")
        assert 0.3 < sim < 0.8

    def test_empty_strings(self):
        assert title_similarity("", "") == 0.0
        assert title_similarity("hello", "") == 0.0

    def test_cjk_similarity(self):
        a = "SGLT2抑制劑對慢性腎臟病的療效分析"
        b = "SGLT2抑制劑對慢性腎臟病的療效研究"
        sim = title_similarity(a, b)
        assert sim > 0.6  # High overlap despite different last 2 chars


class TestDedupe:
    def test_no_duplicates(self):
        rows = [
            {"pmid": "1", "doi": "", "title": "Article A"},
            {"pmid": "2", "doi": "", "title": "Article B"},
        ]
        kept, removed = dedupe(rows)
        assert len(kept) == 2
        assert len(removed) == 0

    def test_pmid_duplicate(self):
        rows = [
            {"pmid": "123", "doi": "", "title": "Article A"},
            {"pmid": "123", "doi": "", "title": "Article A copy"},
        ]
        kept, removed = dedupe(rows)
        assert len(kept) == 1
        assert len(removed) == 1
        assert "PMID" in removed[0]["_dedupe_reason"]

    def test_doi_duplicate(self):
        rows = [
            {"pmid": "1", "doi": "10.1234/test", "title": "Article A"},
            {"pmid": "2", "doi": "10.1234/TEST", "title": "Different title"},
        ]
        kept, removed = dedupe(rows)
        assert len(kept) == 1
        assert "DOI" in removed[0]["_dedupe_reason"]

    def test_title_similarity_duplicate(self):
        rows = [
            {"pmid": "1", "doi": "", "title": "Effect of SGLT2 inhibitors on CKD outcomes"},
            {"pmid": "2", "doi": "", "title": "Effect of SGLT2 inhibitors on CKD outcomes: a review"},
        ]
        kept, removed = dedupe(rows, threshold=0.7)
        assert len(kept) == 1

    def test_empty_rows(self):
        kept, removed = dedupe([])
        assert kept == []
        assert removed == []

    def test_missing_fields(self):
        rows = [{"title": "Only title"}, {"title": "Only title too"}]
        kept, removed = dedupe(rows)
        assert len(kept) == 2  # No PMID/DOI, different titles
