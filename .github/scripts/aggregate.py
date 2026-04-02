#!/usr/bin/env python3
"""Aggregate hyperfine JSON results into markdown tables.

Outputs:
  summary.md  – only statistically significant results (Welch's t-test, p < ALPHA)
  results.md  – complete table with p-values
"""
import json
import math
import os
import sys
from dataclasses import dataclass

from scipy.stats import ttest_ind

ALPHA = 0.05


@dataclass
class BenchmarkRow:
    name: str
    baseline_ms: str
    feature_ms: str
    ratio: float
    p_value: float

    @property
    def is_significant(self) -> bool:
        return not math.isnan(self.p_value) and self.p_value < ALPHA


def format_ms(mean_s: float, stddev_s: float) -> str:
    return f"{mean_s * 1000:.1f} ± {stddev_s * 1000:.1f}"


def format_p(p: float) -> str:
    if math.isnan(p):
        return "n/a"
    if p < 0.001:
        return "< 0.001"
    return f"{p:.3f}"


def make_table(rows: list[BenchmarkRow]) -> str:
    lines = [
        "| Benchmark | Baseline (ms) | Feature (ms) | Ratio | p-value |",
        "|-----------|--------------|--------------|-------|---------|",
        *[
            f"| `{r.name}` | {r.baseline_ms} | {r.feature_ms} | {r.ratio:.3f} | {format_p(r.p_value)} |"
            for r in rows
        ],
    ]
    return "\n".join(lines) + "\n"


def load_benchmark(path: str, filename: str) -> BenchmarkRow | None:
    with open(os.path.join(path, filename)) as fh:
        data = json.load(fh)

    entries = {
        ("baseline" if "baseline" in r["command"] else "feature"): r
        for r in data["results"]
    }
    if "baseline" not in entries or "feature" not in entries:
        print(f"Warning: missing baseline or feature in {filename}", file=sys.stderr)
        return None

    b, f = entries["baseline"], entries["feature"]

    b_times: list[float] = b.get("times", [])
    f_times: list[float] = f.get("times", [])
    _, p = ttest_ind(b_times, f_times, equal_var=False) if len(b_times) >= 2 and len(f_times) >= 2 else (None, float("nan"))

    return BenchmarkRow(
        name=filename[:-5],
        baseline_ms=format_ms(b["mean"], b["stddev"]),
        feature_ms=format_ms(f["mean"], f["stddev"]),
        ratio=b["mean"] / f["mean"],
        p_value=float(p),
    )


def load_all_benchmarks(results_dir: str) -> list[BenchmarkRow]:
    rows = []
    for filename in sorted(os.listdir(results_dir)):
        if filename.endswith(".json"):
            if row := load_benchmark(results_dir, filename):
                rows.append(row)
    return rows


def write_results(rows: list[BenchmarkRow], path: str) -> None:
    with open(path, "w") as fh:
        fh.write(f"_Significance threshold: α = {ALPHA}_\n\n")
        fh.write(make_table(rows))


def write_summary(rows: list[BenchmarkRow], sig_rows: list[BenchmarkRow], path: str) -> None:
    with open(path, "w") as fh:
        if sig_rows:
            fh.write(
                f"_Showing {len(sig_rows)} of {len(rows)} benchmarks with p < {ALPHA} (Welch's t-test)._\n\n"
            )
            fh.write(make_table(sig_rows))
        else:
            fh.write(
                f"_No benchmark showed a statistically significant difference "
                f"(Welch's t-test, α = {ALPHA}). See results.md for the full table._\n"
            )


def main() -> None:
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "results"
    summary_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join(results_dir, "summary.md")
    results_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join(results_dir, "results.md")

    rows = load_all_benchmarks(results_dir)
    if not rows:
        print("No benchmark results found.", file=sys.stderr)
        sys.exit(1)

    sig_rows = [r for r in rows if r.is_significant]

    write_results(rows, results_file)
    write_summary(rows, sig_rows, summary_file)

    print(f"Wrote {len(rows)} total rows to {results_file}")
    print(f"Wrote {len(sig_rows)} significant rows to {summary_file}")


if __name__ == "__main__":
    main()