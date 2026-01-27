#!/usr/bin/env python3
"""
Experiment 3: Pareto-Front Quality Visualization
=================================================
Multi-objective analysis showing trade-offs between:
- LU cost vs Distance
- Requests served vs LU cost

Uses existing experiment data to generate Pareto plots.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path("/home/gunturi/VRPLU-OptLoad")
EXPERIMENTS_DIR = BASE_DIR / "experiments"
RESULTS_DIR = EXPERIMENTS_DIR / "results"
PLOTS_DIR = RESULTS_DIR / "missing_experiments" / "pareto_plots"

PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# Set plot style
plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 14,
    'legend.fontsize': 11,
    'figure.figsize': (10, 6),
    'lines.markersize': 8
})

COLORS = {
    'OptLoad': '#2ecc71',
    'Insertion': '#3498db',
    'ExactLIFO': '#e74c3c',
    'FoodMatch': '#9b59b6'
}

MARKERS = {
    'OptLoad': 'o',
    'Insertion': 's',
    'ExactLIFO': '^',
    'FoodMatch': 'D'
}

print("=" * 70)
print("EXPERIMENT 3: PARETO-FRONT QUALITY VISUALIZATION")
print("=" * 70)
print()

# Load experiment results
results_file = RESULTS_DIR / "experiment_results.json"
with open(results_file, 'r') as f:
    all_results = json.load(f)

print(f"Loaded {len(all_results)} experiment results")

# Organize results by N and algorithm
organized = {}
for key, result in all_results.items():
    parts = key.split("_")
    n = int(parts[0].replace("N", ""))
    algo = parts[2]
    
    if n not in organized:
        organized[n] = {}
    if algo not in organized[n]:
        organized[n][algo] = []
    
    # Handle both field names
    served = result.get("served_requests", result.get("served", 0))
    if not result.get("timeout") and served > 0:
        # Normalize field names
        normalized = {
            "served": served,
            "lu_cost": result.get("lu_cost", 0),
            "distance": result.get("distance", 0),
            "runtime_ms": result.get("runtime_ms", 0)
        }
        organized[n][algo].append(normalized)

# ============ PARETO PLOT 1: LU Cost vs Served Requests ============
print("\nGenerating Pareto Plot 1: LU Cost vs Served Requests...")

for n in [20, 40]:
    if n not in organized:
        continue
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for algo in ['OptLoad', 'Insertion', 'ExactLIFO', 'FoodMatch']:
        if algo not in organized[n]:
            continue
        
        data = organized[n][algo]
        served = [d["served"] for d in data]
        lu_cost = [d["lu_cost"] for d in data]
        
        ax.scatter(served, lu_cost, 
                   c=COLORS.get(algo, 'gray'), 
                   marker=MARKERS.get(algo, 'o'),
                   label=algo, alpha=0.7, s=80)
    
    ax.set_xlabel('Requests Served')
    ax.set_ylabel('LU Cost')
    ax.set_title(f'Pareto Front: LU Cost vs Served Requests (N={n})')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / f'pareto_lu_vs_served_n{n}.png', dpi=300, bbox_inches='tight')
    plt.savefig(PLOTS_DIR / f'pareto_lu_vs_served_n{n}.pdf', bbox_inches='tight')
    plt.close()
    print(f"  Saved: pareto_lu_vs_served_n{n}.png")

# ============ PARETO PLOT 2: Runtime vs Quality Trade-off ============
print("\nGenerating Pareto Plot 2: Runtime vs Quality Trade-off...")

fig, ax = plt.subplots(figsize=(12, 6))

for algo in ['OptLoad', 'Insertion', 'ExactLIFO', 'FoodMatch']:
    runtimes = []
    served_values = []
    
    for n in [10, 20, 40, 60, 80, 100]:
        if n in organized and algo in organized[n]:
            data = organized[n][algo]
            if data:
                avg_runtime = np.mean([d["runtime_ms"]/1000 for d in data])
                avg_served = np.mean([d["served"] for d in data])
                runtimes.append(avg_runtime)
                served_values.append(avg_served)
    
    if runtimes:
        ax.scatter(runtimes, served_values,
                   c=COLORS.get(algo, 'gray'),
                   marker=MARKERS.get(algo, 'o'),
                   label=algo, s=100)
        
        # Connect points with line
        sorted_pairs = sorted(zip(runtimes, served_values))
        ax.plot([p[0] for p in sorted_pairs], [p[1] for p in sorted_pairs],
                c=COLORS.get(algo, 'gray'), alpha=0.5, linestyle='--')

ax.set_xlabel('Runtime (seconds)')
ax.set_ylabel('Requests Served')
ax.set_title('Quality-Time Trade-off: All Problem Sizes')
ax.set_xscale('log')
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(PLOTS_DIR / 'pareto_quality_time_tradeoff.png', dpi=300, bbox_inches='tight')
plt.savefig(PLOTS_DIR / 'pareto_quality_time_tradeoff.pdf', bbox_inches='tight')
plt.close()
print("  Saved: pareto_quality_time_tradeoff.png")

# ============ PARETO PLOT 3: Per-Query Pareto Front (N=20) ============
print("\nGenerating Pareto Plot 3: Per-Query Pareto Front...")

N_TARGET = 20
if N_TARGET in organized:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Left: LU Cost vs Served
    ax = axes[0]
    for algo in ['OptLoad', 'Insertion', 'ExactLIFO', 'FoodMatch']:
        if algo not in organized[N_TARGET]:
            continue
        
        data = organized[N_TARGET][algo]
        served = [d["served"] for d in data]
        lu_cost = [d["lu_cost"] for d in data]
        
        ax.scatter(served, lu_cost,
                   c=COLORS.get(algo, 'gray'),
                   marker=MARKERS.get(algo, 'o'),
                   label=algo, alpha=0.6, s=60)
    
    ax.set_xlabel('Requests Served')
    ax.set_ylabel('LU Cost')
    ax.set_title(f'(a) LU Cost vs Served Requests (N={N_TARGET})')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # Right: LU Cost per Served Request
    ax = axes[1]
    for algo in ['OptLoad', 'Insertion', 'ExactLIFO', 'FoodMatch']:
        if algo not in organized[N_TARGET]:
            continue
        
        data = organized[N_TARGET][algo]
        served = [d["served"] for d in data]
        efficiency = [d["lu_cost"]/d["served"] if d["served"] > 0 else 0 for d in data]
        
        ax.scatter(served, efficiency,
                   c=COLORS.get(algo, 'gray'),
                   marker=MARKERS.get(algo, 'o'),
                   label=algo, alpha=0.6, s=60)
    
    ax.set_xlabel('Requests Served')
    ax.set_ylabel('LU Cost per Request')
    ax.set_title(f'(b) Efficiency: LU Cost per Request (N={N_TARGET})')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / f'pareto_combined_n{N_TARGET}.png', dpi=300, bbox_inches='tight')
    plt.savefig(PLOTS_DIR / f'pareto_combined_n{N_TARGET}.pdf', bbox_inches='tight')
    plt.close()
    print(f"  Saved: pareto_combined_n{N_TARGET}.png")

# ============ PARETO DOMINANCE ANALYSIS ============
print("\n" + "=" * 70)
print("PARETO DOMINANCE ANALYSIS")
print("=" * 70)

def is_dominated(point, other_points):
    """Check if point is dominated by any other point."""
    served, lu_cost = point
    for other_served, other_lu in other_points:
        if other_served >= served and other_lu <= lu_cost:
            if other_served > served or other_lu < lu_cost:
                return True
    return False

for n in [20, 40]:
    if n not in organized:
        continue
    
    print(f"\nN={n}:")
    
    # Collect all points
    all_points = []
    for algo in ['OptLoad', 'Insertion', 'ExactLIFO', 'FoodMatch']:
        if algo not in organized[n]:
            continue
        for d in organized[n][algo]:
            all_points.append((d["served"], d["lu_cost"], algo))
    
    # Count non-dominated points per algorithm
    algo_dominated = {algo: {"total": 0, "non_dominated": 0} for algo in ['OptLoad', 'Insertion', 'ExactLIFO', 'FoodMatch']}
    
    for served, lu_cost, algo in all_points:
        algo_dominated[algo]["total"] += 1
        other_points = [(s, l) for s, l, a in all_points if a != algo]
        if not is_dominated((served, lu_cost), other_points):
            algo_dominated[algo]["non_dominated"] += 1
    
    print(f"  {'Algorithm':<12} {'Total Points':<15} {'Non-Dominated':<15} {'Ratio':<10}")
    print(f"  {'-'*52}")
    for algo in ['OptLoad', 'Insertion', 'ExactLIFO', 'FoodMatch']:
        total = algo_dominated[algo]["total"]
        non_dom = algo_dominated[algo]["non_dominated"]
        ratio = non_dom / total * 100 if total > 0 else 0
        print(f"  {algo:<12} {total:<15} {non_dom:<15} {ratio:.1f}%")

# Save summary
summary = {
    "plots_generated": [
        "pareto_lu_vs_served_n20.png",
        "pareto_lu_vs_served_n40.png",
        "pareto_quality_time_tradeoff.png",
        "pareto_combined_n20.png"
    ],
    "analysis": "Pareto dominance analysis completed"
}

summary_file = PLOTS_DIR / "pareto_analysis_summary.json"
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\nAll Pareto plots saved to: {PLOTS_DIR}")
print("Experiment 3 complete!")
