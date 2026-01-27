#!/usr/bin/env python3
"""
Experiment 1: True Exact Baseline on Small Instances
=====================================================
Establishes optimality gap by running full exact solver on small N.
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

def run_solver_on_query(query_content: str, solver_flag: str, timeout: int = 300) -> Dict:
    """Run solver on a query and return results."""
    # Write query to dataset directory
    query_file = DATASET_DIR / "Query_285050.txt"
    with open(query_file, 'w') as f:
        f.write(query_content)
    
    # Compile and run from src directory (as run.sh does)
    src_dir = BASE_DIR / "src"
    
    cmd = [
        "java",
        "VRPLoadingUnloadingMain",
        str(BASE_DIR),  # ROOT_DIR as first argument
        solver_flag
    ]
    
    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(src_dir)  # Run from src directory
        )
        runtime_ms = (time.time() - start_time) * 1000
        
        output = result.stdout + result.stderr
        return parse_output(output, runtime_ms, solver_flag)
        
    except subprocess.TimeoutExpired:
        return {"served": 0, "lu_cost": 0, "distance": 0, "runtime_ms": timeout*1000, "timeout": True}
    except Exception as e:
        return {"served": 0, "lu_cost": 0, "distance": 0, "runtime_ms": 0, "error": str(e)}

def parse_output(output: str, runtime_ms: float, solver_flag: str) -> Dict:
    """Parse solver output."""
    result = {"served": 0, "lu_cost": 0, "distance": 0.0, "runtime_ms": runtime_ms, "timeout": False}
    
    # Parse from stdout
    match = re.search(r'Found solution:\s*(\d+)\s*requests,\s*LU cost:\s*(\d+),\s*Distance:\s*([\d.]+)', output)
    if match:
        result["served"] = int(match.group(1))
        result["lu_cost"] = int(match.group(2))
        result["distance"] = float(match.group(3))
        return result
    
    # Try parsing output file
    output_prefix = {
        "--cluster": "Output_",
        "--insertion": "OutputInsertion_",
        "--lifostack": "OutputLifo_",
        "--foodmatch": "OutputFoodMatch_"
    }.get(solver_flag, "Output_")
    
    output_file = DATASET_DIR / f"{output_prefix}285050.txt"
    if output_file.exists():
        try:
            with open(output_file, 'r') as f:
                content = f.read()
                # Parse output format
                lines = content.strip().split('\n')
                for line in lines:
                    if 'TotalReq' in line:
                        match = re.search(r'TotalReq[:\s]+(\d+)', line)
                        if match:
                            result["served"] = int(match.group(1))
                    if 'TotalLUCost' in line:
                        match = re.search(r'TotalLUCost[:\s]+(\d+)', line)
                        if match:
                            result["lu_cost"] = int(match.group(1))
        except:
            pass
    
    return result

def load_existing_queries(n: int, max_queries: int = 20) -> List[str]:
    """Load existing query files for given N."""
    query_dir = QUERIES_DIR / f"N_{n}"
    queries = []
    
    if query_dir.exists():
        # Find all .txt query files (not _meta.json)
        query_files = [f for f in query_dir.glob("query_*.txt") if '_meta' not in f.name]
        query_files = sorted(query_files, key=lambda x: int(re.search(r'query_(\d+)', x.name).group(1)))[:max_queries]
        for qf in query_files:
            with open(qf, 'r') as f:
                content = f.read()
                if content.strip():  # Only add non-empty queries
                    queries.append(content)
    
    return queries

def create_small_n_query(base_query: str, target_n: int) -> str:
    """Create a smaller query by taking first target_n services from base query."""
    lines = base_query.strip().split('\n')
    result_lines = []
    service_count = 0
    
    for line in lines:
        if line.startswith('D ') or line.startswith('C '):
            result_lines.append(line)
        elif line.startswith('S ') and service_count < target_n:
            result_lines.append(line)
            service_count += 1
    
    return '\n'.join(result_lines)

print("=" * 70)
print("EXPERIMENT 1: TRUE EXACT BASELINE ON SMALL INSTANCES")
print("=" * 70)
print()

# Load base queries from N=10
base_queries = load_existing_queries(10, max_queries=30)
print(f"Loaded {len(base_queries)} base queries from N=10")

# Test N values
N_VALUES = [5, 8, 10]
ALGORITHMS = [
    ("OptLoad", "--cluster"),
    ("Insertion", "--insertion"),
    ("ExactLIFO", "--lifostack"),
    ("FoodMatch", "--foodmatch")
]

results = {n: {} for n in N_VALUES}
NUM_QUERIES = 20
TIMEOUT = 300  # 5 minutes per query

for n in N_VALUES:
    print(f"\n{'='*50}")
    print(f"Running experiments for N={n}")
    print(f"{'='*50}")
    
    for algo_name, algo_flag in ALGORITHMS:
        print(f"\n  {algo_name}:")
        results[n][algo_name] = []
        
        for i, base_query in enumerate(base_queries[:NUM_QUERIES]):
            # Create query with exactly N services
            query = create_small_n_query(base_query, n)
            
            result = run_solver_on_query(query, algo_flag, timeout=TIMEOUT)
            results[n][algo_name].append(result)
            
            status = "TIMEOUT" if result.get("timeout") else f"{result['served']} served"
            print(f"    Query {i+1}: {status} ({result['runtime_ms']/1000:.2f}s)")
        
        # Calculate averages
        completed = [r for r in results[n][algo_name] if not r.get("timeout")]
        if completed:
            avg_served = sum(r["served"] for r in completed) / len(completed)
            avg_lu = sum(r["lu_cost"] for r in completed) / len(completed)
            avg_runtime = sum(r["runtime_ms"] for r in completed) / len(completed)
            completion_rate = len(completed) / NUM_QUERIES * 100
            print(f"    Summary: {avg_served:.1f} served, {avg_lu:.1f} LU, {avg_runtime/1000:.2f}s avg, {completion_rate:.0f}% complete")

# Save results
results_file = RESULTS_DIR / "experiment1_exact_baseline.json"
with open(results_file, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to: {results_file}")

# Generate summary table
print("\n" + "=" * 70)
print("EXPERIMENT 1 SUMMARY: OPTIMALITY GAP ANALYSIS")
print("=" * 70)

print(f"\n{'N':<6} {'Algorithm':<12} {'Completed':<12} {'Served':<12} {'LU Cost':<12} {'Runtime(s)':<12}")
print("-" * 66)

for n in N_VALUES:
    for algo_name, _ in ALGORITHMS:
        data = results[n][algo_name]
        completed = [r for r in data if not r.get("timeout")]
        if completed:
            avg_served = sum(r["served"] for r in completed) / len(completed)
            avg_lu = sum(r["lu_cost"] for r in completed) / len(completed)
            avg_runtime = sum(r["runtime_ms"] for r in completed) / len(completed) / 1000
            comp_rate = f"{len(completed)}/{len(data)}"
            print(f"{n:<6} {algo_name:<12} {comp_rate:<12} {avg_served:<12.1f} {avg_lu:<12.1f} {avg_runtime:<12.2f}")
        else:
            print(f"{n:<6} {algo_name:<12} {'0/'+str(len(data)):<12} {'-':<12} {'-':<12} {'-':<12}")
    print("-" * 66)

# Calculate optimality gaps
print("\nOPTIMALITY GAP (OptLoad vs competitors):")
for n in N_VALUES:
    optload_data = [r for r in results[n]["OptLoad"] if not r.get("timeout")]
    if optload_data:
        optload_avg = sum(r["served"] for r in optload_data) / len(optload_data)
        
        for algo_name, _ in ALGORITHMS:
            if algo_name != "OptLoad":
                other_data = [r for r in results[n][algo_name] if not r.get("timeout")]
                if other_data:
                    other_avg = sum(r["served"] for r in other_data) / len(other_data)
                    if other_avg > 0:
                        gap = (optload_avg - other_avg) / other_avg * 100
                        print(f"  N={n}: OptLoad vs {algo_name}: +{gap:.1f}% more requests")

print("\nExperiment 1 complete!")
