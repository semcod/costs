"""Verify local evidence bindings and budgets in a Wellmanifest performance plan.

The pinned upstream validator checks the plan contract; this adopter-side check
also verifies local file digests, measured values and the current source tree.
"""

import hashlib
import argparse
import json
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def evidence(binding):
    path = (ROOT / binding["uri"]).resolve()
    if ROOT not in path.parents:
        raise ValueError("Evidence must be inside the repository")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != binding["sha256"]:
        raise ValueError(f"Evidence digest mismatch: {binding['uri']}")
    return raw


def metrics(report):
    result = {"peak_rss": ("bytes", report["peak_rss_bytes"])}
    for scenario, measurement in report["measurements"].items():
        samples = measurement["samples"]
        if len(samples) != report["workload"]["samples"] or len(samples) < 3:
            raise ValueError("Incomparable sample count")
        for field in ("wall", "cpu"):
            value = statistics.median(s[f"{field}_s"] for s in samples)
            if value != measurement[f"median_{field}_s"]:
                raise ValueError("Median does not match raw samples")
            result[f"{scenario}_{field}"] = ("s", value)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--historical",
        action="store_true",
        help="Verify archived evidence without asserting that today's source is unchanged",
    )
    args = parser.parse_args()
    plan = json.loads((ROOT / "docs/performance/plan.json").read_text())
    evidence(plan["workload"]["evidence"])
    reports = {}
    for name in ("baseline", "candidate"):
        report = json.loads(evidence(plan[name]["evidence"]))
        actual = metrics(report)
        declared = {m["name"]: (m["unit"], m["value"]) for m in plan[name]["metrics"]}
        if actual != declared:
            raise ValueError(f"{name} metrics do not match evidence")
        reports[name] = report
    for key in ("workload", "workload_sha256", "environment"):
        if reports["baseline"][key] != reports["candidate"][key]:
            raise ValueError(f"Incomparable {key}")
    for name, expected in (
        {} if args.historical else reports["candidate"]["source_sha256"]
    ).items():
        actual = hashlib.sha256((ROOT / "src/costs" / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Candidate evidence is stale for {name}")
    observed = metrics(reports["candidate"])
    for budget in plan["budgets"]:
        unit, value = observed[budget["metric"]]
        if unit != budget["unit"]:
            raise ValueError("Incomparable budget units")
        passed = (
            value <= budget["threshold"]
            if budget["comparison"] == "at_most"
            else value >= budget["threshold"]
        )
        if not passed:
            raise ValueError(f"Budget failed: {budget['metric']}")
    print(
        "PASS: evidence digests, workload, environment, samples and budgets"
        + (" (historical source)" if args.historical else ", current source")
    )


if __name__ == "__main__":
    main()
