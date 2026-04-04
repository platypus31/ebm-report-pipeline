"""Tests for generate_platform_config.py — cross-platform config generation."""

from scripts.generate_platform_config import PLATFORMS, generate_config


class TestGenerateConfig:
    def test_all_platforms_generate(self):
        for platform in PLATFORMS:
            content = generate_config(platform)
            assert len(content) > 100, f"{platform} config is too short"

    def test_claude_has_slash_commands(self):
        content = generate_config("claude")
        assert "/ebm" in content
        assert "/brainstorm" in content
        assert "/pico" in content

    def test_claude_has_mcp_section(self):
        content = generate_config("claude")
        assert "PubMed MCP" in content
        assert "Canva MCP" in content

    def test_gemini_has_gemini_cli_instructions(self):
        content = generate_config("gemini")
        assert "gemini" in content.lower()
        assert "skills/ebm.md" in content
        assert "/memory" in content

    def test_cursor_has_at_references(self):
        content = generate_config("cursor")
        assert "@skills/" in content

    def test_copilot_has_file_references(self):
        content = generate_config("copilot")
        assert "#file:skills/" in content

    def test_codex_has_agents_instructions(self):
        content = generate_config("codex")
        assert "codex" in content.lower() or "Codex" in content
        assert "skills/ebm.md" in content

    def test_all_platforms_have_shared_content(self):
        for platform in PLATFORMS:
            content = generate_config(platform)
            assert "EBM Report Pipeline" in content
            assert "5A" in content
            assert "PICO" in content
            assert "projects/<name>/" in content
            assert "init_project.py" in content
            assert "繁體中文" in content

    def test_non_claude_platforms_no_slash_triggers(self):
        for platform in ["gemini", "cursor", "copilot", "codex"]:
            content = generate_config(platform)
            # These platforms should not have Claude-style /command triggers
            assert "| `/ebm`" not in content

    def test_platform_filenames(self):
        assert PLATFORMS["claude"]["filename"] == "CLAUDE.md"
        assert PLATFORMS["gemini"]["filename"] == "GEMINI.md"
        assert PLATFORMS["cursor"]["filename"] == ".cursorrules"
        assert PLATFORMS["copilot"]["filename"] == ".github/copilot-instructions.md"
        assert PLATFORMS["codex"]["filename"] == "AGENTS.md"
