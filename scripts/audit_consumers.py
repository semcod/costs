"""Read-only costs dependency audit from an explicit list of discovered files.

Reports contain configuration evidence, not a claim about unobserved deployments.
Write reports outside the published repository when auditing private projects.
"""

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import SpecifierSet


def repository(path, root):
    for parent in (path.parent, *path.parents):
        if (parent / ".git").exists():
            return parent
        if parent == root:
            break
    return path.parent


def requirement(value, latest):
    try:
        item = Requirement(value)
    except InvalidRequirement:
        return None
    if item.name.lower().replace("_", "-") != "costs":
        return None
    return {
        "requirement": str(item),
        "allows_latest": item.specifier.contains(latest),
        "direct_url": bool(item.url),
        "conditional": bool(item.marker),
    }


def scan(files, root, latest):
    projects = {}
    errors = []
    for path in files:
        try:
            if path.stat().st_size > 2_000_000:
                errors.append({"path": str(path), "reason": "over 2 MB limit"})
                continue
            source = path.read_text(encoding="utf-8")
            repo = repository(path, root)
            record = projects.setdefault(
                str(repo.relative_to(root)),
                {
                    "declarations": [],
                    "locked_versions": [],
                    "usage": [],
                    "upgrade_commands": [],
                    "installed": [],
                },
            )
            location = str(path.relative_to(repo))
            if path.suffix == ".toml" or path.name in {
                "uv.lock",
                "poetry.lock",
                "Pipfile",
            }:
                data = tomllib.loads(source)
                for package in data.get("package", []):
                    if package.get("name") == "costs":
                        record["locked_versions"].append(
                            {"file": location, "version": package.get("version")}
                        )
                if "costs" in data.get("tool", {}):
                    record["usage"].append(
                        {"file": location, "kind": "tool.costs configuration"}
                    )

                def walk(value, field=""):
                    if isinstance(value, list):
                        for entry in value:
                            if isinstance(entry, str):
                                req = requirement(entry, latest)
                                if req:
                                    record["declarations"].append(
                                        {"file": location, "field": field, **req}
                                    )
                            elif isinstance(entry, dict) and path.name not in {
                                "uv.lock",
                                "poetry.lock",
                            }:
                                walk(entry, field)
                    elif isinstance(value, dict):
                        for key, entry in value.items():
                            if (
                                key == "costs"
                                and "dependencies" in field
                                and isinstance(entry, (str, dict))
                            ):
                                spec = (
                                    entry
                                    if isinstance(entry, str)
                                    else entry.get("version", "*")
                                )
                                allowed = None
                                try:
                                    allowed = (
                                        True
                                        if spec == "*"
                                        else SpecifierSet(spec).contains(latest)
                                    )
                                except Exception:
                                    pass
                                record["declarations"].append(
                                    {
                                        "file": location,
                                        "field": field,
                                        "requirement": "costs " + spec,
                                        "allows_latest": allowed,
                                        "direct_url": isinstance(entry, dict)
                                        and any(
                                            k in entry for k in ("git", "path", "url")
                                        ),
                                        "conditional": False,
                                    }
                                )
                            elif key != "package":
                                walk(entry, field + "." + key)

                walk(data)
            for index, line in enumerate(source.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "requirements" in path.name:
                    req = requirement(stripped.split(" #", 1)[0], latest)
                    if req:
                        record["declarations"].append(
                            {"file": location, "line": index, **req}
                        )
                if re.search(
                    r"\b(?:aicost|costs)\s+(?:auto-badge|analyze|report|badge|estimate)\b",
                    line,
                ):
                    record["usage"].append(
                        {"file": location, "line": index, "kind": "CLI invocation"}
                    )
                if re.search(
                    r"\b(?:pip3?\s+install|uv\s+(?:pip\s+install|sync|run|tool\s+(?:install|upgrade)))\b",
                    line,
                ) and re.search(r"\bcosts\b", line):
                    upgrade = bool(
                        re.search(
                            r"(?:--upgrade(?:-package)?\b|(?:^|\s)-U(?:\s|$)|uv\s+tool\s+upgrade)",
                            line,
                        )
                    )
                    record["upgrade_commands"].append(
                        {"file": location, "line": index, "explicit_upgrade": upgrade}
                    )
        except (OSError, UnicodeError, ValueError, TypeError, AttributeError) as error:
            errors.append({"path": str(path), "reason": type(error).__name__})
    relevant = {}
    for name, record in projects.items():
        if not any(record.values()):
            continue
        repo = root / name
        for env in (".venv", "venv"):
            for metadata in (repo / env / "lib").glob(
                "python*/site-packages/costs-*.dist-info/METADATA"
            ):
                version = metadata.parent.name[len("costs-") : -len(".dist-info")]
                record["installed"].append(
                    {
                        "environment": env,
                        "version": version,
                        "latest": version == latest,
                    }
                )
        record["has_explicit_upgrade_command"] = any(
            item["explicit_upgrade"] for item in record["upgrade_commands"]
        )
        relevant[name] = record
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "latest_pypi_version": latest,
        "scope": "Discovered local manifests, lockfiles, scripts, workflows and conventional project virtual environments; no remote runtime inspection",
        "projects": dict(sorted(relevant.items())),
        "errors": errors,
        "summary": {
            "projects": len(relevant),
            "with_upgrade_command": sum(
                r["has_explicit_upgrade_command"] for r in relevant.values()
            ),
            "with_installed_metadata": sum(
                bool(r["installed"]) for r in relevant.values()
            ),
            "installed_versions": dict(
                Counter(i["version"] for r in relevant.values() for i in r["installed"])
            ),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--latest", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    files = [Path(line) for line in args.files.read_text().splitlines()]
    if len(files) > 10_000:
        parser.error("File count exceeds 10000")
    report = scan(files, args.root, args.latest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"]))


if __name__ == "__main__":
    main()
