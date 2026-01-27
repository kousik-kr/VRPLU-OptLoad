#!/usr/bin/env python3
"""
Network Scalability Experiment Runner
======================================

Runs OptLoad, LIFO, and Insertion algorithms on:
- Oldenburg (6,105 nodes)
- California (21,048 nodes)
- London (285,050 nodes)

Compares: LU cost, served requests, and runtime.
"""

import subprocess
import os
import json
import time
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional

# Configuration
BASE_DIR = Path("/home/gunturi/VRPLU-OptLoad")
JAR_DIR = BASE_DIR / "target" / "classes"
RESULTS_DIR = BASE_DIR / "experiments" / "results" / "network_scalability"

# Datasets (only new datasets - London already has results)
DATASETS = {
    'oldenburg': {
        'node_count': 6105,
        'name': 'Oldenburg',
        'queries_dir': RESULTS_DIR / 'oldenburg' / 'queries'
    },
    'california': {
        'node_count': 21048,
        'name': 'California',
        'queries_dir': RESULTS_DIR / 'california' / 'queries'
    }
    # London results already exist from previous experiments
}

# Algorithms (run fast heuristics first)
ALGORITHMS = {
    'insertion': {'flag': '--insertion', 'name': 'Insertion', 'output_prefix': 'OutputInsertion_'},
    'lifo': {'flag': '--lifostack', 'name': 'ExactLIFO', 'output_prefix': 'OutputLifo_'},
    # 'optload': {'flag': '--cluster', 'name': 'OptLoad', 'output_prefix': 'Output_'},  # Very slow for full experiments
}


def parse_output(output: str) -> Dict:
    """Parse solver output to extract metrics."""
    result = {
        'served_requests': 0,
        'lu_cost': 0.0,
        'time_ms': 0.0,
        'status': 'unknown'
    }
    
    # Extract served requests - format: "Number of Successful Requests:X"
    match = re.search(r'Number of Successful Requests\s*:\s*(\d+)', output, re.IGNORECASE)
    if match:
        result['served_requests'] = int(match.group(1))
    
    # Extract LU cost - format: "L-U Cost:X"
    match = re.search(r'L-U\s+Cost\s*:\s*(-?[\d.]+)', output, re.IGNORECASE)
    if match:
        result['lu_cost'] = float(match.group(1))
    
    # Extract time - usually last number in output (in ms)
    lines = output.strip().split('\n')
    for line in reversed(lines):
        # Look for time at end of line
        match = re.search(r'([\d.]+)\s*$', line)
        if match:
            try:
                result['time_ms'] = float(match.group(1))
                break
            except ValueError:
                continue
    
    # Check for successful completion
    if result['served_requests'] > 0:
        result['status'] = 'success'
    elif result['lu_cost'] != 0:
        result['status'] = 'partial'
    
    return result


def run_single_experiment(dataset_key: str, algorithm_key: str, query_file: Path) -> Dict:
    """Run a single experiment."""
    dataset = DATASETS[dataset_key]
    algorithm = ALGORITHMS[algorithm_key]
    node_count = dataset['node_count']
    
    # Clear previous output file
    output_file = BASE_DIR / f"{algorithm['output_prefix']}{node_count}.txt"
    if output_file.exists():
        output_file.unlink()
    
    # Build command
    cmd = [
        'java', '-cp', str(JAR_DIR),
        'VRPLoadingUnloadingMain',
        f'--nodes={node_count}',
        algorithm['flag'],
        str(query_file)
    ]
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Read output from file
        output_content = ""
        if output_file.exists():
            with open(output_file, 'r') as f:
                output_content = f.read()
        
        # Parse output
        metrics = parse_output(output_content)
        
        # Use actual elapsed time if not found in output
        if metrics['time_ms'] == 0:
            metrics['time_ms'] = elapsed_time
        
        return {
            'dataset': dataset_key,
            'algorithm': algorithm_key,
            'query_file': query_file.name,
            'metrics': metrics,
            'raw_output': output_content[:1000],  # First 1000 chars
            'status': 'success' if result.returncode == 0 else 'error'
        }
        
    except subprocess.TimeoutExpired:
        return {
            'dataset': dataset_key,
            'algorithm': algorithm_key,
            'query_file': query_file.name,
            'metrics': {'status': 'timeout'},
            'status': 'timeout'
        }
    except Exception as e:
        return {
            'dataset': dataset_key,
            'algorithm': algorithm_key,
            'query_file': query_file.name,
            'metrics': {'status': 'error', 'error': str(e)},
            'status': 'error'
        }


def run_experiments():
    """Run all network scalability experiments."""
    print("=" * 70)
    print("NETWORK SCALABILITY EXPERIMENTS")
    print("=" * 70)
    
    all_results = []
    
    for dataset_key, dataset in DATASETS.items():
        queries_dir = dataset['queries_dir']
        
        if not queries_dir.exists():
            print(f"\n⚠ Skipping {dataset['name']}: queries directory not found")
            print(f"  Expected: {queries_dir}")
            continue
        
        # Get query files
        query_files = sorted(queries_dir.glob('query_*.txt'))
        query_files = [f for f in query_files if '_meta' not in f.name]
        
        if not query_files:
            print(f"\n⚠ Skipping {dataset['name']}: no query files found")
            continue
        
        print(f"\n{'='*60}")
        print(f"DATASET: {dataset['name']} ({dataset['node_count']:,} nodes)")
        print(f"Queries: {len(query_files)}")
        print(f"{'='*60}")
        
        for algorithm_key, algorithm in ALGORITHMS.items():
            print(f"\n  Algorithm: {algorithm['name']}")
            
            for i, query_file in enumerate(query_files[:20]):  # Run all 20 queries
                result = run_single_experiment(dataset_key, algorithm_key, query_file)
                all_results.append(result)
                
                # Progress indicator
                served = result['metrics'].get('served_requests', 0)
                lu_cost = result['metrics'].get('lu_cost', 0)
                time_ms = result['metrics'].get('time_ms', 0)
                
                print(f"    [{i+1:2d}/{len(query_files):2d}] {query_file.name}: "
                      f"served={served}, LU={lu_cost:.2f}, time={time_ms:.1f}ms")
    
    # Save results
    results_file = RESULTS_DIR / 'scalability_results.json'
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n\nResults saved to: {results_file}")
    
    # Generate summary
    generate_summary(all_results)
    
    return all_results


def generate_summary(results: List[Dict]):
    """Generate summary statistics."""
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)
    
    summary = {}
    
    for result in results:
        dataset = result['dataset']
        algorithm = result['algorithm']
        metrics = result['metrics']
        
        key = (dataset, algorithm)
        if key not in summary:
            summary[key] = {
                'served': [],
                'lu_cost': [],
                'time_ms': []
            }
        
        if metrics.get('served_requests', 0) > 0:
            summary[key]['served'].append(metrics['served_requests'])
            summary[key]['lu_cost'].append(metrics.get('lu_cost', 0))
            summary[key]['time_ms'].append(metrics.get('time_ms', 0))
    
    # Print summary table
    print(f"\n{'Dataset':<12} {'Algorithm':<12} {'Queries':<8} {'Avg Served':<12} {'Avg LU Cost':<12} {'Avg Time (ms)':<15}")
    print("-" * 75)
    
    for (dataset, algorithm), stats in sorted(summary.items()):
        if stats['served']:
            avg_served = sum(stats['served']) / len(stats['served'])
            avg_lu = sum(stats['lu_cost']) / len(stats['lu_cost'])
            avg_time = sum(stats['time_ms']) / len(stats['time_ms'])
            
            print(f"{dataset:<12} {algorithm:<12} {len(stats['served']):<8} "
                  f"{avg_served:<12.1f} {avg_lu:<12.2f} {avg_time:<15.1f}")
    
    # Save summary
    summary_file = RESULTS_DIR / 'scalability_summary.json'
    summary_data = {}
    for (dataset, algorithm), stats in summary.items():
        if dataset not in summary_data:
            summary_data[dataset] = {}
        if stats['served']:
            summary_data[dataset][algorithm] = {
                'count': len(stats['served']),
                'avg_served': sum(stats['served']) / len(stats['served']),
                'avg_lu_cost': sum(stats['lu_cost']) / len(stats['lu_cost']),
                'avg_time_ms': sum(stats['time_ms']) / len(stats['time_ms'])
            }
    
    with open(summary_file, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    print(f"\nSummary saved to: {summary_file}")


if __name__ == "__main__":
    run_experiments()
