"""Revalidate legacy DOC records without regenerating or renumbering the backlog.

The report argument is the output of a new scan, never an old report input.
Unmatched findings are superseded only in files covered by the scan. Matching
headings remain open, including ambiguous repeated headings. Severity is kept;
it is not evidence that a historical finding is currently urgent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

import yaml


def reconcile(text: str, report: dict, root: Path, head: str, report_hash: str):
    data = yaml.safe_load(text)
    files = {f["path"]: f for f in report["files"]}
    records = {}
    for ticket_id, ticket in data["tickets"].items():
        if not ticket_id.startswith("DOC-") or ticket.get("status") != "open":
            continue
        source = ticket.get("source", {})
        # Old exports contain absolute paths from the original checkout.
        old = str(source.get("file", ""))
        marker = "/costs/"
        relative = old.split(marker, 1)[1] if marker in old else old
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            continue
        scanned = files.get(relative)
        if (not scanned or scanned.get("status") == "error"
                or not scanned.get("chunks") or not (root / path).is_file()):
            continue
        heading = ticket.get("title", "").partition(": ")[2]
        rule = source.get("issue_type")
        if not heading or not rule:
            continue
        matches = [c for c in scanned["chunks"] if c.get("heading") == heading
                   and any(i.get("rule") == rule for i in c.get("issues", []))]
        # 'empty' is a chunk status in docval, not necessarily an issue rule.
        if rule == "empty":
            matches = [c for c in scanned["chunks"] if c.get("heading") == heading
                       and (c.get("status") == "empty" or any(
                           i.get("rule") in {"empty", "heading_only"} for i in c.get("issues", [])))]
        records[ticket_id] = {
            "result": "still_reported" if matches else "superseded",
            "head": head, "report_sha256": report_hash,
            "source": relative,
            "source_sha256": hashlib.sha256((root / path).read_bytes()).hexdigest(),
            "locations": [c["lines"] for c in matches],
        }
    # Preserve unrelated edits and the old export's formatting verbatim.
    pattern = re.compile(r"(?ms)^  (DOC-\d+):\n.*?(?=^  [A-Z][A-Z0-9-]*:\n|\Z)")
    def update(match):
        record = records.get(match[1])
        block = match[0]
        if record is None:
            return block
        if record["result"] == "superseded":
            block, count = re.subn(r"(?m)^    status: open$", "    status: done", block)
            assert count == 1
        block = re.sub(r"(?m)^    revalidation: .*\n", "", block)
        return block.rstrip("\n") + "\n    revalidation: " + json.dumps(record, sort_keys=True) + "\n"
    return pattern.sub(update, text), records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    before = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in root.rglob("*.md") if not any(
                  part.startswith(".") for part in p.relative_to(root).parts)}
    subprocess.run(["docval", "scan", ".", "--project", ".", "--no-llm",
                    "--output", str(args.report.resolve())], check=True,
                   stdout=__import__("sys").stderr)
    raw = args.report.read_bytes()
    report = json.loads(raw)
    for scanned in report["files"]:
        source = root / scanned["path"]
        if before.get(scanned["path"]) != hashlib.sha256(source.read_bytes()).hexdigest():
            raise RuntimeError("Documentation changed during scan; rerun reconciliation")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    path = root / "planfile.yaml"
    original = path.read_text()
    updated, records = reconcile(original, report, root, head, hashlib.sha256(raw).hexdigest())
    print(json.dumps(records, indent=2))
    if args.apply:
        if path.read_text() != original:
            raise RuntimeError("Backlog changed during reconciliation")
        path.write_text(updated)


if __name__ == "__main__":
    main()
