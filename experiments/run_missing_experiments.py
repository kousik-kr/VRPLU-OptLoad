#!/usr/bin/env python3
"""
Missing Experiments for GeoInformatica Submission
=================================================
This script implements 5 critical experiments:
1. True Exact Baseline on Small N (optimality gap)
2. OptLoad Component Ablation (C, LU, TW, P)
3. Pareto-Front Quality Visualization
4. Explicit Feasibility Validation
5. Capacity Sensitivity Analysis
"""

import subprocess
import os
import json
import re
import time
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import shutil

# Configuration
BASE_DIR = Path("/home/gunturi/VRPLU-OptLoad")
EXPERIMENTS_DIR = BASE_DIR / "experiments"
RESULTS_DIR = EXPERIMENTS_DIR / "results" / "missing_experiments"
QUERIES_DIR = EXPERIMENTS_DIR / "queries"
DATASET_DIR = BASE_DIR / "dataset"

# Create results directory
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def run_solver(query_file: str, solver_flag: str, timeout: int = 300) -> Dict:
    """Run a solver and parse output."""
    cmd = [
        "java", "-cp", str(BASE_DIR / "target" / "classes"),
        "VRPLoadingUnloadingMain",
        str(DATASET_DIR),
        solver_flag
    ]
    
    # Copy query file to dataset directory
    query_dest = DATASET_DIR / f"Query_285050.txt"
    shutil.copy(query_file, query_dest)
    
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
        return parse_solver_output(output, runtime_ms)
        
    except subprocess.TimeoutExpired:
        return {
            "served": 0,
            "lu_cost": 0,
            "distance": 0,
            "runtime_ms": timeout * 1000,
            "timeout": True,
            "error": None
        }
    except Exception as e:
        return {
            "served": 0,
            "lu_cost": 0,
            "distance": 0,
            "runtime_ms": 0,
            "timeout": False,
            "error": str(e)
        }

def parse_solver_output(output: str, runtime_ms: float) -> Dict:
    """Parse solver output to extract metrics."""
    result = {
        "served": 0,
        "lu_cost": 0,
        "distance": 0.0,
        "runtime_ms": runtime_ms,
        "timeout": False,
        "error": None
    }
    
    # Look for solution lines
    # Format: "Found solution: X requests, LU cost: Y, Distance: Z"
    match = re.search(r'Found solution:\s*(\d+)\s*requests,\s*LU cost:\s*(\d+),\s*Distance:\s*([\d.]+)', output)
    if match:
        result["served"] = int(match.group(1))
        result["lu_cost"] = int(match.group(2))
        result["distance"] = float(match.group(3))
    
    # Also try parsing from output file
    output_files = list(DATASET_DIR.glob("Output*.txt"))
    for ofile in output_files:
        try:
            with open(ofile, 'r') as f:
                content = f.read()
                # Parse TotalReq, TotalLUCost, Distance patterns
                req_match = re.search(r'TotalReq[:\s]+(\d+)', content)
                lu_match = re.search(r'TotalLUCost[:\s]+(\d+)', content)
                dist_match = re.search(r'Distance[:\s]+([\d.]+)', content)
                
                if req_match:
                    result["served"] = max(result["served"], int(req_match.group(1)))
                if lu_match:
                    result["lu_cost"] = max(result["lu_cost"], int(lu_match.group(1)))
                if dist_match:
                    result["distance"] = max(result["distance"], float(dist_match.group(1)))
        except:
            pass
    
    return result

def generate_small_queries(n_values: List[int], num_queries: int = 20) -> Dict[int, List[str]]:
    """Generate small query files for exact baseline experiments."""
    small_queries_dir = RESULTS_DIR / "small_queries"
    small_queries_dir.mkdir(exist_ok=True)
    
    queries = {}
    
    for n in n_values:
        queries[n] = []
        # Try to use existing queries if available, or generate new ones
        existing_query_dir = QUERIES_DIR / f"N_{n}"
        
        if existing_query_dir.exists():
            query_files = sorted(existing_query_dir.glob("query_*.txt"))[:num_queries]
            for qf in query_files:
                queries[n].append(str(qf))
        else:
            # Generate simple queries for very small N
            for i in range(num_queries):
                query_file = small_queries_dir / f"query_n{n}_{i+1}.txt"
                generate_simple_query(query_file, n)
                queries[n].append(str(query_file))
    
    return queries

def generate_simple_query(output_file: Path, n: int):
    """Generate a simple query file with n services."""
    # Use a fixed depot and generate random services
    depot_node = 1  # Use node 1 as depot
    
    with open(output_file, 'w') as f:
        f.write(f"D {depot_node}\n")
        f.write(f"C 10\n")  # Capacity 10
        
        # Generate n services with reasonable nodes and time windows
        for i in range(n):
            pickup_node = random.randint(1000, 10000)
            delivery_node = random.randint(10000, 20000)
            # Time windows within depot hours (540-1140)
            pickup_start = 540 + random.randint(0, 300)
            pickup_end = pickup_start + random.randint(60, 180)
            delivery_start = pickup_end + random.randint(30, 120)
            delivery_end = min(delivery_start + random.randint(60, 180), 1140)
            quantity = random.randint(1, 3)
            
            f.write(f"S {pickup_node},{delivery_node} [{pickup_start},{pickup_end}] [{delivery_start},{delivery_end}] {quantity}\n")

print("=" * 70)
print("MISSING EXPERIMENTS FOR GEOINFORMATICA")
print("=" * 70)
print(f"Results will be saved to: {RESULTS_DIR}")
print()

# Check if Java is compiled
if not (BASE_DIR / "target" / "classes" / "VRPLoadingUnloadingMain.class").exists():
    print("ERROR: Java classes not compiled. Run 'mvn compile' first.")
    exit(1)

print("Java classes found. Ready to run experiments.")
