#!/usr/bin/env python3
"""
Compare VRP-LU solver results across different algorithms.
Generates a comprehensive comparison table for all queries.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

def parse_output_file(filepath: Path) -> Dict[int, Dict[str, any]]:
    """Parse solver output file and extract results per query."""
    results = {}
    
    if not filepath.exists():
        print(f"Warning: {filepath} not found")
        return results
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Split by lines and process
    lines = content.strip().split('\n')
    query_id = 1
    
    for line in lines:
        if not line.strip():
            continue
            
        # Parse route line format: [route] Number of Successful Requests:X L-U Cost:Y Distance:Z time
        match = re.search(r'Number of Successful Requests:\s*(\d+)\s+L-U Cost:\s*(\d+)\s+Distance:\s*([\d.]+)', line)
        if match:
            requests = int(match.group(1))
            lu_cost = int(match.group(2))
            distance = float(match.group(3))
            
            # Extract route if present
            route_match = re.match(r'\[(.*?)\]', line)
            route = route_match.group(1) if route_match else ""
            
            # Extract execution time if present
            time_match = re.search(r'([\d.]+)\s*$', line)
            exec_time = float(time_match.group(1)) if time_match else 0.0
            
            results[query_id] = {
                'requests': requests,
                'lu_cost': lu_cost,
                'distance': distance,
                'time': exec_time,
                'route': route
            }
            query_id += 1
    
    return results

def create_comparison_table(output_dir: Path) -> pd.DataFrame:
    """Create comparison DataFrame from all solver outputs."""
    
    # Parse all output files
    clustering = parse_output_file(output_dir / "Output_285050.txt")
    exact = parse_output_file(output_dir / "OutputExact_285050.txt")
    lifo = parse_output_file(output_dir / "OutputLifo_285050.txt")
    insertion = parse_output_file(output_dir / "OutputInsertion_285050.txt")
    
    # Determine all query IDs
    all_queries = sorted(set(list(clustering.keys()) + list(exact.keys()) + 
                             list(lifo.keys()) + list(insertion.keys())))
    
    # Build comparison data
    data = []
    for qid in all_queries:
        row = {'Query': qid}
        
        # Clustering (default)
        if qid in clustering:
            row['Clustering_Requests'] = clustering[qid]['requests']
            row['Clustering_LU_Cost'] = clustering[qid]['lu_cost']
            row['Clustering_Distance'] = f"{clustering[qid]['distance']:.2f}"
            row['Clustering_Time'] = f"{clustering[qid]['time']:.3f}"
        else:
            row['Clustering_Requests'] = '-'
            row['Clustering_LU_Cost'] = '-'
            row['Clustering_Distance'] = '-'
            row['Clustering_Time'] = '-'
        
        # Exact
        if qid in exact:
            row['Exact_Requests'] = exact[qid]['requests']
            row['Exact_LU_Cost'] = exact[qid]['lu_cost']
            row['Exact_Distance'] = f"{exact[qid]['distance']:.2f}"
            row['Exact_Time'] = f"{exact[qid]['time']:.3f}"
        else:
            row['Exact_Requests'] = '-'
            row['Exact_LU_Cost'] = '-'
            row['Exact_Distance'] = '-'
            row['Exact_Time'] = '-'
        
        # LIFO
        if qid in lifo:
            row['LIFO_Requests'] = lifo[qid]['requests']
            row['LIFO_LU_Cost'] = lifo[qid]['lu_cost']
            row['LIFO_Distance'] = f"{lifo[qid]['distance']:.2f}"
            row['LIFO_Time'] = f"{lifo[qid]['time']:.3f}"
        else:
            row['LIFO_Requests'] = '-'
            row['LIFO_LU_Cost'] = '-'
            row['LIFO_Distance'] = '-'
            row['LIFO_Time'] = '-'
        
        # Insertion
        if qid in insertion:
            row['Insertion_Requests'] = insertion[qid]['requests']
            row['Insertion_LU_Cost'] = insertion[qid]['lu_cost']
            row['Insertion_Distance'] = f"{insertion[qid]['distance']:.2f}"
            row['Insertion_Time'] = f"{insertion[qid]['time']:.3f}"
        else:
            row['Insertion_Requests'] = '-'
            row['Insertion_LU_Cost'] = '-'
            row['Insertion_Distance'] = '-'
            row['Insertion_Time'] = '-'
        
        data.append(row)
    
    df = pd.DataFrame(data)
    return df

def print_summary_statistics(df: pd.DataFrame):
    """Print summary statistics comparing all solvers."""
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    # Count queries
    total_queries = len(df)
    print(f"\nTotal Queries: {total_queries}")
    
    # Extract numeric columns for each solver
    solvers = ['Clustering', 'Exact', 'LIFO', 'Insertion']
    
    for solver in solvers:
        print(f"\n{solver}:")
        print("-" * 40)
        
        # Requests
        req_col = f'{solver}_Requests'
        if req_col in df.columns:
            valid_requests = df[req_col][df[req_col] != '-']
            if len(valid_requests) > 0:
                valid_requests = valid_requests.astype(int)
                print(f"  Avg Requests: {valid_requests.mean():.2f}")
                print(f"  Total Requests: {valid_requests.sum()}")
        
        # LU Cost
        cost_col = f'{solver}_LU_Cost'
        if cost_col in df.columns:
            valid_costs = df[cost_col][df[cost_col] != '-']
            if len(valid_costs) > 0:
                valid_costs = valid_costs.astype(int)
                print(f"  Avg LU Cost: {valid_costs.mean():.2f}")
        
        # Distance
        dist_col = f'{solver}_Distance'
        if dist_col in df.columns:
            valid_distances = df[dist_col][df[dist_col] != '-']
            if len(valid_distances) > 0:
                valid_distances = valid_distances.astype(float)
                print(f"  Avg Distance: {valid_distances.mean():.2f}")
        
        # Time
        time_col = f'{solver}_Time'
        if time_col in df.columns:
            valid_times = df[time_col][df[time_col] != '-']
            if len(valid_times) > 0:
                valid_times = valid_times.astype(float)
                print(f"  Avg Time (s): {valid_times.mean():.3f}")
                print(f"  Total Time (s): {valid_times.sum():.3f}")

def main():
    """Main function to generate comparison report."""
    output_dir = Path(__file__).parent
    
    print("VRP-LU Solver Comparison")
    print("="*80)
    print("\nParsing output files...")
    
    # Create comparison table
    df = create_comparison_table(output_dir)
    
    # Save to CSV
    csv_file = output_dir / "solver_comparison.csv"
    df.to_csv(csv_file, index=False)
    print(f"\nSaved detailed comparison to: {csv_file}")
    
    # Save to formatted text
    txt_file = output_dir / "solver_comparison.txt"
    with open(txt_file, 'w') as f:
        f.write("VRP-LU SOLVER COMPARISON\n")
        f.write("="*120 + "\n\n")
        f.write("Legend: Requests = Successful Requests Served, LU_Cost = Loading/Unloading Cost, ")
        f.write("Distance = Total Distance, Time = Execution Time (seconds)\n\n")
        f.write(df.to_string(index=False))
        f.write("\n\n")
    
    print(f"Saved formatted table to: {txt_file}")
    
    # Print first 20 queries as preview
    print("\nComparison Table (First 20 queries):")
    print("-" * 120)
    print(df.head(20).to_string(index=False))
    
    # Print summary statistics
    print_summary_statistics(df)
    
    print("\n" + "="*80)
    print(f"Complete results saved to {csv_file}")
    print("="*80)

if __name__ == "__main__":
    try:
        import pandas as pd
    except ImportError:
        print("Error: pandas is required. Install with: pip install pandas")
        sys.exit(1)
    
    main()
