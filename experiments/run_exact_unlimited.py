#!/usr/bin/env python3
"""
Unlimited-Time Exact Solver Experiment
=======================================
Runs the parallelized Exact solver for N=5, N=10, N=15 with 2 queries each.
No time limit — lets every run complete regardless of duration.

Outputs to: experiments/results/exact_unlimited.csv

Usage:
    python run_exact_unlimited.py              # Run all
    python run_exact_unlimited.py --n 5 10     # Run only N=5 and N=10
    python run_exact_unlimited.py --resume     # Skip already-completed runs
"""

import os
import sys
import csv
import re
import time
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.absolute()
SRC_DIR = PROJECT_ROOT / "src"
QUERIES_DIR = PROJECT_ROOT / "experiments" / "queries"
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"
CSV_FILE = RESULTS_DIR / "exact_unlimited.csv"

# London network (all queries are London-based)
NETWORK = "london"
NODE_COUNT = 285050

# Experiment parameters
N_VALUES = [5, 10, 15]
QUERIES_PER_N = 2

# CSV header — one row per Pareto route
CSV_HEADER = [
    "n_requests", "query", "runtime_ms", "pareto_size", "route_index",
    "served", "lu_cost", "distance", "route", "status",
]


def ensure_compiled():
    """Compile Java sources if needed."""
    print("Compiling Java sources...")
    result = subprocess.run(
        "javac *.java",
        cwd=str(SRC_DIR),
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Compilation FAILED:\n{result.stderr}")
        sys.exit(1)
    print("Compilation successful.\n")


def parse_output_file(output_file: str) -> Dict:
    """Parse solver output file to extract per-route metrics."""
    result = {
        "routes": [],
        "runtime_ms": 0,
        "pareto_size": 0,
    }

    if not os.path.exists(output_file):
        return result

    with open(output_file, "r") as f:
        content = f.read()

    # Parse route lines
    route_pattern = re.compile(
        r"(\[.*?\])\s+Number of Successful Requests:(\d+)"
        r"\s+L-U Cost:(\d+)\s+Distance:([\d.]+)"
    )
    for match in route_pattern.finditer(content):
        route_str = match.group(1)
        served = int(match.group(2))
        lu = int(match.group(3))
        dist = float(match.group(4))
        result["routes"].append({
            "served": served,
            "lu_cost": lu,
            "distance": dist,
            "route": route_str,
        })
    result["pareto_size"] = len(result["routes"])

    # Parse runtime (last numeric line, in seconds → convert to ms)
    runtime_match = re.findall(r"^([\d.]+)\s*$", content, re.MULTILINE)
    if runtime_match:
        result["runtime_ms"] = int(float(runtime_match[-1]) * 1000)

    return result


def run_exact(query_file: str, n: int, query_idx: int) -> Tuple[Dict, str]:
    """Run the Exact solver on a single query with NO time limit."""
    output_file = str(PROJECT_ROOT / f"OutputExact_{NODE_COUNT}.txt")

    # Remove existing output file
    if os.path.exists(output_file):
        os.remove(output_file)

    cmd = [
        "java",
        "VRPLoadingUnloadingMain",
        str(PROJECT_ROOT),
        query_file,
        "--exact",
        f"--nodes={NODE_COUNT}",
    ]

    print(f"  Running: N={n}, query={query_idx}")
    print(f"    cmd: {' '.join(cmd)}")
    start_time = time.time()
    status = "success"

    try:
        result = subprocess.run(
            cmd,
            cwd=str(SRC_DIR),
            capture_output=True,
            text=True,
            # No timeout — let it run until completion
        )
        if result.returncode != 0:
            status = "error"
            print(f"    ERROR (rc={result.returncode}): {result.stderr[:300]}")
    except Exception as e:
        status = "error"
        print(f"    EXCEPTION: {e}")

    elapsed_ms = int((time.time() - start_time) * 1000)

    metrics = parse_output_file(output_file)
    if metrics["runtime_ms"] == 0:
        metrics["runtime_ms"] = elapsed_ms

    return metrics, status


def load_completed() -> set:
    """Load already-completed (n, query) pairs from the CSV."""
    completed = set()
    if CSV_FILE.exists():
        with open(CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (int(row["n_requests"]), int(row["query"]))
                completed.add(key)
    return completed


def main():
    parser = argparse.ArgumentParser(description="Exact solver unlimited-time experiments")
    parser.add_argument("--n", type=int, nargs="+", default=N_VALUES,
                        help="N values to run (default: 5 10 15)")
    parser.add_argument("--resume", action="store_true",
                        help="Skip already-completed (n, query) pairs")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ensure_compiled()

    # Determine which runs to do
    completed = load_completed() if args.resume else set()
    write_header = not CSV_FILE.exists() or not args.resume

    experiments = []
    for n in args.n:
        query_dir = QUERIES_DIR / f"N_{n}"
        if not query_dir.exists():
            print(f"WARNING: Query directory {query_dir} not found — skipping N={n}")
            continue
        for q in range(1, QUERIES_PER_N + 1):
            qfile = query_dir / f"query_{q}.txt"
            if not qfile.exists():
                print(f"WARNING: {qfile} not found — skipping")
                continue
            if (n, q) in completed:
                print(f"  Skipping N={n}, query={q} (already completed)")
                continue
            experiments.append((n, q, str(qfile)))

    if not experiments:
        print("No experiments to run.")
        return

    print(f"\nExperiments to run: {len(experiments)}")
    for n, q, qf in experiments:
        print(f"  N={n}, query={q}: {qf}")
    print()

    # Open CSV for appending (or create new)
    mode = "a" if args.resume and CSV_FILE.exists() else "w"
    with open(CSV_FILE, mode, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if mode == "w":
            writer.writeheader()

        for n, q, qfile in experiments:
            print(f"\n{'='*60}")
            print(f"Exact solver: N={n}, query={q}")
            print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")

            metrics, status = run_exact(qfile, n, q)

            runtime_sec = metrics["runtime_ms"] / 1000
            print(f"  Status: {status}")
            print(f"  Runtime: {runtime_sec:.1f}s")
            print(f"  Pareto front size: {metrics['pareto_size']}")

            if metrics["routes"]:
                for i, route in enumerate(metrics["routes"]):
                    row = {
                        "n_requests": n,
                        "query": q,
                        "runtime_ms": metrics["runtime_ms"],
                        "pareto_size": metrics["pareto_size"],
                        "route_index": i,
                        "served": route["served"],
                        "lu_cost": route["lu_cost"],
                        "distance": route["distance"],
                        "route": route["route"],
                        "status": status,
                    }
                    writer.writerow(row)
                    print(f"    Route {i}: served={route['served']}, "
                          f"LU={route['lu_cost']}, dist={route['distance']:.2f}")
            else:
                # Write a single row with no route data
                row = {
                    "n_requests": n,
                    "query": q,
                    "runtime_ms": metrics["runtime_ms"],
                    "pareto_size": 0,
                    "route_index": "",
                    "served": "",
                    "lu_cost": "",
                    "distance": "",
                    "route": "",
                    "status": status,
                }
                writer.writerow(row)
                print(f"    No feasible routes found.")

            f.flush()  # Flush after each experiment for safety

    print(f"\n{'='*60}")
    print(f"All experiments complete. Results saved to:")
    print(f"  {CSV_FILE}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
