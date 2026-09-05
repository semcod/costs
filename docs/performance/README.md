# Calculation performance and correctness

ADOPT `wellmanifest/performance@1b9b259f90adc480257ec6a13df30d7be549db4d`.
`semcod/costs` owns this local adapter and evidence. It does not HOME Wellmanifest.
The pinned contract is [Performance v1](https://github.com/wellmanifest/performance/blob/1b9b259f90adc480257ec6a13df30d7be549db4d/docs/PERFORMANCE.md).
The upstream checkout was clean when its validator was used.

## Measured result

Nine samples per scenario, one warm-up pass, 30 commits at
`d77d31004ddc92141577c0577046150ccaca452c`, 2,216,592 bytes of canonical patches.
Baseline source was restored from that immutable revision into a temporary
directory. Both variants ran consecutively in fresh processes using the same
harness, Python environment and Git history. Raw samples, workload hashes,
source hashes and environment versions are in [baseline.json](baseline.json)
and [candidate.json](candidate.json). Git version: 2.51.0.

| Scenario | Before | After | Less wall time |
|---|---:|---:|---:|
| Git patch extraction | 0.551 s | 0.174 s | 68.4% |
| Calculation on fixed patches | 0.611 s | 0.530 s | 13.1% |
| Complete pipeline | 1.409 s | 0.897 s | 36.4% |

Complete-pipeline CPU time (including Git children):
1.091 s -> 0.739 s.
Process peak RSS: 139.8 MiB -> 114.1 MiB.
These are local observations, not universal speed guarantees. Host load caused
wall-time variation during initial profiling, so the final comparison remeasured
both versions with nine samples. Tokenizer warm-up is excluded. On an uncached
machine tiktoken may download encoding tables on first use. Peak RSS includes
fixture preparation and warm-up and covers the Python process, not child RSS.

## Changes and compatibility

- Read selected commits in sequential groups of at most 16 with one Git call.
  No thread pool or unbounded task queue. Retain commit order and filtering:
  `max_count` still limits inspected commits before AI/date filters. Full history
  removes the count limit without an extra scan to find a lower date bound.
- Compare root commits to an empty tree and merges to their first parent.
  Preserve patch headers and disable external diff helpers and textconv.
  Batch extraction uses Git's `show --first-parent` diff behavior; validation
  was performed with Git 2.51.0.
- Parse diff statistics once, respect hunk boundaries and LF line separators.
  Lines starting with literal `++` or `--` inside a hunk count as code.
- Use tiktoken's model mapping and literal special-token handling. Claude and
  unsupported families explicitly report an approximation. The SDK is not
  initialized during local counting. Metadata cache: 32 model-name entries,
  process lifetime, LRU eviction or process restart for invalidation. tiktoken
  owns its encoding-object cache. No source text or credentials are cached.
- Remove the cost floor, validate token counts and numeric rates, use decimal
  multiplication for prices and round batch time/value only after aggregation.
  Known routed model aliases retain their known price. Existing unknown-model
  fallback rates remain bundled estimates, not live provider prices.
- Preserve existing result keys and add `estimation` and `diff_stats`.
  Output-token counts and human time remain heuristics. Finite ROI values above
  1000 are formatted numerically. Malformed SaaS results warn and fall back;
  the analyze command forwards its configured SaaS URL.
- The badge integration test now uses the current source in a temporary Git
  repository, with real assertions and no edits to the project README.

Expected numerical differences on the recorded workload: fixed-patch cost
10.3412 -> 10.3430 USD from corrected line counting;
pipeline cost 10.2846 -> 10.3430 USD also includes the now-preserved patch headers.
Tests compare line counts to Git rather than treating incorrect historical
results as a compatibility requirement.

## Verification and reproduction

Run from the repository root:

```bash
PYTHONPATH=src python3 -m pytest -q
python3 benchmarks/check_performance.py --historical
PYTHONPATH=src python3 benchmarks/calculation.py --samples 9 --output /tmp/costs-repeat.json
```

For an exact workload repeat, use a repository whose HEAD is the recorded subject
revision. To repeat the baseline, extract `src/costs` from that revision to a
temporary directory and set `PYTHONPATH` to its `src` directory while running the
same current benchmark harness against the same Git fixture. No checkout reset is
needed. Keep baseline and candidate sample counts and environments identical.
New measurements need new evidence digests and a new plan binding.

The [plan](plan.json) follows `performance.plan/v1`. Validate the schema and
semantic contract with a checkout of the pinned standard:

```bash
PERFORMANCE_STANDARD=/path/to/wellmanifest/performance
python3 "$PERFORMANCE_STANDARD/src/performance.py" validate docs/performance/plan.json
```

The local checker verifies raw-file hashes, medians, matching workload/environment
and CPU/memory/time budgets. This first-stage report is archived: use
`--historical` after subsequent implementation changes. Without that flag the
checker additionally requires the source to match the original measured candidate.
Acceptance requires at least 10% less pipeline wall time and CPU, no peak-RSS
increase, at least 20% less Git extraction CPU, and at most 10% additional CPU
for isolated calculation. The latter permits the added correctness checks.
Functional validation consists of 44 passing regression/integration tests.

Scope is local source review and measurement. No release or deployment was
performed. A future rollout observes the same budgets for 60 seconds and aborts
on any functional or resource regression. Roll back only the five implementation
paths listed in the plan to the subject revision, preserve unrelated work, and
rerun the same fixture. The plan grants no execution authority.

## Incremental calculation and dated pricing

The next stage adds a bounded persistent cache and a dated price catalog.
[Incremental measurements](incremental.json) compare five cold/warm pairs on 64
deterministic diffs, verify identical per-commit results and require at least 25%
less CPU on the warm run. Warm runs must report 64 cache hits. Reproduce with:

```bash
PYTHONPATH=src python3 benchmarks/incremental.py --output /tmp/incremental.json
```

The cache stores counts only, with 10,000 entries and a 30-day TTL. Prices and ROI
are never cached. Invalidation binds content, model, encoding, tokenizer version
and estimator revision. The cache has a 50 ms database lock wait, no worker pool
and an uncached fallback. The price refresh is explicit, capped at 4 MB, uses a
20-second HTTP timeout, validates all rates and replaces the file atomically.
Unknown models have no guessed price. Catalog retrieval date, source, currency
and legacy/custom status are exposed alongside results. Current regression tests
cover repricing, invalidation, cache limits/expiry/corruption/locking and invalid
price refreshes. CI runs the tests and cache benchmark on Python 3.9 and 3.13.

The initial plan and receipt remain historical evidence; their measured output
was produced before this cache and catalog change.
