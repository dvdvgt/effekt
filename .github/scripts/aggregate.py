#!/usr/bin/env python3
"""Aggregate hyperfine JSON results into a markdown table."""

import json
import os
import sys


def format_ms(mean_s: float, stddev_s: float) -> str:
    return f"{mean_s * 1000:.1f} ± {stddev_s * 1000:.1f}"


def main() -> None:
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "results"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "results/summary.md"

    rows = []
    for json_file in sorted(os.listdir(results_dir)):
        if not json_file.endswith(".json"):
            continue

        name = json_file[:-5]
        with open(os.path.join(results_dir, json_file)) as f:
            data = json.load(f)

        entries = {
            ("baseline" if "baseline" in r["command"] else "feature"): r
            for r in data["results"]
        }

        if "baseline" not in entries or "feature" not in entries:
            print(f"Warning: missing baseline or feature in {json_file}", file=sys.stderr)
            continue

        b, f = entries["baseline"], entries["feature"]
        ratio = b["mean"] / f["mean"]
        rows.append((name, format_ms(b["mean"], b["stddev"]), format_ms(f["mean"], f["stddev"]), ratio))

    if not rows:
        print("No benchmark results found.", file=sys.stderr)
        sys.exit(1)

    lines = [
        "| Benchmark | Baseline (ms) | Feature (ms) | Ratio |",
        "|-----------|--------------|--------------|-------|",
        *[f"| `{name}` | {b} | {f} | {ratio:.3f} |" for name, b, f, ratio in rows],
    ]

    with open(output_file, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()