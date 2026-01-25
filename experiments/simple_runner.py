#!/usr/bin/env python3
"""
Simple Batch Experiment Runner
Runs experiments without issues with terminal interrupts.
"""

import sys
import json
import time
import shutil
import subprocess
import re
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

# Paths
PROJECT_ROOT = Path("/home/gunturi/VRPLU-OptLoad")
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
QUERIES_DIR = EXPERIMENTS_DIR / "queries"
RESULTS_DIR = EXPERIMENTS_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_DIR = PROJECT_ROOT / "target" / "classes"
RESULTS_FILE = RESULTS_DIR / "experiment_results.json"


@dataclass
class Result:
    query_id: str
    algorithm: str
    success: bool
    served_requests: int = 0
    lu_cost: int = 0
    distance: float = 0.0
    runtime_ms: int = 0
    error: str = ""


ALGORITHMS = {
    "Insertion": "--insertion",
    "OptLoad": "--cluster",
    "ExactLIFO": "--lifostack",
    "Bazelmans": "--bazelmans",
    "FoodMatch": "--foodmatch",
}


def load_existing_results():
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_results(results):
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)


def get_output_prefix(flag):
    prefixes = {
        "--exact": "OutputExact_",
        "--lifostack": "OutputLifo_",
        "--insertion": "OutputInsertion_",
        "--cluster": "Output_",
        "--foodmatch": "OutputFoodMatch_",
        "--bazelmans": "OutputBazelmans_",
    }
    return prefixes.get(flag, "Output_")


def run_single_experiment(query_path, algo_name, algo_flag, timeout=120):
    """Run a single experiment and return results."""
    vertex_count = 285050
    expected_query = PROJECT_ROOT / f"Query_{vertex_count}.txt"
    
    start = time.time()
    
    try:
        # Copy query
        shutil.copy(query_path, expected_query)
        
        # Run solver
        cmd = [
            "java", "-Xmx8g", "-Xms2g",
            "-cp", str(TARGET_DIR),
            "VRPLoadingUnloadingMain",
            str(PROJECT_ROOT),
            algo_flag
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_ROOT
        )
        
        runtime = int((time.time() - start) * 1000)
        
        # Read output file
        prefix = get_output_prefix(algo_flag)
        output_file = PROJECT_ROOT / f"{prefix}{vertex_count}.txt"
        
        output = ""
        if output_file.exists():
            with open(output_file, 'r') as f:
                output = f.read()
        
        # Parse results
        served, lu_cost, distance = 0, 0, 0.0
        match = re.search(
            r"Number of Successful Requests:(\d+)\s*L-U Cost:(\d+)\s*Distance:([\d.]+)",
            output
        )
        if match:
            served = int(match.group(1))
            lu_cost = int(match.group(2))
            distance = float(match.group(3))
        
        return Result(
            query_id="",
            algorithm=algo_name,
            success=True,
            served_requests=served,
            lu_cost=lu_cost,
            distance=distance,
            runtime_ms=runtime
        )
        
    except subprocess.TimeoutExpired:
        return Result(query_id="", algorithm=algo_name, success=False,
                     runtime_ms=int((time.time()-start)*1000), error="Timeout")
    except Exception as e:
        return Result(query_id="", algorithm=algo_name, success=False,
                     runtime_ms=int((time.time()-start)*1000), error=str(e))
    finally:
        if expected_query.exists():
            expected_query.unlink()


def main():
    print("="*60)
    print("VRP-LU Batch Experiment Runner")
    print("="*60)
    
    # Load query index
    query_index_file = QUERIES_DIR / "query_index.json"
    if not query_index_file.exists():
        print("ERROR: Query index not found!")
        return
    
    with open(query_index_file, 'r') as f:
        query_index = json.load(f)
    
    print(f"Found {len(query_index)} queries")
    
    # Select algorithms (customize as needed)
    algos_to_run = ["Insertion", "OptLoad"]
    # algos_to_run = list(ALGORITHMS.keys())  # All algorithms
    
    print(f"Running: {algos_to_run}")
    
    # Load existing results
    results = load_existing_results()
    print(f"Already completed: {len(results)}")
    
    total = len(query_index) * len(algos_to_run)
    completed = 0
    skipped = 0
    
    start_time = time.time()
    
    for query_id, query_path in query_index.items():
        query_path = Path(query_path)
        
        if not query_path.exists():
            print(f"WARN: Missing query file: {query_path}")
            continue
        
        for algo_name in algos_to_run:
            experiment_key = f"{query_id}_{algo_name}"
            
            # Skip if done
            if experiment_key in results:
                skipped += 1
                continue
            
            # Run experiment
            flag = ALGORITHMS[algo_name]
            result = run_single_experiment(query_path, algo_name, flag)
            result.query_id = query_id
            
            # Store
            results[experiment_key] = asdict(result)
            completed += 1
            
            # Progress
            if completed % 10 == 0:
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                remaining = (total - len(results)) / rate if rate > 0 else 0
                print(f"Progress: {len(results)}/{total} "
                      f"({100*len(results)/total:.1f}%) "
                      f"Rate: {rate:.2f}/s "
                      f"ETA: {remaining/60:.1f}min")
                
                # Save periodically
                save_results(results)
    
    # Final save
    save_results(results)
    
    elapsed = time.time() - start_time
    print(f"\nCompleted {completed} new experiments in {elapsed/60:.1f} minutes")
    print(f"Total results: {len(results)}")
    print(f"Results saved to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
