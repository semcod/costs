from scripts.audit_consumers import scan


def test_constraints_locks_and_installed_versions_are_separate(tmp_path):
    repo = tmp_path / "demo"
    (repo / ".git").mkdir(parents=True)
    manifest = repo / "pyproject.toml"
    manifest.write_text(
        '[project]\nname="demo"\ndependencies=["costs>=0.1.53"]\n'
        '[project.optional-dependencies]\ncosts=["costs"]\n'
    )
    lock = repo / "uv.lock"
    lock.write_text('[[package]]\nname="costs"\nversion="0.1.53"\n')
    script = repo / "project.sh"
    script.write_text("python -m pip install --upgrade costs\n")
    metadata = (
        repo / ".venv/lib/python3.13/site-packages/costs-0.1.51.dist-info/METADATA"
    )
    metadata.parent.mkdir(parents=True)
    metadata.write_text("Name: costs\nVersion: 0.1.51\n")
    result = scan([manifest, lock, script], tmp_path, "0.1.100")
    assert result["errors"] == []
    project = result["projects"]["demo"]
    assert len(project["declarations"]) == 2
    assert all(d["allows_latest"] for d in project["declarations"])
    assert project["locked_versions"][0]["version"] == "0.1.53"
    assert project["installed"][0]["latest"] is False
    assert project["has_explicit_upgrade_command"] is True


def test_pinned_requirements_do_not_allow_highest_version(tmp_path):
    manifest = tmp_path / "requirements.txt"
    manifest.write_text("costs==0.1.99\n")
    result = scan([manifest], tmp_path, "0.1.100")
    assert result["projects"]["."]["declarations"][0]["allows_latest"] is False
