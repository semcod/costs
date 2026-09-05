"""Bounded, reproducible local benchmark; no API calls or working-tree writes.

Run from the repository root with PYTHONPATH=src python benchmarks/calculation.py
--output docs/performance/baseline.json. Reuse the same Git HEAD and environment
for the candidate. Timings include CPU consumed by Git subprocesses.
"""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import resource
import statistics
import subprocess
import time
from pathlib import Path

from costs.calculator import batch_calculate_costs
from costs.git_parser import parse_commits
import git


def digest(value):
    return hashlib.sha256(value).hexdigest()


def usage():
    own = resource.getrusage(resource.RUSAGE_SELF)
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + child.ru_utime + child.ru_stime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--max-commits", type=int, default=30)
    args = parser.parse_args()
    if not 3 <= args.samples <= 20 or not 1 <= args.max_commits <= 100:
        parser.error("Use 3..20 samples and 1..100 commits")
    repo = git.Repo(args.repo)
    revision = repo.head.commit.hexsha
    commits = list(repo.iter_commits(max_count=args.max_commits))
    workload = []
    size = 0
    for commit in commits:
        command = [
            "git",
            "-C",
            str(args.repo),
            "show",
            "--format=",
            "--first-parent",
            "--no-ext-diff",
            "--no-textconv",
            "--no-color",
            commit.hexsha,
        ]
        patch = subprocess.check_output(command, timeout=30)
        size += len(patch)
        if size > 20_000_000:
            parser.error("Workload exceeds 20 MB")
        workload.append((commit, patch.decode("utf-8", errors="replace")))
    identity = [(c.hexsha, digest(d.encode())) for c, d in workload]
    metadata = {
        "revision": revision,
        "commits": identity,
        "patch_bytes": size,
        "model": "claude-3.5-sonnet",
        "samples": args.samples,
        "warmup": "one complete pass per scenario",
    }
    operations = {
        "parse": lambda: parse_commits(
            str(args.repo), max_count=args.max_commits, ai_only=False
        ),
        "calculate": lambda: batch_calculate_costs(workload),
        "pipeline": lambda: batch_calculate_costs(
            parse_commits(str(args.repo), max_count=args.max_commits, ai_only=False)
        ),
    }
    measurements = {}
    for name, operation in operations.items():
        operation()
        samples = []
        for _ in range(args.samples):
            cpu = usage()
            start = time.perf_counter()
            result = operation()
            elapsed = time.perf_counter() - start
            samples.append({"wall_s": elapsed, "cpu_s": usage() - cpu})
        measurements[name] = {
            "samples": samples,
            "median_wall_s": statistics.median(s["wall_s"] for s in samples),
            "median_cpu_s": statistics.median(s["cpu_s"] for s in samples),
        }
        if isinstance(result, dict):
            measurements[name]["summary"] = result["summary"]
    source = Path(__import__("costs.calculator", fromlist=["__file__"]).__file__).parent
    report = {
        "workload": metadata,
        "workload_sha256": digest(json.dumps(metadata, sort_keys=True).encode()),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "dependencies": {
                n: importlib.metadata.version(n)
                for n in ("GitPython", "tiktoken", "anthropic")
            },
        },
        "source_sha256": {
            p.name: digest(p.read_bytes()) for p in sorted(source.glob("*.py"))
        },
        "measurements": measurements,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
    }
    assert repo.head.commit.hexsha == revision, "HEAD changed during measurement"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: v["median_wall_s"] for k, v in measurements.items()}))


if __name__ == "__main__":
    main()
