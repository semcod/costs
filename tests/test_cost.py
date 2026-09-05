"""Tests for AI Cost Tracker with automatic badge generation."""

import subprocess
import sys
from pathlib import Path


def test_placeholder():
    """Placeholder test to verify the test setup works."""
    assert True


def test_import():
    """Verify the main package can be imported."""
    from src.costs import cli  # noqa: F401


def test_cli_version_matches_package():
    from typer.testing import CliRunner
    from src.costs import __version__
    from src.costs.cli import app

    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == f"costs {__version__}"


def test_aicost_auto_badge(tmp_path):
    """Exercise the current checkout against an isolated repository."""
    import os
    import git

    repo = git.Repo.init(tmp_path)
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "1.0.0"\n'
        '[tool.costs]\ndefault_model = "claude-3.5-sonnet"\n'
        "badge = true\nupdate_readme = true\n",
        encoding="utf-8",
    )
    repo.index.add(["README.md", "pyproject.toml"])
    actor = git.Actor("Test", "test@example.invalid")
    repo.index.commit("[ai:test] initial", author=actor, committer=actor)
    repo_root = Path(__file__).parent.parent
    env = {**os.environ, "PYTHONPATH": str(repo_root / "src")}
    for name in ("OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "SAAS_TOKEN", "LLM_MODEL"):
        env.pop(name, None)
    result = subprocess.run(
        [sys.executable, "-m", "costs.cli", "auto-badge", "--repo", str(tmp_path)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "AI Cost" in (tmp_path / "README.md").read_text()


def test_cost_calculator_imports():
    """Test that cost calculator module can be imported and basic functions work."""
    from src.costs.calculator import ai_cost, batch_calculate_costs
    from src.costs.git_parser import parse_commits

    # Verify functions exist
    assert callable(ai_cost)
    assert callable(batch_calculate_costs)
    assert callable(parse_commits)


def test_reports_module():
    """Test that reports module can be imported."""
    from src.costs.reports import generate_markdown_report, update_readme_badge

    assert callable(generate_markdown_report)
    assert callable(update_readme_badge)


def test_readme_badge_uses_summary_version(tmp_path, monkeypatch):
    """README version badge must use the analyzed project's full version."""
    from src.costs import git_parser
    from src.costs.reports import update_readme_badge

    monkeypatch.setattr(git_parser, "parse_commits", lambda *args, **kwargs: [])
    (tmp_path / "README.md").write_text(
        "# Demo\n\n"
        "## AI Cost Tracking\n\n"
        "![Version](https://img.shields.io/badge/version-0.1.31-blue)\n\n"
        "---\n\n",
        encoding="utf-8",
    )

    updated = update_readme_badge(
        tmp_path,
        {
            "summary": {
                "model": "openrouter/deep/deep-v4-pro",
                "total_cost": 1.23,
                "total_cost_formatted": "$1.2300",
                "total_commits": 7,
                "version": "0.1.351",
            }
        },
    )

    content = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert updated is True
    assert "version-0.1.351-blue" in content
    assert "version-0.1.31-blue" not in content


def test_readme_badge_falls_back_to_project_version_file(tmp_path, monkeypatch):
    """Badge generation should not fall back to a hardcoded package version."""
    from src.costs import git_parser
    from src.costs.reports import update_readme_badge

    monkeypatch.setattr(git_parser, "parse_commits", lambda *args, **kwargs: [])
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "VERSION").write_text("2.4.68\n", encoding="utf-8")

    updated = update_readme_badge(
        tmp_path,
        {
            "summary": {
                "model": "openrouter/deep/deep-v4-pro",
                "total_cost": 1.23,
                "total_cost_formatted": "$1.2300",
                "total_commits": 7,
            }
        },
    )

    content = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert updated is True
    assert "version-2.4.68-blue" in content
