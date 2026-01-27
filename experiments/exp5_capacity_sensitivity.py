#!/usr/bin/env python3
"""
Experiment 5: Sensitivity to Capacity C
=======================================
Tests robustness to vehicle capacity variations.
Fix N = 40, run OptLoad and Insertion for C ∈ {8, 10, 12}
"""

import subprocess
import os
import json
import re
import time
import shutil
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path("/home/gunturi/VRPLU-OptLoad")
EXPERIMENTS_DIR = BASE_DIR / "experiments"
RESULTS_DIR = EXPERIMENTS_DIR / "results" / "missing_experiments"
QUERIES_DIR = EXPERIMENTS_DIR / "queries"
DATASET_DIR = BASE_DIR / "dataset"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def modify_query_capacity(query_content: str, new_capacity: int) -> str:
    """Modify the capacity in a query file."""
    lines = query_content.strip().split('\n')
    result_lines = []
    
    for line in lines:
        if line.startswith('C '):
            result_lines.append(f'C {new_capacity}')
        else:
            result_lines.append(line)
    
    return '\n'.join(result_lines)

def run_solver_on_query(query_content: str, solver_flag: str, timeout: int = 300) -> Dict:
    """Run solver on a query and return results."""
    query_file = DATASET_DIR / "Query_285050.txt"
    with open(query_file, 'w') as f:
        f.write(query_content)
    
    cmd = [
        "java", "-cp", str(BASE_DIR / "target" / "classes"),
        "VRPLoadingUnloadingMain",
        str(DATASET_DIR),
        solver_flag
    ]
    
    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(BASE_DIR)
        )
        runtime_ms = (time.time() - start_time) * 1000
        
        output = result.stdout + result.stderr
        return parse_output(output, runtime_ms)
        
    except subprocess.TimeoutExpired:
        return {"served": 0, "lu_cost": 0, "distance": 0, "runtime_ms": timeout*1000, "timeout": True}
    except Exception as e:
        return {"served": 0, "lu_cost": 0, "distance": 0, "runtime_ms": 0, "error": str(e)}

def parse_output(output: str, runtime_ms: float) -> Dict:
    """Parse solver output."""
    result = {"served": 0, "lu_cost": 0, "distance": 0.0, "runtime_ms": runtime_ms, "timeout": False}
    
    match = re.search(r'Found solution:\s*(\d+)\s*requests,\s*LU cost:\s*(\d+),\s*Distance:\s*([\d.]+)', output)
    if match:
        result["served"] = int(match.group(1))
        result["lu_cost"] = int(match.group(2))
        result["distance"] = float(match.group(3))
    
    return result

def load_queries(n: int, max_queries: int = 30) -> List[str]:
    """Load existing query files for given N."""
    query_dir = QUERIES_DIR / f"N_{n}"
    queries = []
    
    if query_dir.exists():
        query_files = sorted(query_dir.glob("query_*.txt"))[:max_queries]
        for qf in query_files:
            with open(qf, 'r') as f:
                queries.append(f.read())
    
    return queries

print("=" * 70)
print("EXPERIMENT 5: CAPACITY SENSITIVITY ANALYSIS")
print("=" * 70)
print()

# Configuration
N_VALUE = 40  # Fixed problem size
CAPACITY_VALUES = [8, 10, 12]
ALGORITHMS = [
    ("OptLoad", "--cluster"),
    ("Insertion", "--insertion")
]
NUM_QUERIES = 20
TIMEOUT = 300

# Load base queries
base_queries = load_queries(N_VALUE, max_queries=NUM_QUERIES)
print(f"Loaded {len(base_queries)} queries for N={N_VALUE}")

if len(base_queries) == 0:
    print("ERROR: No queries found. Please run query generation first.")
    exit(1)

# Run experiments
results = {c: {} for c in CAPACITY_VALUES}

for capacity in CAPACITY_VALUES:
    print(f"\n{'='*50}")
    print(f"Testing Capacity C={capacity}")
    print(f"{'='*50}")
    
    for algo_name, algo_flag in ALGORITHMS:
        print(f"\n  {algo_name}:")
        results[capacity][algo_name] = []
        
        for i, query in enumerate(base_queries):
            # Modify capacity
            modified_query = modify_query_capacity(query, capacity)
            
            result = run_solver_on_query(modified_query, algo_flag, timeout=TIMEOUT)
            results[capacity][algo_name].append(result)
            
            status = "TIMEOUT" if result.get("timeout") else f"{result['served']} served"
            print(f"    Query {i+1}: {status} ({result['runtime_ms']/1000:.2f}s)")
        
        # Calculate averages
        completed = [r for r in results[capacity][algo_name] if not r.get("timeout")]
        if completed:
            avg_served = sum(r["served"] for r in completed) / len(completed)
            avg_lu = sum(r["lu_cost"] for r in completed) / len(completed)
            avg_runtime = sum(r["runtime_ms"] for r in completed) / len(completed)
            completion_rate = len(completed) / len(base_queries) * 100
            print(f"    Summary: {avg_served:.1f} served, {avg_lu:.1f} LU, {avg_runtime/1000:.2f}s, {completion_rate:.0f}% complete")

# Save results
results_file = RESULTS_DIR / "experiment5_capacity_sensitivity.json"
with open(results_file, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to: {results_file}")

# Generate summary
print("\n" + "=" * 70)
print("EXPERIMENT 5 SUMMARY: CAPACITY SENSITIVITY")
print("=" * 70)

print(f"\n{'Capacity':<10} {'Algorithm':<12} {'Completed':<12} {'Served':<12} {'LU Cost':<12} {'Runtime(s)':<12}")
print("-" * 70)

summary_data = []
for capacity in CAPACITY_VALUES:
    for algo_name, _ in ALGORITHMS:
        data = results[capacity][algo_name]
        completed = [r for r in data if not r.get("timeout")]
        if completed:
            avg_served = sum(r["served"] for r in completed) / len(completed)
            avg_lu = sum(r["lu_cost"] for r in completed) / len(completed)
            avg_runtime = sum(r["runtime_ms"] for r in completed) / len(completed) / 1000
            comp_rate = f"{len(completed)}/{len(data)}"
            print(f"C={capacity:<7} {algo_name:<12} {comp_rate:<12} {avg_served:<12.1f} {avg_lu:<12.1f} {avg_runtime:<12.2f}")
            summary_data.append({
                "capacity": capacity,
                "algorithm": algo_name,
                "served": avg_served,
                "lu_cost": avg_lu,
                "runtime": avg_runtime,
                "completed": len(completed),
                "total": len(data)
            })
        else:
            print(f"C={capacity:<7} {algo_name:<12} {'0/'+str(len(data)):<12} {'-':<12} {'-':<12} {'-':<12}")
    print("-" * 70)

# Analyze sensitivity
print("\n📈 CAPACITY SENSITIVITY ANALYSIS:")

for algo_name, _ in ALGORITHMS:
    algo_data = [d for d in summary_data if d["algorithm"] == algo_name]
    if len(algo_data) >= 2:
        served_values = [(d["capacity"], d["served"]) for d in algo_data]
        print(f"\n  {algo_name}:")
        for c, served in served_values:
            print(f"    C={c}: {served:.1f} requests served")
        
        # Calculate sensitivity
        if len(served_values) >= 2:
            c_low, s_low = served_values[0]
            c_high, s_high = served_values[-1]
            sensitivity = (s_high - s_low) / (c_high - c_low)
            print(f"    Sensitivity: {sensitivity:.2f} requests per unit capacity")

print("\nExperiment 5 complete!")
