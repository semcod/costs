"""Compare fresh and persistent-cache calculations on one deterministic workload."""

import argparse
import hashlib
import json
import os
import statistics
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from costs.calculator import batch_calculate_costs
from costs.tokenizers import count_tokens


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    workload = []
    for index in range(64):
        commit = SimpleNamespace(
            hexsha=f"{index:040x}",
            message="benchmark",
            author=SimpleNamespace(name="Fixture"),
            committed_datetime=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        patch = "@@ -0,0 +1,128 @@\n" + "".join(
            f"+def calculation_{index}_{line}(value): return value * {line + 1}\n"
            for line in range(128)
        )
        workload.append((commit, patch))
    samples = {"cold": [], "warm": []}
    old = {name: os.environ.get(name) for name in ("COSTS_CACHE", "COSTS_CACHE_DIR")}
    count_tokens("warmup", "gpt-4o")
    try:
        os.environ["COSTS_CACHE"] = "1"
        with tempfile.TemporaryDirectory(prefix="costs-benchmark-") as directory:
            for index in range(5):
                os.environ["COSTS_CACHE_DIR"] = str(Path(directory) / str(index))
                results = {}
                for scenario in ("cold", "warm"):
                    cpu, wall = time.process_time(), time.perf_counter()
                    result = batch_calculate_costs(workload, model="gpt-4o")
                    samples[scenario].append(
                        {
                            "wall_s": time.perf_counter() - wall,
                            "cpu_s": time.process_time() - cpu,
                        }
                    )
                    assert result["summary"]["cache_hits"] == (
                        64 if scenario == "warm" else 0
                    )
                    results[scenario] = result["commits"]
                assert results["cold"] == results["warm"]
    finally:
        for name, value in old.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    medians = {
        name: {
            metric: statistics.median(s[metric] for s in values)
            for metric in ("wall_s", "cpu_s")
        }
        for name, values in samples.items()
    }
    report = {
        "schema": "costs.incremental-benchmark/v1",
        "commits": 64,
        "samples": samples,
        "workload_sha256": hashlib.sha256(
            "".join(d for _, d in workload).encode()
        ).hexdigest(),
        "medians": medians,
        "equal_results": True,
        "warm_cache_hits": 64,
        "source_sha256": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [Path(__file__), *sorted(Path("src/costs").glob("*.py"))]
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(medians))
    if medians["warm"]["cpu_s"] > medians["cold"]["cpu_s"] * 0.75:
        raise SystemExit("Warm cache failed the 25% CPU reduction budget")


if __name__ == "__main__":
    main()
