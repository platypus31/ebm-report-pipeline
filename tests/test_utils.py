"""Tests for scripts/utils.py — shared utilities."""

from pathlib import Path

from scripts.utils import _parse_yaml_fallback, file_has_content, read_yaml


class TestReadYaml:
    def test_nonexistent_file(self):
        result = read_yaml(Path("/nonexistent/path.yaml"))
        assert result == {}

    def test_simple_yaml(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text('topic: "hello"\nversion: "1.0"\n')
        result = read_yaml(f)
        assert result["topic"] == "hello"
        assert result["version"] == "1.0"

    def test_nested_yaml(self, tmp_path):
        f = tmp_path / "pico.yaml"
        f.write_text(
            "pico:\n"
            "  p:\n"
            '    zh: "高血壓患者"\n'
            '    mesh: "Hypertension"\n'
            "  i:\n"
            '    zh: "SGLT2 抑制劑"\n'
            '    mesh: "SGLT2 Inhibitors"\n'
        )
        result = read_yaml(f)
        assert result["pico"]["p"]["zh"] == "高血壓患者"
        assert result["pico"]["i"]["mesh"] == "SGLT2 Inhibitors"

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.yaml"
        f.write_text("")
        result = read_yaml(f)
        assert result == {}

    def test_malformed_yaml(self, tmp_path):
        f = tmp_path / "bad.yaml"
        f.write_text("{{{{invalid yaml content")
        result = read_yaml(f)
        assert isinstance(result, dict)


class TestFallbackParser:
    def test_nested_pico(self, tmp_path):
        f = tmp_path / "pico.yaml"
        f.write_text(
            "# PICO 分析\n"
            "topic: 'SGLT2i in CKD'\n"
            "\n"
            "pico:\n"
            "  p:\n"
            '    zh: "CKD 患者"\n'
            '    mesh: "Renal Insufficiency, Chronic"\n'
            "  i:\n"
            '    zh: "SGLT2 抑制劑"\n'
            '    mesh: "Sodium-Glucose Transporter 2 Inhibitors"\n'
            "  c:\n"
            '    zh: "安慰劑"\n'
            '    mesh: "Placebos"\n'
            "  o:\n"
            "    primary:\n"
            '      zh: "eGFR 變化"\n'
            '      mesh: "Glomerular Filtration Rate"\n'
        )
        result = _parse_yaml_fallback(f)
        assert result["topic"] == "SGLT2i in CKD"
        assert result["pico"]["p"]["zh"] == "CKD 患者"
        assert result["pico"]["o"]["primary"]["zh"] == "eGFR 變化"

    def test_list_value(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text("mesh_terms: []\n")
        result = _parse_yaml_fallback(f)
        assert result["mesh_terms"] == []


class TestFileHasContent:
    def test_nonexistent(self, tmp_path):
        assert not file_has_content(tmp_path / "nope.txt")

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        assert not file_has_content(f)

    def test_small_file(self, tmp_path):
        f = tmp_path / "small.txt"
        f.write_text("hi")
        assert not file_has_content(f)

    def test_file_with_content(self, tmp_path):
        f = tmp_path / "content.txt"
        f.write_text("This is meaningful content for an EBM report step.")
        assert file_has_content(f)
