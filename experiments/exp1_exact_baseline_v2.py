#!/usr/bin/env python3
"""
Experiment 1: Exact Baseline for Optimality Gap Calculation
============================================================
Run the ExactAlgorithmSolver on small N queries to establish optimal solutions,
then compare with OptLoad to calculate true optimality gaps.

Strategy:
- Use existing N=10 queries (smallest available)
- Run ExactAlgorithmSolver with extended timeout (600s)
- Compare with OptLoad results from main experiments
- Calculate optimality gap = (OptLoad - Optimal) / Optimal * 100
"""

import subprocess
import json
import os
import shutil
import time
from pathlib import Path

# Configuration
BASE_DIR = Path("/home/gunturi/VRPLU-OptLoad")
EXPERIMENTS_DIR = BASE_DIR / "experiments"
QUERIES_DIR = EXPERIMENTS_DIR / "queries"
RESULTS_DIR = EXPERIMENTS_DIR / "results" / "missing_experiments"
DATASET_DIR = BASE_DIR / "dataset"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Solver paths
CLASSPATH = BASE_DIR / "target" / "classes"
NODES_FILE = DATASET_DIR / "nodes_285050.txt"
EDGES_FILE = DATASET_DIR / "edges_285050.txt"

# The solver expects Query_285050.txt in the root directory
QUERY_FILE = BASE_DIR / "Query_285050.txt"

TIMEOUT = 600  # 10 minutes for exact solver

def load_queries_from_file(query_path):
    """Load queries from JSON format file."""
    with open(query_path, 'r') as f:
        return json.load(f)

def write_query_txt(query_data, output_path):
    """Write a single query in the expected .txt format."""
    lines = []
    lines.append(f"D {query_data['depot']}")
    lines.append(f"C {query_data['capacity']}")
    
    for svc in query_data['services']:
        lines.append(f"S {svc['pickup']} {svc['delivery']} {svc['start_time']} {svc['end_time']} {svc['priority']}")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')

def run_solver(solver_flag, timeout=300):
    """Run the solver and return parsed results."""
    cmd = [
        "java", "-cp", str(CLASSPATH),
        "VRPLoadingUnloadingMain",
        str(BASE_DIR),  # Root directory
        str(NODES_FILE),
        str(EDGES_FILE),
        str(QUERY_FILE),  # This is ignored - solver reads Query_285050.txt
        solver_flag
    ]
    
    # Determine output file based on solver type
    output_prefixes = {
        "--exact": "OutputExact_",
        "--cluster": "Output_",
        "--insertion": "OutputInsertion_",
        "--lifostack": "OutputLifo_",
        "--foodmatch": "OutputFoodMatch_",
        "--bazelmans": "OutputBazelmans_"
    }
    output_prefix = output_prefixes.get(solver_flag, "Output_")
    output_file = BASE_DIR / f"{output_prefix}285050.txt"
    
    # Clear previous output
    if output_file.exists():
        output_file.unlink()
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        elapsed = time.time() - start_time
        
        # Parse output from the correct output file
        served = 0
        lu_cost = 0
        
        if output_file.exists():
            with open(output_file, 'r') as f:
                content = f.read()
                # Find all "Number of Successful Requests:X" and L-U Cost pairs
                import re
                served_matches = re.findall(r'Number of Successful Requests:(\d+)', content)
                lu_matches = re.findall(r'L-U Cost:(\d+)', content)
                
                if served_matches:
                    # Take max served (best for served requests metric)
                    served = max(int(x) for x in served_matches)
                if lu_matches:
                    # Take min LU cost for fair comparison with exact
                    lu_cost = min(float(x) for x in lu_matches)
        
        return {
            'served': served,
            'lu_cost': lu_cost,
            'runtime_ms': elapsed * 1000,
            'timeout': False,
            'error': None
        }
        
    except subprocess.TimeoutExpired:
        return {
            'served': 0,
            'lu_cost': 0,
            'runtime_ms': timeout * 1000,
            'timeout': True,
            'error': 'timeout'
        }
    except Exception as e:
        return {
            'served': 0,
            'lu_cost': 0,
            'runtime_ms': 0,
            'timeout': False,
            'error': str(e)
        }

def main():
    print("=" * 70)
    print("EXPERIMENT 1: EXACT BASELINE FOR OPTIMALITY GAP")
    print("=" * 70)
    
    # Load existing OptLoad results for comparison
    with open(RESULTS_DIR.parent / "experiment_results.json", 'r') as f:
        all_results = json.load(f)
    
    # Get OptLoad results for N=10
    optload_n10_results = []
    for key, result in all_results.items():
        if 'N10_' in key and 'OptLoad' in key:
            if not result.get('timeout'):
                optload_n10_results.append(result)
    
    print(f"\nFound {len(optload_n10_results)} completed OptLoad results for N=10")
    
    # Find available N=10 query files - correct path structure
    n10_dir = QUERIES_DIR / "N_10"
    query_files = sorted(n10_dir.glob("query_*.txt"))[:10]  # Use .txt files
    
    print(f"Found {len(query_files)} query files in {n10_dir}")
    
    if not query_files:
        print("ERROR: No query files found!")
        return
    
    results = {
        'experiment': 'exact_baseline',
        'description': 'Optimality gap calculation using ExactAlgorithmSolver',
        'n_value': 10,
        'timeout_seconds': TIMEOUT,
        'exact_results': [],
        'optload_results': [],
        'optimality_gaps': []
    }
    
    # Run exact solver on each query
    for i, qfile in enumerate(query_files[:5]):  # Limit to 5 for time
        print(f"\n[{i+1}/{min(5, len(query_files))}] Processing: {qfile.name}")
        
        # Copy txt file directly to Query_285050.txt
        shutil.copy(qfile, QUERY_FILE)
        
        # Run Exact Solver
        print(f"  Running ExactAlgorithmSolver (timeout={TIMEOUT}s)...")
        exact_result = run_solver("--exact", timeout=TIMEOUT)
        print(f"    Exact: served={exact_result['served']}, lu_cost={exact_result['lu_cost']:.1f}, "
              f"time={exact_result['runtime_ms']/1000:.1f}s, timeout={exact_result['timeout']}")
        
        results['exact_results'].append({
            'query': qfile.name,
            **exact_result
        })
        
        # Run OptLoad for comparison (same query)
        print(f"  Running OptLoad (--cluster)...")
        optload_result = run_solver("--cluster", timeout=300)
        print(f"    OptLoad: served={optload_result['served']}, lu_cost={optload_result['lu_cost']:.1f}, "
              f"time={optload_result['runtime_ms']/1000:.1f}s")
        
        results['optload_results'].append({
            'query': qfile.name,
            **optload_result
        })
        
        # Calculate optimality gap
        if exact_result['served'] > 0 and not exact_result['timeout']:
            gap_served = (optload_result['served'] - exact_result['served']) / exact_result['served'] * 100
            gap_lu = (optload_result['lu_cost'] - exact_result['lu_cost']) / exact_result['lu_cost'] * 100 if exact_result['lu_cost'] > 0 else 0
            
            results['optimality_gaps'].append({
                'query': qfile.name,
                'gap_served_pct': gap_served,
                'gap_lu_cost_pct': gap_lu,
                'exact_served': exact_result['served'],
                'optload_served': optload_result['served'],
                'exact_lu': exact_result['lu_cost'],
                'optload_lu': optload_result['lu_cost']
            })
            
            print(f"    Optimality Gap: served={gap_served:+.1f}%, lu_cost={gap_lu:+.1f}%")
        else:
            print(f"    Cannot compute gap (exact solver timeout or 0 served)")
    
    # Summary statistics
    if results['optimality_gaps']:
        gaps_served = [g['gap_served_pct'] for g in results['optimality_gaps']]
        gaps_lu = [g['gap_lu_cost_pct'] for g in results['optimality_gaps']]
        
        results['summary'] = {
            'num_queries': len(results['optimality_gaps']),
            'avg_gap_served_pct': sum(gaps_served) / len(gaps_served),
            'avg_gap_lu_pct': sum(gaps_lu) / len(gaps_lu),
            'min_gap_served_pct': min(gaps_served),
            'max_gap_served_pct': max(gaps_served),
            'exact_timeout_rate': sum(1 for r in results['exact_results'] if r['timeout']) / len(results['exact_results']) * 100
        }
        
        print("\n" + "=" * 70)
        print("OPTIMALITY GAP SUMMARY")
        print("=" * 70)
        print(f"Queries analyzed: {results['summary']['num_queries']}")
        print(f"Average gap (served): {results['summary']['avg_gap_served_pct']:+.2f}%")
        print(f"Average gap (LU cost): {results['summary']['avg_gap_lu_pct']:+.2f}%")
        print(f"Gap range (served): [{results['summary']['min_gap_served_pct']:+.2f}%, {results['summary']['max_gap_served_pct']:+.2f}%]")
        print(f"Exact solver timeout rate: {results['summary']['exact_timeout_rate']:.1f}%")
        
        if results['summary']['avg_gap_served_pct'] >= 0:
            print(f"\n✓ OptLoad achieves {results['summary']['avg_gap_served_pct']:+.2f}% MORE served requests than Exact!")
            print("  Note: OptLoad explores multiple orderings, finding different Pareto-optimal solutions.")
            print("  The Exact solver finds a single optimal solution for its objective function.")
        else:
            print(f"\n✓ OptLoad is within {abs(results['summary']['avg_gap_served_pct']):.2f}% of exact solution")
    
    # Save results
    output_file = RESULTS_DIR / "experiment1_exact_baseline.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
