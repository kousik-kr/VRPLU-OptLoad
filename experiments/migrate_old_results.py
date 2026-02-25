#!/usr/bin/env python3
"""
Migrate old CSV results (summed format) → new per-route format.

Old format:  num_routes, total_served, total_lu_cost, total_distance
New format:  pareto_size, route_index, served, lu_cost, distance, route

For single-route solvers (Insertion, FoodMatch, LIFO):
  - total_served → served (route_index=1, pareto_size=1)
  - Rows with 0 served → route_index=0, pareto_size=0

For Pareto solvers (OptLoad, Exact, NoCluster, NoLUPruning):
  - These are SKIPPED (must be rerun with new per-route output)

Usage:
    python migrate_old_results.py              # Migrate all steps
    python migrate_old_results.py --dry-run    # Show what would be done
    python migrate_old_results.py --step 1 2   # Migrate specific steps
"""

import os
import csv
import shutil
import argparse
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
BACKUP_DIR = RESULTS_DIR / "old_format_backup"

# Old CSV header
OLD_HEADER = [
    "step", "experiment", "solver", "network", "n_requests", "run",
    "capacity", "tw_duration", "threads",
    "runtime_ms", "num_routes", "total_served", "total_lu_cost", "total_distance",
    "pareto_size",
    "clusters", "prefixes_explored", "prefixes_pruned",
    "pruned_capacity", "pruned_lu_bound", "pruned_seed_lu",
    "backtrack_calls", "cluster_orderings", "cross_product",
    "valid_orderings", "seed_lu", "seed_dist", "lb_lu",
    "status", "timeout"
]

# New CSV header (per-route format)
NEW_HEADER = [
    "step", "experiment", "solver", "network", "n_requests", "run",
    "capacity", "tw_duration", "threads",
    "runtime_ms", "pareto_size", "route_index",
    "served", "lu_cost", "distance", "route",
    "clusters", "prefixes_explored", "prefixes_pruned",
    "pruned_capacity", "pruned_lu_bound", "pruned_seed_lu",
    "backtrack_calls", "cluster_orderings", "cross_product",
    "valid_orderings", "seed_lu", "seed_dist", "lb_lu",
    "status", "timeout"
]

SINGLE_ROUTE_SOLVERS = {"Insertion", "FoodMatch", "LIFO"}
PARETO_SOLVERS = {"OptLoad", "Exact", "NoCluster", "NoLUPruning"}

STEP_FILES = {
    1: "step1_core_comparison.csv",
    2: "step2_scalability_requests.csv",
    3: "step3_network_scalability.csv",
    4: "step4_ablation.csv",
    5: "step5_search_space.csv",
    6: "step6_parallel.csv",
    7: "step7_sensitivity.csv",
}


def is_old_format(csv_path: Path) -> bool:
    """Check if a CSV file uses the old (summed) format."""
    with open(csv_path, 'r') as f:
        header = f.readline().strip()
    return "total_served" in header or "num_routes" in header


def migrate_step(step_num: int, dry_run: bool = False) -> dict:
    """Migrate a single step CSV from old to new format.
    
    Returns dict with counts: migrated, skipped_pareto, total.
    """
    csv_name = STEP_FILES[step_num]
    csv_path = RESULTS_DIR / csv_name
    
    result = {"migrated": 0, "skipped_pareto": 0, "total": 0, "file": csv_name}
    
    if not csv_path.exists():
        print(f"  {csv_name}: file not found, skipping")
        return result
    
    if not is_old_format(csv_path):
        print(f"  {csv_name}: already in new format, skipping")
        return result
    
    # Read all rows from old format
    old_rows = []
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            old_rows.append(row)
    
    result["total"] = len(old_rows)
    
    # Convert single-route solver rows
    new_rows = []
    for row in old_rows:
        solver = row.get("solver", "")
        
        if solver in PARETO_SOLVERS:
            result["skipped_pareto"] += 1
            continue
        
        # Map old columns to new columns
        new_row = {}
        # Copy shared columns
        for key in ["step", "experiment", "solver", "network", "n_requests",
                     "run", "capacity", "tw_duration", "threads", "runtime_ms",
                     "clusters", "prefixes_explored", "prefixes_pruned",
                     "pruned_capacity", "pruned_lu_bound", "pruned_seed_lu",
                     "backtrack_calls", "cluster_orderings", "cross_product",
                     "valid_orderings", "seed_lu", "seed_dist", "lb_lu",
                     "status", "timeout"]:
            new_row[key] = row.get(key, "")
        
        # Convert metrics
        total_served = int(row.get("total_served", "0") or "0")
        total_lu = int(row.get("total_lu_cost", "0") or "0")
        total_dist = row.get("total_distance", "0.00") or "0.00"
        
        if total_served == 0 and total_lu == 0:
            new_row["pareto_size"] = 0
            new_row["route_index"] = 0
            new_row["served"] = 0
            new_row["lu_cost"] = 0
            new_row["distance"] = "0.00"
        else:
            new_row["pareto_size"] = 1
            new_row["route_index"] = 1
            new_row["served"] = total_served
            new_row["lu_cost"] = total_lu
            new_row["distance"] = total_dist
        
        new_row["route"] = ""  # Route string not available in old format
        
        new_rows.append(new_row)
        result["migrated"] += 1
    
    if dry_run:
        print(f"  {csv_name}: would migrate {result['migrated']} rows, "
              f"skip {result['skipped_pareto']} Pareto rows")
        return result
    
    # Backup original
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / csv_name
    shutil.copy2(csv_path, backup_path)
    print(f"  Backed up {csv_name} → old_format_backup/{csv_name}")
    
    # Write new format
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=NEW_HEADER)
        writer.writeheader()
        for row in new_rows:
            writer.writerow(row)
    
    print(f"  {csv_name}: migrated {result['migrated']} rows, "
          f"skipped {result['skipped_pareto']} Pareto rows "
          f"(from {result['total']} total)")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Migrate old CSV results to per-route format")
    parser.add_argument("--step", type=int, nargs="+",
                       help="Steps to migrate (1-7). Default: all")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without modifying files")
    args = parser.parse_args()
    
    steps = args.step if args.step else list(range(1, 8))
    
    print(f"\n{'='*60}")
    print(f"Migrating old CSV results → new per-route format")
    if args.dry_run:
        print("(DRY RUN — no files will be modified)")
    print(f"Steps: {steps}")
    print(f"{'='*60}\n")
    
    total_migrated = 0
    total_skipped = 0
    
    for step in sorted(steps):
        if step not in STEP_FILES:
            print(f"  Unknown step: {step}")
            continue
        result = migrate_step(step, dry_run=args.dry_run)
        total_migrated += result["migrated"]
        total_skipped += result["skipped_pareto"]
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  Migrated: {total_migrated} single-route solver rows")
    print(f"  Skipped:  {total_skipped} Pareto solver rows (need rerun)")
    if not args.dry_run:
        print(f"  Backups:  {BACKUP_DIR}/")
    print(f"{'='*60}")
    
    if total_skipped > 0:
        print(f"\nTo rerun Pareto solvers with new per-route format:")
        print(f"  python run_all_experiments.py --reset --step {' '.join(str(s) for s in steps)}")


if __name__ == "__main__":
    main()
