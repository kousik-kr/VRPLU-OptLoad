#!/usr/bin/env python3
"""
Master Experiment Runner for VRPLU-OptLoad
==========================================
Executes all 7 experiment steps, captures results in structured CSV format.

Usage:
    python run_all_experiments.py                  # Run all steps
    python run_all_experiments.py --step 1         # Run only step 1
    python run_all_experiments.py --step 1 2 3     # Run steps 1, 2, 3
    python run_all_experiments.py --resume          # Resume from checkpoint
"""

import os
import sys
import csv
import json
import time
import signal
import subprocess
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.absolute()
SRC_DIR = PROJECT_ROOT / "src"
DATASET_DIR = PROJECT_ROOT / "dataset"
QUERIES_DIR = PROJECT_ROOT / "experiments" / "queries"
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"
CHECKPOINT_FILE = RESULTS_DIR / "checkpoint.json"

# Network configurations
NETWORKS = {
    "oldenburg": {"node_count": 6105, "vertex_count": 6105},
    "california": {"node_count": 21048, "vertex_count": 21048},
    "london": {"node_count": 285050, "vertex_count": 285050},
}

# Solver CLI flags
SOLVERS = {
    "OptLoad": "--cluster",
    "Exact": "--exact",
    "Insertion": "--insertion",
    "LIFO": "--lifostack",
    "FoodMatch": "--foodmatch",
    "NoCluster": "--nocluster",
    "NoLUPruning": "--nolupruning",
}

TIMEOUT = 1200  # 20 minutes per query
RUNS = 10

# CSV header for results — one row per Pareto route
CSV_HEADER = [
    "step", "experiment", "solver", "network", "n_requests", "run",
    "capacity", "tw_duration", "threads",
    "runtime_ms", "pareto_size", "route_index",
    "served", "lu_cost", "distance", "route",
    # OptLoad-specific stats
    "clusters", "prefixes_explored", "prefixes_pruned",
    "pruned_capacity", "pruned_lu_bound", "pruned_seed_lu",
    "backtrack_calls", "cluster_orderings", "cross_product",
    "valid_orderings", "seed_lu", "seed_dist", "lb_lu",
    "status", "timeout"
]


def ensure_compiled():
    """Compile Java sources if needed."""
    print("Compiling Java sources...")
    result = subprocess.run(
        ["javac", "*.java"],
        cwd=str(SRC_DIR),
        shell=True,
        capture_output=True,
        text=True
    )
    # javac with shell=True and glob may not work; use explicit
    result = subprocess.run(
        "javac *.java",
        cwd=str(SRC_DIR),
        shell=True,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Compilation FAILED:\n{result.stderr}")
        sys.exit(1)
    print("Compilation successful.")


def parse_output_file(output_file: str) -> Dict:
    """Parse solver output file to extract per-route metrics.

    Returns a dict with:
      - routes: list of dicts, each with served/lu_cost/distance/route
      - pareto_size: number of Pareto-optimal routes
      - runtime_ms: query runtime in milliseconds
      - OptLoad stats (clusters, prefixes_explored, etc.)
    """
    result = {
        "routes": [],
        "runtime_ms": 0,
        "pareto_size": 0,
        # OptLoad stats
        "clusters": "", "prefixes_explored": "", "prefixes_pruned": "",
        "pruned_capacity": "", "pruned_lu_bound": "", "pruned_seed_lu": "",
        "backtrack_calls": "", "cluster_orderings": "", "cross_product": "",
        "valid_orderings": "", "seed_lu": "", "seed_dist": "", "lb_lu": "",
    }

    if not os.path.exists(output_file):
        return result

    with open(output_file, 'r') as f:
        content = f.read()

    # Parse route lines — capture the full route string and per-route metrics
    route_pattern = re.compile(
        r'(\[.*?\])\s+Number of Successful Requests:(\d+)\s+L-U Cost:(\d+)\s+Distance:([\d.]+)'
    )
    for match in route_pattern.finditer(content):
        route_str, served, lu, dist = match.group(1), match.group(2), match.group(3), match.group(4)
        result["routes"].append({
            "served": int(served),
            "lu_cost": int(lu),
            "distance": float(dist),
            "route": route_str,
        })
    result["pareto_size"] = len(result["routes"])

    # Parse stats line
    stats_match = re.search(r'#STATS (.+)', content)
    if stats_match:
        stats_str = stats_match.group(1)
        stats_pairs = re.findall(r'(\w+)=([\d.]+)', stats_str)
        stats_dict = {k: v for k, v in stats_pairs}
        for key in ["clusters", "prefixes_explored", "prefixes_pruned",
                     "pruned_capacity", "pruned_lu_bound", "pruned_seed_lu",
                     "backtrack_calls", "cluster_orderings", "cross_product",
                     "valid_orderings", "seed_lu", "seed_dist", "lb_lu"]:
            if key in stats_dict:
                result[key] = stats_dict[key]
        if "pareto_size" in stats_dict:
            result["pareto_size"] = int(stats_dict["pareto_size"])

    # Parse runtime (last numeric line)
    runtime_match = re.findall(r'^([\d.]+)\s*$', content, re.MULTILINE)
    if runtime_match:
        result["runtime_ms"] = int(float(runtime_match[-1]) * 1000)

    return result


def run_single_experiment(solver_flag: str, query_file: str, network: str,
                          node_count: int, threads: int = 0) -> Tuple[Dict, str]:
    """Run a single solver on a single query file."""
    # Determine output file prefix based on solver flag
    solver_prefix_map = {
        "--cluster": "Output_",
        "--exact": "OutputExact_",
        "--foodmatch": "OutputFoodMatch_",
        "--lifostack": "OutputLifo_",
        "--insertion": "OutputInsertion_",
        "--bazelmans": "OutputBazelmans_",
        "--nocluster": "OutputNoCluster_",
        "--nolupruning": "OutputNoLUPruning_",
    }
    prefix = solver_prefix_map.get(solver_flag, "Output_")
    vertex_count = NETWORKS[network]["vertex_count"]
    output_file = str(PROJECT_ROOT / f"{prefix}{vertex_count}.txt")

    # Remove existing output file
    if os.path.exists(output_file):
        os.remove(output_file)

    # Build command
    cmd = ["java"]
    if threads > 0:
        cmd.append(f"-Djava.util.concurrent.ForkJoinPool.common.parallelism={threads}")
    cmd.extend([
        "VRPLoadingUnloadingMain",
        str(PROJECT_ROOT),
        query_file,
        solver_flag,
        f"--nodes={node_count}"
    ])
    if threads > 0:
        cmd.append(f"--threads={threads}")

    # Run with timeout
    status = "success"
    timed_out = False
    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            cwd=str(SRC_DIR),
            capture_output=True,
            text=True,
            timeout=TIMEOUT
        )
        if result.returncode != 0:
            status = "error"
            print(f"    ERROR: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        status = "timeout"
        timed_out = True
        print(f"    TIMEOUT after {TIMEOUT}s")

    elapsed_ms = int((time.time() - start_time) * 1000)

    # Parse output
    metrics = parse_output_file(output_file)
    if status == "timeout":
        metrics["runtime_ms"] = TIMEOUT * 1000
    elif metrics["runtime_ms"] == 0:
        metrics["runtime_ms"] = elapsed_ms

    return metrics, status


def get_query_files(query_dir: str, runs: int = RUNS) -> List[str]:
    """Get sorted list of query files from a directory."""
    d = Path(query_dir)
    if not d.exists():
        return []
    files = sorted(d.glob("query_*.txt"), key=lambda p: int(re.search(r'(\d+)', p.stem).group(1)))
    return [str(f) for f in files[:runs]]


def load_checkpoint() -> Dict:
    """Load checkpoint to resume experiments."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {"completed": []}


def save_checkpoint(checkpoint: Dict):
    """Save checkpoint."""
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def is_completed(checkpoint: Dict, run_key: str) -> bool:
    return run_key in checkpoint.get("completed", [])


def mark_completed(checkpoint: Dict, run_key: str):
    if "completed" not in checkpoint:
        checkpoint["completed"] = []
    checkpoint["completed"].append(run_key)
    save_checkpoint(checkpoint)


def run_experiment_batch(step_name: str, experiments: List[Dict],
                         csv_file: str, checkpoint: Dict,
                         solver_filter: Optional[set] = None):
    """Run a batch of experiments and write results to CSV.

    If solver_filter is set, only experiments matching those solvers are run.
    """
    if solver_filter:
        experiments = [e for e in experiments if e["solver"] in solver_filter]
        if not experiments:
            print(f"  No experiments match solver filter {solver_filter}")
            return

    csv_path = RESULTS_DIR / csv_file
    file_exists = csv_path.exists()

    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if not file_exists:
            writer.writeheader()

        total = len(experiments)
        for idx, exp in enumerate(experiments, 1):
            run_key = f"{step_name}_{exp['solver']}_{exp['network']}_N{exp['n_requests']}_R{exp['run']}"
            if 'threads' in exp and exp['threads']:
                run_key += f"_T{exp['threads']}"
            if 'capacity' in exp and exp['capacity']:
                run_key += f"_C{exp['capacity']}"
            if 'tw_duration' in exp and exp['tw_duration']:
                run_key += f"_TW{exp['tw_duration']}"

            if is_completed(checkpoint, run_key):
                continue

            print(f"  [{idx}/{total}] {run_key}")

            metrics, status = run_single_experiment(
                SOLVERS[exp["solver"]],
                exp["query_file"],
                exp["network"],
                NETWORKS[exp["network"]]["node_count"],
                threads=exp.get("threads", 0)
            )

            # Build the common (per-query) part of each row
            common = {
                "step": step_name,
                "experiment": exp.get("experiment", step_name),
                "solver": exp["solver"],
                "network": exp["network"],
                "n_requests": exp["n_requests"],
                "run": exp["run"],
                "capacity": exp.get("capacity", ""),
                "tw_duration": exp.get("tw_duration", ""),
                "threads": exp.get("threads", ""),
                "runtime_ms": metrics["runtime_ms"],
                "pareto_size": metrics["pareto_size"],
                "clusters": metrics.get("clusters", ""),
                "prefixes_explored": metrics.get("prefixes_explored", ""),
                "prefixes_pruned": metrics.get("prefixes_pruned", ""),
                "pruned_capacity": metrics.get("pruned_capacity", ""),
                "pruned_lu_bound": metrics.get("pruned_lu_bound", ""),
                "pruned_seed_lu": metrics.get("pruned_seed_lu", ""),
                "backtrack_calls": metrics.get("backtrack_calls", ""),
                "cluster_orderings": metrics.get("cluster_orderings", ""),
                "cross_product": metrics.get("cross_product", ""),
                "valid_orderings": metrics.get("valid_orderings", ""),
                "seed_lu": metrics.get("seed_lu", ""),
                "seed_dist": metrics.get("seed_dist", ""),
                "lb_lu": metrics.get("lb_lu", ""),
                "status": status,
                "timeout": "1" if status == "timeout" else "0"
            }

            # Write one CSV row per Pareto route
            routes = metrics["routes"]
            if routes:
                for ri, route_info in enumerate(routes, 1):
                    row = dict(common)
                    row["route_index"] = ri
                    row["served"] = route_info["served"]
                    row["lu_cost"] = route_info["lu_cost"]
                    row["distance"] = f"{route_info['distance']:.2f}"
                    row["route"] = route_info["route"]
                    writer.writerow(row)
            else:
                # No routes (timeout / error / empty result) — write a single
                # row with zeroed metrics so the run is still recorded.
                row = dict(common)
                row["route_index"] = 0
                row["served"] = 0
                row["lu_cost"] = 0
                row["distance"] = "0.00"
                row["route"] = ""
                writer.writerow(row)
            f.flush()

            mark_completed(checkpoint, run_key)

            # Log summary (sum across all routes for quick reference)
            total_s = sum(r["served"] for r in routes)
            total_l = sum(r["lu_cost"] for r in routes)
            total_d = sum(r["distance"] for r in routes)
            print(f"    -> {status} | pareto={len(routes)} "
                  f"served={[r['served'] for r in routes]} "
                  f"lu={[r['lu_cost'] for r in routes]} "
                  f"time={metrics['runtime_ms']}ms")


# ============================================================
# STEP DEFINITIONS
# ============================================================

def step1_core_comparison(checkpoint, solver_filter=None):
    """Step 1: Core Algorithm Comparison on Oldenburg."""
    print("\n" + "=" * 60)
    print("STEP 1: Core Algorithm Comparison (Oldenburg, N=2,5,10)")
    print("=" * 60)

    experiments = []
    solvers = ["OptLoad", "Exact", "Insertion", "LIFO", "FoodMatch"]

    for n in [2, 5, 10]:
        query_dir = QUERIES_DIR / "step1_core" / f"oldenburg_N{n}"
        query_files = get_query_files(query_dir)
        if not query_files:
            print(f"  WARNING: No queries found for oldenburg N={n}")
            continue

        for solver in solvers:
            for run_idx, qf in enumerate(query_files, 1):
                experiments.append({
                    "solver": solver,
                    "network": "oldenburg",
                    "n_requests": n,
                    "run": run_idx,
                    "query_file": qf,
                    "experiment": "core_comparison"
                })

    print(f"  Total runs: {len(experiments)}")
    run_experiment_batch("step1", experiments, "step1_core_comparison.csv", checkpoint, solver_filter)


def step2_scalability_requests(checkpoint, solver_filter=None):
    """Step 2: Scalability with Number of Requests on London.
    All solvers use the same N values for fair comparison.
    N=5,10,15,20,25,30,35,40 (OptLoad feasible range).
    """
    print("\n" + "=" * 60)
    print("STEP 2: Scalability with Requests (London, N=5,10,15,20,25,30,35,40)")
    print("=" * 60)

    experiments = []
    solvers = ["OptLoad", "Insertion", "FoodMatch"]

    for n in [5, 10, 15, 20, 25, 30, 35, 40]:
        query_dir = QUERIES_DIR / f"N_{n}"
        if not query_dir.exists():
            query_dir = QUERIES_DIR / "step2_scalability" / f"london_N{n}"
        query_files = get_query_files(query_dir)
        if not query_files:
            print(f"  WARNING: No queries found for london N={n}")
            continue

        for solver in solvers:
            for run_idx, qf in enumerate(query_files, 1):
                experiments.append({
                    "solver": solver,
                    "network": "london",
                    "n_requests": n,
                    "run": run_idx,
                    "query_file": qf,
                    "experiment": "scalability_requests"
                })

    print(f"  Total runs: {len(experiments)}")
    run_experiment_batch("step2", experiments, "step2_scalability_requests.csv", checkpoint, solver_filter)


def step3_network_scalability(checkpoint, solver_filter=None):
    """Step 3: Scalability with Network Size."""
    print("\n" + "=" * 60)
    print("STEP 3: Network Scalability (All networks, N=20)")
    print("=" * 60)

    experiments = []
    solvers = ["OptLoad", "Insertion", "FoodMatch"]

    for network in ["oldenburg", "california", "london"]:
        if network == "london":
            query_dir = QUERIES_DIR / "N_20"
        else:
            query_dir = QUERIES_DIR / "step3_network" / f"{network}_N20"
        query_files = get_query_files(query_dir)
        if not query_files:
            print(f"  WARNING: No queries found for {network} N=20")
            continue

        for solver in solvers:
            for run_idx, qf in enumerate(query_files, 1):
                experiments.append({
                    "solver": solver,
                    "network": network,
                    "n_requests": 20,
                    "run": run_idx,
                    "query_file": qf,
                    "experiment": "network_scalability"
                })

    print(f"  Total runs: {len(experiments)}")
    run_experiment_batch("step3", experiments, "step3_network_scalability.csv", checkpoint, solver_filter)


def step4_ablation(checkpoint, solver_filter=None):
    """Step 4: Ablation Study on London — N=5,10,15,20,25,30,35,40."""
    print("\n" + "=" * 60)
    print("STEP 4: Ablation Study (London, N=5,10,15,20,25,30,35,40)")
    print("=" * 60)

    experiments = []
    solvers = ["OptLoad", "NoCluster", "NoLUPruning"]

    for n in [5, 10, 15, 20, 25, 30, 35, 40]:
        query_dir = QUERIES_DIR / f"N_{n}"
        if not query_dir.exists():
            query_dir = QUERIES_DIR / "step4_ablation" / f"london_N{n}"
        query_files = get_query_files(query_dir)
        if not query_files:
            print(f"  WARNING: No queries found for london N={n}")
            continue

        for solver in solvers:
            for run_idx, qf in enumerate(query_files, 1):
                experiments.append({
                    "solver": solver,
                    "network": "london",
                    "n_requests": n,
                    "run": run_idx,
                    "query_file": qf,
                    "experiment": "ablation"
                })

    print(f"  Total runs: {len(experiments)}")
    run_experiment_batch("step4", experiments, "step4_ablation.csv", checkpoint, solver_filter)


def step5_search_space(checkpoint, solver_filter=None):
    """Step 5: Search Space Reduction Analysis on London.
    Capped at N=5..40 (OptLoad feasible range).
    """
    print("\n" + "=" * 60)
    print("STEP 5: Search Space Reduction (London, N=5,10,15,20,25,30,35,40)")
    print("=" * 60)

    experiments = []

    for n in [5, 10, 15, 20, 25, 30, 35, 40]:
        query_dir = QUERIES_DIR / f"N_{n}"
        if not query_dir.exists():
            query_dir = QUERIES_DIR / "step5_searchspace" / f"london_N{n}"
        query_files = get_query_files(query_dir)
        if not query_files:
            print(f"  WARNING: No queries found for london N={n}")
            continue

        for run_idx, qf in enumerate(query_files, 1):
            experiments.append({
                "solver": "OptLoad",
                "network": "london",
                "n_requests": n,
                "run": run_idx,
                "query_file": qf,
                "experiment": "search_space"
            })

    print(f"  Total runs: {len(experiments)}")
    run_experiment_batch("step5", experiments, "step5_search_space.csv", checkpoint, solver_filter)


def step6_parallel(checkpoint, solver_filter=None):
    """Step 6: Parallel Performance on London.
    Changed from N=60 to N=20 (feasible for OptLoad).
    """
    print("\n" + "=" * 60)
    print("STEP 6: Parallel Performance (London, N=20, threads=1,2,4,8,16,24)")
    print("=" * 60)

    experiments = []
    query_dir = QUERIES_DIR / "N_20"
    if not query_dir.exists():
        query_dir = QUERIES_DIR / "step6_parallel" / "london_N20"
    query_files = get_query_files(query_dir)

    if not query_files:
        print("  WARNING: No queries found for london N=20")
        return

    for threads in [1, 2, 4, 8, 16, 24]:
        for run_idx, qf in enumerate(query_files, 1):
            experiments.append({
                "solver": "OptLoad",
                "network": "london",
                "n_requests": 20,
                "run": run_idx,
                "query_file": qf,
                "threads": threads,
                "experiment": "parallel_performance"
            })

    print(f"  Total runs: {len(experiments)}")
    run_experiment_batch("step6", experiments, "step6_parallel.csv", checkpoint, solver_filter)


def step7_sensitivity(checkpoint, solver_filter=None):
    """Step 7: Sensitivity Analysis on London."""
    print("\n" + "=" * 60)
    print("STEP 7: Sensitivity Analysis (London, N=20)")
    print("=" * 60)

    experiments = []

    # 7A: Capacity variation
    print("  7A: Capacity variation (C=6,8,10,12)")
    for cap in [6, 8, 10, 12]:
        query_dir = QUERIES_DIR / "step7_sensitivity" / f"capacity_C{cap}"
        query_files = get_query_files(query_dir)
        if not query_files:
            print(f"  WARNING: No queries found for capacity={cap}")
            continue

        for run_idx, qf in enumerate(query_files, 1):
            experiments.append({
                "solver": "OptLoad",
                "network": "london",
                "n_requests": 20,
                "run": run_idx,
                "query_file": qf,
                "capacity": cap,
                "experiment": "sensitivity_capacity"
            })

    # 7B: Time window tightness
    print("  7B: Time window tightness (TW=30,60,90,120)")
    for tw in [30, 60, 90, 120]:
        query_dir = QUERIES_DIR / "step7_sensitivity" / f"timewindow_TW{tw}"
        query_files = get_query_files(query_dir)
        if not query_files:
            print(f"  WARNING: No queries found for tw={tw}")
            continue

        for run_idx, qf in enumerate(query_files, 1):
            experiments.append({
                "solver": "OptLoad",
                "network": "london",
                "n_requests": 20,
                "run": run_idx,
                "query_file": qf,
                "tw_duration": tw,
                "experiment": "sensitivity_timewindow"
            })

    print(f"  Total runs: {len(experiments)}")
    run_experiment_batch("step7", experiments, "step7_sensitivity.csv", checkpoint, solver_filter)


def main():
    parser = argparse.ArgumentParser(description="Run VRPLU-OptLoad experiments")
    parser.add_argument("--step", type=int, nargs="+",
                       help="Steps to run (1-7). Default: all")
    parser.add_argument("--solvers", type=str, nargs="+",
                       help="Only run these solvers (e.g., OptLoad Exact)")
    parser.add_argument("--resume", action="store_true",
                       help="Resume from checkpoint")
    parser.add_argument("--reset", action="store_true",
                       help="Reset checkpoint AND remove CSV files")
    parser.add_argument("--reset-checkpoint", action="store_true",
                       help="Reset checkpoint only (keep CSV files)")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Handle checkpoint
    if args.reset:
        if CHECKPOINT_FILE.exists():
            os.remove(CHECKPOINT_FILE)
        # Remove CSV files
        for f in RESULTS_DIR.glob("step*.csv"):
            os.remove(f)
        print("Reset complete. Starting fresh.")

    if args.reset_checkpoint:
        if CHECKPOINT_FILE.exists():
            os.remove(CHECKPOINT_FILE)
        print("Checkpoint reset (CSV files preserved).")

    checkpoint = load_checkpoint() if args.resume or (not args.reset) else {"completed": []}

    # Solver filter
    solver_filter = set(args.solvers) if args.solvers else None
    if solver_filter:
        print(f"Solver filter: {solver_filter}")

    # Compile
    ensure_compiled()

    # Determine which steps to run
    steps_to_run = args.step if args.step else [1, 2, 3, 4, 5, 6, 7]

    step_funcs = {
        1: step1_core_comparison,
        2: step2_scalability_requests,
        3: step3_network_scalability,
        4: step4_ablation,
        5: step5_search_space,
        6: step6_parallel,
        7: step7_sensitivity,
    }

    start_time = time.time()
    for step in steps_to_run:
        if step in step_funcs:
            step_funcs[step](checkpoint, solver_filter)
        else:
            print(f"Unknown step: {step}")

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"ALL EXPERIMENTS COMPLETE in {elapsed/3600:.1f} hours")
    print(f"Results saved in: {RESULTS_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
