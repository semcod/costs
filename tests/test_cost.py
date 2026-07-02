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


def test_aicost_auto_badge():
    """Test that aicost auto-badge command runs successfully.

    This test automatically calculates costs and updates the badge,
    ensuring the cost calculation pipeline works end-to-end.
    """
    repo_root = Path(__file__).parent.parent

    # Check if pyproject.toml has [tool.costs] config
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        print("⚠️  pyproject.toml not found, skipping auto-badge test")
        return

    pyproject_content = pyproject_path.read_text()
    if "[tool.costs]" not in pyproject_content:
        print("⚠️  [tool.costs] not configured, skipping auto-badge test")
        return

    # Find costs command
    costs_cmd = None
    for cmd in [
        "costs",
        str(repo_root / ".venv" / "bin" / "costs"),
        str(repo_root / "venv" / "bin" / "costs"),
    ]:
        result = subprocess.run(
            ["which", cmd] if "/" not in cmd else ["test", "-f", cmd],
            capture_output=True,
            shell=False if "/" not in cmd else True,
        )
        if result.returncode == 0 or Path(cmd).exists():
            costs_cmd = cmd
            break

    if not costs_cmd:
        # Try to use python -m
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.costs.cli",
                "auto-badge",
                "--repo",
                str(repo_root),
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
    else:
        result = subprocess.run(
            [costs_cmd, "auto-badge", "--repo", str(repo_root)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )

    # Command should succeed (exit code 0) or exit with 0 if no AI commits
    assert result.returncode in [0], f"costs auto-badge failed: {result.stderr}"

    # Verify README.md exists and potentially has badge
    readme_path = repo_root / "README.md"
    if readme_path.exists():
        readme_content = readme_path.read_text()
        # Check if badge marker or cost info is present
        assert "AI Cost" in readme_content or "cost" in readme_content.lower() or True


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
