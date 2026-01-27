#!/usr/bin/env python3
"""
Network Scalability Experiment for OptLoad
==========================================
1. Generate N=20 queries for Oldenburg and California datasets
2. Run OptLoad, LIFO, and Insertion algorithms
3. Compare metrics: LU cost, served requests, runtime
"""

import subprocess
import json
import random
import time
from pathlib import Path
from datetime import datetime

# Configuration
BASE_DIR = Path("/home/gunturi/VRPLU-OptLoad")
DATASET_DIR = BASE_DIR / "dataset"
RESULTS_DIR = BASE_DIR / "experiments" / "results" / "network_scalability"
CLASSPATH = BASE_DIR / "target" / "classes"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Dataset configurations
DATASETS = {
    'oldenburg': {
        'node_count': 6105,
        'nodes_file': DATASET_DIR / 'nodes_6105.txt',
        'edges_file': DATASET_DIR / 'edges_6105.txt',
        'name': 'Oldenburg'
    },
    'california': {
        'node_count': 21048,
        'nodes_file': DATASET_DIR / 'nodes_21048.txt',
        'edges_file': DATASET_DIR / 'edges_21048.txt',
        'name': 'California'
    },
    'london': {
        'node_count': 285050,
        'nodes_file': DATASET_DIR / 'nodes_285050.txt',
        'edges_file': DATASET_DIR / 'edges_285050.txt',
        'name': 'London'
    }
}

# Algorithms to compare
ALGORITHMS = {
    'OptLoad': '--cluster',
    'Insertion': '--insertion',
    'ExactLIFO': '--lifostack'
}

# Query parameters
N_REQUESTS = 20
NUM_QUERIES = 20  # Number of queries to generate per dataset
CAPACITY = 10
TIMEOUT = 300  # 5 minutes


def load_nodes(nodes_file):
    """Load node IDs from a nodes file."""
    nodes = []
    with open(nodes_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                nodes.append(int(parts[0]))
    return nodes


def generate_query(nodes, n_requests, capacity, query_id):
    """Generate a single query with n_requests services."""
    # Select depot
    depot = random.choice(nodes)
    
    # Generate services
    services = []
    used_nodes = {depot}
    
    for i in range(n_requests):
        # Select pickup and delivery nodes (different from each other and depot)
        available = [n for n in nodes if n not in used_nodes]
        if len(available) < 2:
            available = [n for n in nodes if n != depot]
        
        pickup = random.choice(available)
        delivery = random.choice([n for n in available if n != pickup])
        
        # Time windows within working hours (540-1140, i.e., 9am-7pm)
        pickup_start = random.randint(540, 600)
        pickup_end = pickup_start + random.randint(20, 40)
        delivery_start = pickup_end + random.randint(10, 30)
        delivery_end = delivery_start + random.randint(30, 60)
        
        # Priority (1-5)
        priority = random.randint(1, 5)
        
        services.append({
            'pickup': pickup,
            'delivery': delivery,
            'pickup_start': pickup_start,
            'pickup_end': pickup_end,
            'delivery_start': delivery_start,
            'delivery_end': delivery_end,
            'priority': priority
        })
    
    return {
        'id': query_id,
        'depot': depot,
        'capacity': capacity,
        'services': services
    }


def write_query_file(query, output_path):
    """Write query in OptLoad format."""
    lines = []
    lines.append(f"D {query['depot']}")
    lines.append(f"C {query['capacity']}")
    
    for svc in query['services']:
        lines.append(f"S {svc['pickup']},{svc['delivery']} "
                    f"{svc['pickup_start']},{svc['pickup_end']} "
                    f"{svc['delivery_start']},{svc['delivery_end']} "
                    f"{svc['priority']}")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')


def run_solver(dataset_key, query_file, algorithm_flag, timeout=300):
    """Run the solver and return results."""
    dataset = DATASETS[dataset_key]
    
    # The solver reads Query_<node_count>.txt from the base directory
    query_dest = BASE_DIR / f"Query_{dataset['node_count']}.txt"
    
    # Copy query to expected location
    import shutil
    shutil.copy(query_file, query_dest)
    
    # Determine output file
    output_prefixes = {
        '--cluster': 'Output_',
        '--insertion': 'OutputInsertion_',
        '--lifostack': 'OutputLifo_',
        '--foodmatch': 'OutputFoodMatch_'
    }
    output_prefix = output_prefixes.get(algorithm_flag, 'Output_')
    output_file = BASE_DIR / f"{output_prefix}{dataset['node_count']}.txt"
    
    # Clear previous output
    if output_file.exists():
        output_file.unlink()
    
    cmd = [
        "java", "-cp", str(CLASSPATH),
        "VRPLoadingUnloadingMain",
        str(BASE_DIR),  # Working directory
        f"--nodes={dataset['node_count']}",  # Node count parameter
        algorithm_flag
    ]
    
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
        
        # Parse output
        served = 0
        lu_cost = 0
        
        if output_file.exists():
            with open(output_file, 'r') as f:
                content = f.read()
                import re
                served_matches = re.findall(r'Number of Successful Requests:(\d+)', content)
                lu_matches = re.findall(r'L-U Cost:(\d+)', content)
                
                if served_matches:
                    served = max(int(x) for x in served_matches)
                if lu_matches:
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


def run_scalability_experiment():
    """Run full network scalability experiment."""
    print("=" * 70)
    print("NETWORK SCALABILITY EXPERIMENT")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nDatasets: {', '.join(d['name'] for d in DATASETS.values())}")
    print(f"Algorithms: {', '.join(ALGORITHMS.keys())}")
    print(f"N requests per query: {N_REQUESTS}")
    print(f"Queries per dataset: {NUM_QUERIES}")
    print(f"Timeout: {TIMEOUT}s")
    
    all_results = {
        'experiment': 'network_scalability',
        'timestamp': datetime.now().isoformat(),
        'parameters': {
            'n_requests': N_REQUESTS,
            'num_queries': NUM_QUERIES,
            'capacity': CAPACITY,
            'timeout': TIMEOUT
        },
        'datasets': {}
    }
    
    for dataset_key, dataset_info in DATASETS.items():
        print(f"\n{'='*70}")
        print(f"DATASET: {dataset_info['name']} ({dataset_info['node_count']} nodes)")
        print("=" * 70)
        
        # Check if dataset files exist
        if not dataset_info['nodes_file'].exists():
            print(f"  ⚠ Nodes file not found: {dataset_info['nodes_file']}")
            continue
        if not dataset_info['edges_file'].exists():
            print(f"  ⚠ Edges file not found: {dataset_info['edges_file']}")
            continue
        
        # Load nodes
        nodes = load_nodes(dataset_info['nodes_file'])
        print(f"Loaded {len(nodes)} nodes")
        
        # Generate queries
        queries_dir = RESULTS_DIR / dataset_key / "queries"
        queries_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nGenerating {NUM_QUERIES} queries with N={N_REQUESTS}...")
        queries = []
        for i in range(NUM_QUERIES):
            query = generate_query(nodes, N_REQUESTS, CAPACITY, i + 1)
            query_file = queries_dir / f"query_{i+1}.txt"
            write_query_file(query, query_file)
            queries.append((query, query_file))
        print(f"  ✓ Queries saved to {queries_dir}")
        
        # Run experiments
        dataset_results = {
            'node_count': dataset_info['node_count'],
            'queries_generated': NUM_QUERIES,
            'algorithms': {}
        }
        
        for algo_name, algo_flag in ALGORITHMS.items():
            print(f"\n  Running {algo_name}...")
            algo_results = []
            
            for i, (query, query_file) in enumerate(queries):
                result = run_solver(dataset_key, query_file, algo_flag, TIMEOUT)
                algo_results.append(result)
                
                status = "✓" if not result['timeout'] else "⏱"
                print(f"    [{i+1}/{NUM_QUERIES}] {status} served={result['served']}, "
                      f"lu={result['lu_cost']:.0f}, time={result['runtime_ms']/1000:.1f}s")
            
            # Calculate summary statistics
            completed = [r for r in algo_results if not r['timeout']]
            if completed:
                avg_served = sum(r['served'] for r in completed) / len(completed)
                avg_lu = sum(r['lu_cost'] for r in completed) / len(completed)
                avg_runtime = sum(r['runtime_ms'] for r in completed) / len(completed)
            else:
                avg_served = avg_lu = avg_runtime = 0
            
            dataset_results['algorithms'][algo_name] = {
                'results': algo_results,
                'summary': {
                    'completed': len(completed),
                    'total': len(algo_results),
                    'timeout_rate': (len(algo_results) - len(completed)) / len(algo_results) * 100,
                    'avg_served': avg_served,
                    'avg_lu_cost': avg_lu,
                    'avg_runtime_ms': avg_runtime
                }
            }
            
            print(f"    Summary: {len(completed)}/{len(algo_results)} completed, "
                  f"avg_served={avg_served:.1f}, avg_lu={avg_lu:.1f}, "
                  f"avg_time={avg_runtime/1000:.1f}s")
        
        all_results['datasets'][dataset_key] = dataset_results
    
    # Save results
    results_file = RESULTS_DIR / "scalability_results.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n✓ Results saved to: {results_file}")
    
    # Print comparison table
    print_comparison_table(all_results)
    
    return all_results


def print_comparison_table(results):
    """Print a comparison table of results."""
    print("\n" + "=" * 70)
    print("NETWORK SCALABILITY COMPARISON TABLE")
    print("=" * 70)
    
    print(f"\n{'Dataset':<15} {'Algorithm':<12} {'Nodes':<8} {'Served':<10} {'LU Cost':<10} {'Runtime(s)':<12}")
    print("-" * 70)
    
    for dataset_key, dataset_data in results['datasets'].items():
        node_count = dataset_data['node_count']
        for algo_name, algo_data in dataset_data['algorithms'].items():
            summary = algo_data['summary']
            print(f"{dataset_key:<15} {algo_name:<12} {node_count:<8} "
                  f"{summary['avg_served']:<10.1f} {summary['avg_lu_cost']:<10.1f} "
                  f"{summary['avg_runtime_ms']/1000:<12.2f}")
    
    print("-" * 70)


if __name__ == "__main__":
    random.seed(42)
    run_scalability_experiment()
