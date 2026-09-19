import importlib.util
from pathlib import Path

import yaml

spec = importlib.util.spec_from_file_location("revalidation", Path(__file__).parents[1] / "scripts/revalidate_docval_backlog.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_preserves_occurrences_and_unscanned_records(tmp_path):
    (tmp_path / "README.md").write_text("# Same\n\nbody\n")
    def ticket(heading="Same", file="README.md", status="open"):
        return dict(title="Fix: " + heading, status=status,
                    source=dict(file="/home/tom/github/semcod/costs/" + file, issue_type="bad_link"))
    data = dict(tickets={"DOC-001": ticket(), "DOC-002": ticket(),
                         "DOC-003": ticket("Gone"), "DOC-004": ticket(file="missing.md"),
                         "DOC-005": ticket(status="done")})
    report = dict(files=[dict(path="README.md", chunks=[dict(heading="Same", lines="1-3", issues=[dict(rule="bad_link")])])])
    text = yaml.safe_dump(data, sort_keys=False)
    result, records = module.reconcile(text, report, tmp_path, "a" * 40, "b" * 64)
    parsed = yaml.safe_load(result)["tickets"]
    assert [parsed[f"DOC-00{i}"]["status"] for i in range(1, 6)] == ["open", "open", "done", "open", "done"]
    assert records["DOC-001"]["locations"] == records["DOC-002"]["locations"] == ["1-3"]
    assert "revalidation" not in parsed["DOC-004"]
    assert parsed["DOC-005"] == data["tickets"]["DOC-005"]
    repeated, _ = module.reconcile(result, report, tmp_path, "a" * 40, "b" * 64)
    assert repeated == result


def test_empty_or_missing_scan_never_closes_ticket(tmp_path):
    (tmp_path / "README.md").write_text("# Heading")
    text = "tickets:\n  DOC-001:\n    title: 'Fix: Heading'\n    status: open\n    source:\n      file: README.md\n      issue_type: empty\n"
    for files in ([], [dict(path="README.md", chunks=[])]):
        result, records = module.reconcile(text, dict(files=files), tmp_path, "a" * 40, "b" * 64)
        assert result == text and records == {}
