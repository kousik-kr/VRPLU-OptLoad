#!/usr/bin/env python3
"""
Complete Experiment Runner for GeoInformatica Submission
=========================================================

This script runs ALL required experiments for the OptLoad paper:
- 4 algorithms: OptLoad, Insertion Heuristic, Exact LIFO, FoodMatch
- 6 N values: 10, 20, 40, 60, 80, 100  
- 100 queries per N value
- All metrics logged: LU cost, distance, served requests, runtime

Author: OptLoad Research Team
Date: January 2026
"""

import sys
import json
import time
import shutil
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import traceback

# === Configuration ===
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
QUERIES_DIR = EXPERIMENTS_DIR / "queries"
RESULTS_DIR = EXPERIMENTS_DIR / "results"
TARGET_DIR = PROJECT_ROOT / "target" / "classes"

# Algorithm configurations
ALGORITHMS = {
    "OptLoad": "--cluster",
    "Insertion": "--insertion",
    "ExactLIFO": "--lifostack",
    "FoodMatch": "--foodmatch",
}

# Output file prefixes for each algorithm
OUTPUT_PREFIXES = {
    "--cluster": "Output_",
    "--insertion": "OutputInsertion_",
    "--lifostack": "OutputLifo_",
    "--foodmatch": "OutputFoodMatch_",
}

N_VALUES = [10, 20, 40, 60, 80, 100]
QUERIES_PER_N = 100
TIMEOUT_SECONDS = 300  # 5 minutes per query
VERTEX_COUNT = 285050


@dataclass
class ExperimentResult:
    """Result from running an algorithm on a query."""
    query_id: str
    algorithm: str
    n_value: int
    success: bool
    served_requests: int = 0
    total_requests: int = 0
    lu_cost: int = 0
    distance: float = 0.0
    runtime_ms: int = 0
    capacity: int = 0
    pareto_size: int = 1
    error_message: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def compile_java() -> bool:
    """Compile Java sources."""
    print("Compiling Java sources...")
    src_dir = PROJECT_ROOT / "src"
    java_files = list(src_dir.glob("*.java"))
    
    if not java_files:
        print("ERROR: No Java files found")
        return False
    
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    
    cmd = ["javac", "-d", str(TARGET_DIR), "-sourcepath", str(src_dir)] + \
          [str(f) for f in java_files]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print("✓ Compilation successful")
            return True
        else:
            print(f"✗ Compilation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Compilation error: {e}")
        return False


def run_solver(query_file: Path, solver_flag: str, timeout: int = TIMEOUT_SECONDS) -> Tuple[bool, str, int]:
    """
    Run a solver on a query file.
    Returns: (success, output, runtime_ms)
    """
    expected_query_path = PROJECT_ROOT / f"Query_{VERTEX_COUNT}.txt"
    start_time = time.time()
    
    try:
        # Copy query to expected location
        shutil.copy(query_file, expected_query_path)
        
        # Run solver
        cmd = [
            "java", "-Xmx8g", "-Xms2g",
            "-cp", str(TARGET_DIR),
            "VRPLoadingUnloadingMain",
            str(PROJECT_ROOT),
            solver_flag
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_ROOT
        )
        
        runtime_ms = int((time.time() - start_time) * 1000)
        
        # Read output file
        output_prefix = OUTPUT_PREFIXES.get(solver_flag, "Output_")
        output_file = PROJECT_ROOT / f"{output_prefix}{VERTEX_COUNT}.txt"
        
        output = result.stdout + result.stderr
        if output_file.exists():
            with open(output_file, 'r') as f:
                output += "\n--- OUTPUT FILE ---\n" + f.read()
        
        return True, output, runtime_ms
        
    except subprocess.TimeoutExpired:
        runtime_ms = int((time.time() - start_time) * 1000)
        return False, f"Timeout after {timeout}s", runtime_ms
    except Exception as e:
        runtime_ms = int((time.time() - start_time) * 1000)
        return False, str(e), runtime_ms
    finally:
        # Clean up
        if expected_query_path.exists():
            expected_query_path.unlink()


def parse_output(output: str, algorithm: str, query_id: str, n_value: int, 
                 runtime_ms: int) -> ExperimentResult:
    """Parse solver output and extract metrics."""
    
    result = ExperimentResult(
        query_id=query_id,
        algorithm=algorithm,
        n_value=n_value,
        success=False,
        runtime_ms=runtime_ms,
        timestamp=datetime.now().isoformat()
    )
    
    try:
        # Count Pareto solutions (number of lines with "Number of Successful Requests")
        pareto_matches = re.findall(r"Number of Successful Requests:(\d+)", output)
        if pareto_matches:
            result.pareto_size = len(pareto_matches)
            # Take the best (max served requests)
            served_list = [int(m) for m in pareto_matches]
            best_idx = served_list.index(max(served_list))
            result.served_requests = served_list[best_idx]
        
        # Parse output file content (take last/best result)
        # Format: [Route...]\tNumber of Successful Requests:X\tL-U Cost:Y\tDistance:Z
        match = re.search(
            r"Number of Successful Requests:(\d+)\s*L-U Cost:(\d+)\s*Distance:([\d.]+)",
            output
        )
        if match:
            result.served_requests = int(match.group(1))
            result.lu_cost = int(match.group(2))
            result.distance = float(match.group(3))
            result.success = True
        
        # Find best solution (max requests served)
        all_results = re.findall(
            r"Number of Successful Requests:(\d+)\s*L-U Cost:(\d+)\s*Distance:([\d.]+)",
            output
        )
        if all_results:
            # Find the one with max served requests
            best = max(all_results, key=lambda x: int(x[0]))
            result.served_requests = int(best[0])
            result.lu_cost = int(best[1])
            result.distance = float(best[2])
            result.success = True
        
        # Parse runtime from Java output if available
        time_match = re.search(r"in\s*(\d+)\s*ms", output)
        if time_match:
            result.runtime_ms = int(time_match.group(1))
        
        # Parse capacity
        cap_match = re.search(r"capacity.*to\s*(\d+)", output, re.IGNORECASE)
        if cap_match:
            result.capacity = int(cap_match.group(1))
        
        # Count total requests (services)
        services = re.findall(r"Added service \d+", output)
        if services:
            result.total_requests = len(services)
        else:
            result.total_requests = n_value
        
        # Check for errors
        if "Exception" in output or "Error" in output:
            error_match = re.search(r"(Exception|Error)[^\n]*", output)
            if error_match:
                result.error_message = error_match.group(0)[:200]
        
        if "Timeout" in output:
            result.error_message = "Timeout"
            result.success = False
            
    except Exception as e:
        result.error_message = f"Parse error: {str(e)}"
    
    return result


def run_single_experiment(args: Tuple) -> ExperimentResult:
    """Run a single experiment (for parallel execution)."""
    query_file, algo_name, algo_flag, query_id, n_value = args
    
    success, output, runtime = run_solver(Path(query_file), algo_flag, TIMEOUT_SECONDS)
    result = parse_output(output, algo_name, query_id, n_value, runtime)
    
    if not success and "Timeout" in output:
        result.error_message = "Timeout"
    
    return result


def load_query_index() -> Dict[str, str]:
    """Load the query index file."""
    index_file = QUERIES_DIR / "query_index.json"
    if not index_file.exists():
        print("ERROR: Query index not found. Run query generation first.")
        sys.exit(1)
    
    with open(index_file, 'r') as f:
        return json.load(f)


def save_results(results: Dict[str, dict], filename: str = "experiment_results.json"):
    """Save results to JSON file."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / filename, 'w') as f:
        json.dump(results, f, indent=2)


def run_all_experiments():
    """Run all experiments."""
    print("=" * 60)
    print("OptLoad Complete Experiment Suite")
    print("=" * 60)
    print(f"Start time: {datetime.now().isoformat()}")
    print(f"Algorithms: {list(ALGORITHMS.keys())}")
    print(f"N values: {N_VALUES}")
    print(f"Queries per N: {QUERIES_PER_N}")
    print(f"Timeout: {TIMEOUT_SECONDS}s per query")
    print("=" * 60)
    
    # Compile Java
    if not compile_java():
        print("ERROR: Failed to compile Java sources")
        return
    
    # Load query index
    query_index = load_query_index()
    print(f"Loaded {len(query_index)} queries")
    
    # Organize queries by N value
    queries_by_n = {n: [] for n in N_VALUES}
    for query_key, query_path in query_index.items():
        # Parse N value from query key (e.g., "N10_R1" -> 10)
        match = re.match(r"N(\d+)_R(\d+)", query_key)
        if match:
            n_val = int(match.group(1))
            if n_val in queries_by_n:
                queries_by_n[n_val].append((query_key, query_path))
    
    # Results storage
    all_results = {}
    total_experiments = sum(len(q) for q in queries_by_n.values()) * len(ALGORITHMS)
    completed = 0
    
    start_time = time.time()
    
    # Run experiments for each N value
    for n_value in N_VALUES:
        queries = queries_by_n[n_value]
        if not queries:
            print(f"\n⚠ No queries found for N={n_value}")
            continue
        
        print(f"\n{'='*60}")
        print(f"Running experiments for N={n_value} ({len(queries)} queries)")
        print(f"{'='*60}")
        
        for algo_name, algo_flag in ALGORITHMS.items():
            print(f"\n  Algorithm: {algo_name}")
            algo_start = time.time()
            algo_results = []
            
            for i, (query_key, query_path) in enumerate(queries):
                # Run experiment
                success, output, runtime = run_solver(Path(query_path), algo_flag)
                result = parse_output(output, algo_name, query_key, n_value, runtime)
                
                # Store result
                result_key = f"{query_key}_{algo_name}"
                all_results[result_key] = result.to_dict()
                algo_results.append(result)
                
                completed += 1
                
                # Progress update every 10 queries
                if (i + 1) % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    eta = (total_experiments - completed) / rate if rate > 0 else 0
                    print(f"    Progress: {i+1}/{len(queries)} | "
                          f"Total: {completed}/{total_experiments} | "
                          f"ETA: {eta/60:.1f}min")
            
            # Summary for this algorithm
            successful = [r for r in algo_results if r.success and r.served_requests > 0]
            if successful:
                avg_served = sum(r.served_requests for r in successful) / len(successful)
                avg_lu = sum(r.lu_cost for r in successful) / len(successful)
                avg_time = sum(r.runtime_ms for r in algo_results) / len(algo_results)
                print(f"    Summary: {len(successful)}/{len(algo_results)} successful | "
                      f"Avg served: {avg_served:.1f} | Avg LU: {avg_lu:.1f} | "
                      f"Avg time: {avg_time:.0f}ms")
            else:
                print(f"    Summary: 0/{len(algo_results)} successful")
            
            # Save intermediate results
            save_results(all_results)
    
    # Final summary
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"EXPERIMENT COMPLETE")
    print(f"{'='*60}")
    print(f"Total experiments: {completed}")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Results saved to: {RESULTS_DIR / 'experiment_results.json'}")
    
    # Generate summary
    generate_summary(all_results)


def generate_summary(results: Dict[str, dict]):
    """Generate experiment summary statistics."""
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    
    summary = {}
    
    for n_value in N_VALUES:
        summary[n_value] = {}
        for algo_name in ALGORITHMS.keys():
            algo_results = [
                v for k, v in results.items() 
                if v['algorithm'] == algo_name and v['n_value'] == n_value
            ]
            
            if not algo_results:
                continue
            
            successful = [r for r in algo_results if r['success'] and r['served_requests'] > 0]
            
            if successful:
                served = [r['served_requests'] for r in successful]
                lu_costs = [r['lu_cost'] for r in successful]
                runtimes = [r['runtime_ms'] for r in algo_results]
                
                summary[n_value][algo_name] = {
                    'count': len(successful),
                    'total': len(algo_results),
                    'served_mean': sum(served) / len(served),
                    'served_std': (sum((x - sum(served)/len(served))**2 for x in served) / len(served)) ** 0.5,
                    'lu_cost_mean': sum(lu_costs) / len(lu_costs),
                    'lu_cost_std': (sum((x - sum(lu_costs)/len(lu_costs))**2 for x in lu_costs) / len(lu_costs)) ** 0.5,
                    'runtime_mean': sum(runtimes) / len(runtimes),
                }
            else:
                summary[n_value][algo_name] = {
                    'count': 0,
                    'total': len(algo_results),
                    'served_mean': 0,
                    'served_std': 0,
                    'lu_cost_mean': 0,
                    'lu_cost_std': 0,
                    'runtime_mean': sum(r['runtime_ms'] for r in algo_results) / len(algo_results) if algo_results else 0,
                }
    
    # Print summary table
    print("\nRequests Served (Mean ± Std):")
    print(f"{'N':>5} | " + " | ".join(f"{a:>15}" for a in ALGORITHMS.keys()))
    print("-" * 80)
    for n_value in N_VALUES:
        row = f"{n_value:>5} | "
        for algo_name in ALGORITHMS.keys():
            if algo_name in summary.get(n_value, {}):
                s = summary[n_value][algo_name]
                row += f"{s['served_mean']:>6.1f}±{s['served_std']:>5.1f} | "
            else:
                row += f"{'N/A':>15} | "
        print(row)
    
    print("\nL-U Cost (Mean ± Std):")
    print(f"{'N':>5} | " + " | ".join(f"{a:>15}" for a in ALGORITHMS.keys()))
    print("-" * 80)
    for n_value in N_VALUES:
        row = f"{n_value:>5} | "
        for algo_name in ALGORITHMS.keys():
            if algo_name in summary.get(n_value, {}):
                s = summary[n_value][algo_name]
                row += f"{s['lu_cost_mean']:>6.1f}±{s['lu_cost_std']:>5.1f} | "
            else:
                row += f"{'N/A':>15} | "
        print(row)
    
    print("\nRuntime (Mean in seconds):")
    print(f"{'N':>5} | " + " | ".join(f"{a:>15}" for a in ALGORITHMS.keys()))
    print("-" * 80)
    for n_value in N_VALUES:
        row = f"{n_value:>5} | "
        for algo_name in ALGORITHMS.keys():
            if algo_name in summary.get(n_value, {}):
                s = summary[n_value][algo_name]
                row += f"{s['runtime_mean']/1000:>14.2f}s | "
            else:
                row += f"{'N/A':>15} | "
        print(row)
    
    # Save summary
    with open(RESULTS_DIR / "experiment_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to: {RESULTS_DIR / 'experiment_summary.json'}")


if __name__ == "__main__":
    run_all_experiments()
