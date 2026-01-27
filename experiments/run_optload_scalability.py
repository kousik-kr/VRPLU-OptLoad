#!/usr/bin/env python3
"""
Run OptLoad on Oldenburg and California (5 queries each for reasonable runtime).
"""

import subprocess
import json
import time
import re
from pathlib import Path

BASE_DIR = Path("/home/gunturi/VRPLU-OptLoad")
JAR_DIR = BASE_DIR / "target" / "classes"
RESULTS_DIR = BASE_DIR / "experiments" / "results" / "network_scalability"

DATASETS = {
    'oldenburg': {'node_count': 6105, 'name': 'Oldenburg'},
    'california': {'node_count': 21048, 'name': 'California'}
}

def parse_output(output: str):
    result = {'served_requests': 0, 'lu_cost': 0.0, 'time_ms': 0.0}
    
    match = re.search(r'Number of Successful Requests\s*:\s*(\d+)', output)
    if match:
        result['served_requests'] = int(match.group(1))
    
    match = re.search(r'L-U\s+Cost\s*:\s*(-?[\d.]+)', output)
    if match:
        result['lu_cost'] = float(match.group(1))
    
    lines = output.strip().split('\n')
    for line in reversed(lines):
        match = re.search(r'([\d.]+)\s*$', line)
        if match:
            try:
                result['time_ms'] = float(match.group(1))
                break
            except:
                pass
    
    return result

def run_optload(dataset_key, query_file):
    dataset = DATASETS[dataset_key]
    node_count = dataset['node_count']
    
    output_file = BASE_DIR / f"Output_{node_count}.txt"
    if output_file.exists():
        output_file.unlink()
    
    cmd = [
        'java', '-cp', str(JAR_DIR),
        'VRPLoadingUnloadingMain',
        f'--nodes={node_count}',
        '--cluster',
        str(query_file)
    ]
    
    start = time.time()
    result = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True, timeout=600)
    elapsed = (time.time() - start) * 1000
    
    output_content = ""
    if output_file.exists():
        with open(output_file, 'r') as f:
            output_content = f.read()
    
    metrics = parse_output(output_content)
    if metrics['time_ms'] == 0:
        metrics['time_ms'] = elapsed
    
    return metrics

def main():
    print("=" * 70)
    print("OPTLOAD NETWORK SCALABILITY (5 queries per dataset)")
    print("=" * 70)
    
    all_results = []
    
    for dataset_key, dataset in DATASETS.items():
        queries_dir = RESULTS_DIR / dataset_key / 'queries'
        query_files = sorted(queries_dir.glob('query_*.txt'))
        query_files = [f for f in query_files if '_meta' not in f.name][:5]
        
        print(f"\n{dataset['name']} ({dataset['node_count']:,} nodes):")
        
        for i, qf in enumerate(query_files):
            print(f"  [{i+1}/5] {qf.name}...", end=' ', flush=True)
            metrics = run_optload(dataset_key, qf)
            print(f"served={metrics['served_requests']}, LU={metrics['lu_cost']:.0f}, time={metrics['time_ms']:.1f}ms")
            all_results.append({
                'dataset': dataset_key,
                'algorithm': 'optload',
                'query_file': qf.name,
                'metrics': metrics
            })
    
    # Save results
    with open(RESULTS_DIR / 'optload_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for dataset_key in DATASETS:
        dataset_results = [r for r in all_results if r['dataset'] == dataset_key]
        if dataset_results:
            avg_served = sum(r['metrics']['served_requests'] for r in dataset_results) / len(dataset_results)
            avg_lu = sum(r['metrics']['lu_cost'] for r in dataset_results) / len(dataset_results)
            avg_time = sum(r['metrics']['time_ms'] for r in dataset_results) / len(dataset_results)
            print(f"{dataset_key}: avg_served={avg_served:.1f}, avg_LU={avg_lu:.1f}, avg_time={avg_time:.0f}ms")

if __name__ == "__main__":
    main()
