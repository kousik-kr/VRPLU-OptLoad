#!/usr/bin/env python3
"""
Chart Generator for VRP-LU Experiments
=======================================

Generates publication-quality charts from experiment results:
1. Scalability (Requests Served vs N)
2. LU Cost vs N
3. Runtime vs N
4. Bar chart comparison
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Add experiments directory
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from config import RESULTS_DIR

# Try to import matplotlib
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not installed. Charts will be generated as CSV data.")


# Algorithm colors and markers for consistency
ALGO_STYLES = {
    "Insertion": {"color": "#2ecc71", "marker": "o", "name": "Insertion Heuristic"},
    "OptLoad": {"color": "#e74c3c", "marker": "s", "name": "OptLoad"},
    "ExactLIFO": {"color": "#3498db", "marker": "^", "name": "Exact LIFO"},
    "Bazelmans": {"color": "#9b59b6", "marker": "D", "name": "Bazelmans"},
    "FoodMatch": {"color": "#f39c12", "marker": "v", "name": "FoodMatch"},
    "Exact": {"color": "#1abc9c", "marker": "P", "name": "Exact"},
}

N_VALUES = [10, 20, 40, 60, 80, 100]


def load_results():
    """Load experiment results."""
    results_file = RESULTS_DIR / "experiment_results.json"
    if not results_file.exists():
        print(f"Error: Results file not found at {results_file}")
        return None
    
    with open(results_file, 'r') as f:
        return json.load(f)


def aggregate_results(results):
    """
    Aggregate results by algorithm and N value.
    
    Returns dict: {algo: {n: {"served": [...], "lu_cost": [...], "runtime": [...]}}}
    """
    aggregated = defaultdict(lambda: defaultdict(lambda: {
        "served": [], "lu_cost": [], "runtime": [], "distance": []
    }))
    
    for key, result in results.items():
        algo = result["algorithm"]
        query_id = result["query_id"]
        
        # Extract N value from query_id (e.g., "N10_R1")
        try:
            n_str = query_id.split("_")[0]
            n = int(n_str.replace("N", ""))
        except:
            continue
        
        aggregated[algo][n]["served"].append(result["served_requests"])
        aggregated[algo][n]["lu_cost"].append(result["lu_cost"])
        aggregated[algo][n]["runtime"].append(result["runtime_ms"])
        aggregated[algo][n]["distance"].append(result["distance"])
    
    return aggregated


def compute_statistics(values):
    """Compute mean and std for a list of values."""
    if not values:
        return 0, 0
    
    arr = np.array(values) if HAS_MATPLOTLIB else values
    mean = sum(values) / len(values)
    
    if len(values) > 1:
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        std = variance ** 0.5
    else:
        std = 0
    
    return mean, std


def generate_scalability_chart(aggregated, output_dir):
    """Generate Requests Served vs N chart."""
    if not HAS_MATPLOTLIB:
        return generate_scalability_csv(aggregated, output_dir)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for algo in aggregated.keys():
        if algo not in ALGO_STYLES:
            continue
        
        style = ALGO_STYLES[algo]
        n_vals = []
        means = []
        stds = []
        
        for n in N_VALUES:
            if n in aggregated[algo]:
                served = aggregated[algo][n]["served"]
                mean, std = compute_statistics(served)
                n_vals.append(n)
                means.append(mean)
                stds.append(std)
        
        if n_vals:
            ax.errorbar(n_vals, means, yerr=stds, 
                       label=style["name"],
                       color=style["color"],
                       marker=style["marker"],
                       capsize=3,
                       linewidth=2,
                       markersize=8)
    
    ax.set_xlabel("Number of Service Requests (N)", fontsize=12)
    ax.set_ylabel("Average Requests Served", fontsize=12)
    ax.set_title("Algorithm Scalability: Requests Served vs N", fontsize=14)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    ax.set_xticks(N_VALUES)
    
    output_file = output_dir / "scalability_served.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_file}")


def generate_lu_cost_chart(aggregated, output_dir):
    """Generate LU Cost vs N chart."""
    if not HAS_MATPLOTLIB:
        return generate_lu_cost_csv(aggregated, output_dir)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for algo in aggregated.keys():
        if algo not in ALGO_STYLES:
            continue
        
        style = ALGO_STYLES[algo]
        n_vals = []
        means = []
        stds = []
        
        for n in N_VALUES:
            if n in aggregated[algo]:
                # Filter out zero values (failed runs)
                lu_costs = [x for x in aggregated[algo][n]["lu_cost"] if x > 0]
                if lu_costs:
                    mean, std = compute_statistics(lu_costs)
                    n_vals.append(n)
                    means.append(mean)
                    stds.append(std)
        
        if n_vals:
            ax.errorbar(n_vals, means, yerr=stds,
                       label=style["name"],
                       color=style["color"],
                       marker=style["marker"],
                       capsize=3,
                       linewidth=2,
                       markersize=8)
    
    ax.set_xlabel("Number of Service Requests (N)", fontsize=12)
    ax.set_ylabel("Average L-U Cost", fontsize=12)
    ax.set_title("Loading-Unloading Cost vs N", fontsize=14)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    ax.set_xticks(N_VALUES)
    
    output_file = output_dir / "lu_cost.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_file}")


def generate_runtime_chart(aggregated, output_dir):
    """Generate Runtime vs N chart."""
    if not HAS_MATPLOTLIB:
        return generate_runtime_csv(aggregated, output_dir)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for algo in aggregated.keys():
        if algo not in ALGO_STYLES:
            continue
        
        style = ALGO_STYLES[algo]
        n_vals = []
        means = []
        stds = []
        
        for n in N_VALUES:
            if n in aggregated[algo]:
                runtimes = aggregated[algo][n]["runtime"]
                mean, std = compute_statistics(runtimes)
                n_vals.append(n)
                means.append(mean / 1000)  # Convert to seconds
                stds.append(std / 1000)
        
        if n_vals:
            ax.errorbar(n_vals, means, yerr=stds,
                       label=style["name"],
                       color=style["color"],
                       marker=style["marker"],
                       capsize=3,
                       linewidth=2,
                       markersize=8)
    
    ax.set_xlabel("Number of Service Requests (N)", fontsize=12)
    ax.set_ylabel("Average Runtime (seconds)", fontsize=12)
    ax.set_title("Algorithm Runtime vs N", fontsize=14)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    ax.set_xticks(N_VALUES)
    ax.set_yscale('log')  # Log scale for runtime
    
    output_file = output_dir / "runtime.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_file}")


def generate_bar_comparison(aggregated, output_dir):
    """Generate bar chart comparing algorithms at fixed N=60."""
    if not HAS_MATPLOTLIB:
        return generate_bar_csv(aggregated, output_dir)
    
    target_n = 60
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    algos = list(aggregated.keys())
    algos = [a for a in algos if a in ALGO_STYLES]
    
    metrics = [
        ("served", "Requests Served", axes[0]),
        ("lu_cost", "L-U Cost", axes[1]),
        ("runtime", "Runtime (ms)", axes[2]),
    ]
    
    x = np.arange(len(algos))
    width = 0.6
    
    for metric, title, ax in metrics:
        means = []
        stds = []
        colors = []
        
        for algo in algos:
            values = aggregated[algo][target_n].get(metric, [])
            if metric != "runtime":
                values = [v for v in values if v > 0]
            
            if values:
                mean, std = compute_statistics(values)
            else:
                mean, std = 0, 0
            
            means.append(mean)
            stds.append(std)
            colors.append(ALGO_STYLES[algo]["color"])
        
        bars = ax.bar(x, means, width, yerr=stds, capsize=5, color=colors)
        ax.set_ylabel(title)
        ax.set_xticks(x)
        ax.set_xticklabels([ALGO_STYLES[a]["name"] for a in algos], rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.suptitle(f"Algorithm Comparison at N={target_n}", fontsize=14)
    plt.tight_layout()
    
    output_file = output_dir / "comparison_bar.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_file}")


def generate_scalability_csv(aggregated, output_dir):
    """Generate CSV data for scalability chart."""
    output_file = output_dir / "scalability_data.csv"
    
    with open(output_file, 'w') as f:
        # Header
        algos = list(aggregated.keys())
        f.write("N," + ",".join(f"{a}_mean,{a}_std" for a in algos) + "\n")
        
        for n in N_VALUES:
            row = [str(n)]
            for algo in algos:
                if n in aggregated[algo]:
                    values = aggregated[algo][n]["served"]
                    mean, std = compute_statistics(values)
                    row.extend([f"{mean:.2f}", f"{std:.2f}"])
                else:
                    row.extend(["0", "0"])
            f.write(",".join(row) + "\n")
    
    print(f"Saved CSV: {output_file}")


def generate_lu_cost_csv(aggregated, output_dir):
    """Generate CSV data for LU cost chart."""
    output_file = output_dir / "lu_cost_data.csv"
    
    with open(output_file, 'w') as f:
        algos = list(aggregated.keys())
        f.write("N," + ",".join(f"{a}_mean,{a}_std" for a in algos) + "\n")
        
        for n in N_VALUES:
            row = [str(n)]
            for algo in algos:
                if n in aggregated[algo]:
                    values = [x for x in aggregated[algo][n]["lu_cost"] if x > 0]
                    if values:
                        mean, std = compute_statistics(values)
                    else:
                        mean, std = 0, 0
                    row.extend([f"{mean:.2f}", f"{std:.2f}"])
                else:
                    row.extend(["0", "0"])
            f.write(",".join(row) + "\n")
    
    print(f"Saved CSV: {output_file}")


def generate_runtime_csv(aggregated, output_dir):
    """Generate CSV data for runtime chart."""
    output_file = output_dir / "runtime_data.csv"
    
    with open(output_file, 'w') as f:
        algos = list(aggregated.keys())
        f.write("N," + ",".join(f"{a}_mean_ms,{a}_std_ms" for a in algos) + "\n")
        
        for n in N_VALUES:
            row = [str(n)]
            for algo in algos:
                if n in aggregated[algo]:
                    values = aggregated[algo][n]["runtime"]
                    mean, std = compute_statistics(values)
                    row.extend([f"{mean:.2f}", f"{std:.2f}"])
                else:
                    row.extend(["0", "0"])
            f.write(",".join(row) + "\n")
    
    print(f"Saved CSV: {output_file}")


def generate_bar_csv(aggregated, output_dir):
    """Generate CSV data for bar comparison."""
    output_file = output_dir / "comparison_n60.csv"
    target_n = 60
    
    with open(output_file, 'w') as f:
        f.write("Algorithm,Served_Mean,Served_Std,LU_Mean,LU_Std,Runtime_Mean_ms,Runtime_Std_ms\n")
        
        for algo in aggregated.keys():
            if algo not in ALGO_STYLES:
                continue
            
            served = aggregated[algo][target_n].get("served", [])
            lu_cost = [x for x in aggregated[algo][target_n].get("lu_cost", []) if x > 0]
            runtime = aggregated[algo][target_n].get("runtime", [])
            
            s_mean, s_std = compute_statistics(served) if served else (0, 0)
            l_mean, l_std = compute_statistics(lu_cost) if lu_cost else (0, 0)
            r_mean, r_std = compute_statistics(runtime) if runtime else (0, 0)
            
            f.write(f"{algo},{s_mean:.2f},{s_std:.2f},{l_mean:.2f},{l_std:.2f},{r_mean:.2f},{r_std:.2f}\n")
    
    print(f"Saved CSV: {output_file}")


def generate_summary_table(aggregated, output_dir):
    """Generate a summary table in markdown format."""
    output_file = output_dir / "results_summary.md"
    
    with open(output_file, 'w') as f:
        f.write("# VRP-LU Experiment Results Summary\n\n")
        f.write(f"Generated: {__import__('datetime').datetime.now().isoformat()}\n\n")
        
        # Scalability table
        f.write("## Scalability Results\n\n")
        f.write("### Requests Served (Mean ± Std)\n\n")
        
        algos = [a for a in aggregated.keys() if a in ALGO_STYLES]
        
        f.write("| N | " + " | ".join(ALGO_STYLES[a]["name"] for a in algos) + " |\n")
        f.write("|" + "---|" * (len(algos) + 1) + "\n")
        
        for n in N_VALUES:
            row = [str(n)]
            for algo in algos:
                if n in aggregated[algo]:
                    values = aggregated[algo][n]["served"]
                    mean, std = compute_statistics(values)
                    row.append(f"{mean:.1f} ± {std:.1f}")
                else:
                    row.append("N/A")
            f.write("| " + " | ".join(row) + " |\n")
        
        f.write("\n### L-U Cost (Mean ± Std)\n\n")
        f.write("| N | " + " | ".join(ALGO_STYLES[a]["name"] for a in algos) + " |\n")
        f.write("|" + "---|" * (len(algos) + 1) + "\n")
        
        for n in N_VALUES:
            row = [str(n)]
            for algo in algos:
                if n in aggregated[algo]:
                    values = [x for x in aggregated[algo][n]["lu_cost"] if x > 0]
                    if values:
                        mean, std = compute_statistics(values)
                        row.append(f"{mean:.1f} ± {std:.1f}")
                    else:
                        row.append("0")
                else:
                    row.append("N/A")
            f.write("| " + " | ".join(row) + " |\n")
        
        f.write("\n### Runtime (Mean in seconds)\n\n")
        f.write("| N | " + " | ".join(ALGO_STYLES[a]["name"] for a in algos) + " |\n")
        f.write("|" + "---|" * (len(algos) + 1) + "\n")
        
        for n in N_VALUES:
            row = [str(n)]
            for algo in algos:
                if n in aggregated[algo]:
                    values = aggregated[algo][n]["runtime"]
                    mean, std = compute_statistics(values)
                    row.append(f"{mean/1000:.2f}s")
                else:
                    row.append("N/A")
            f.write("| " + " | ".join(row) + " |\n")
    
    print(f"Saved: {output_file}")


def main():
    print("="*60)
    print("VRP-LU Chart Generator")
    print("="*60)
    
    # Create output directory
    charts_dir = RESULTS_DIR / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    
    # Load results
    results = load_results()
    if not results:
        return
    
    print(f"Loaded {len(results)} experiment results")
    
    # Aggregate
    aggregated = aggregate_results(results)
    print(f"Found {len(aggregated)} algorithms: {list(aggregated.keys())}")
    
    # Generate charts
    if HAS_MATPLOTLIB:
        print("\nGenerating charts...")
        generate_scalability_chart(aggregated, charts_dir)
        generate_lu_cost_chart(aggregated, charts_dir)
        generate_runtime_chart(aggregated, charts_dir)
        generate_bar_comparison(aggregated, charts_dir)
    else:
        print("\nGenerating CSV data (matplotlib not available)...")
    
    # Always generate CSV and markdown
    generate_scalability_csv(aggregated, charts_dir)
    generate_lu_cost_csv(aggregated, charts_dir)
    generate_runtime_csv(aggregated, charts_dir)
    generate_bar_csv(aggregated, charts_dir)
    generate_summary_table(aggregated, charts_dir)
    
    print("\n" + "="*60)
    print("Chart generation complete!")
    print(f"Output directory: {charts_dir}")


if __name__ == "__main__":
    main()
