#!/usr/bin/env python3
"""
Generate ablation study plots for GeoInformatica submission.
Compares algorithm component contributions using the corrected experiment data.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import os

# Create output directory
os.makedirs('plots', exist_ok=True)

# Load summary data
with open('results/experiment_summary.json', 'r') as f:
    summary = json.load(f)

# Configuration
N_VALUES = [10, 20, 40, 60, 80, 100]
ALGORITHMS = ['OptLoad', 'Insertion', 'ExactLIFO', 'FoodMatch']
COLORS = {
    'OptLoad': '#2ecc71',      # Green (our algorithm)
    'Insertion': '#3498db',    # Blue
    'ExactLIFO': '#e74c3c',    # Red
    'FoodMatch': '#9b59b6'     # Purple
}

# Set publication style
plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 14,
    'legend.fontsize': 11,
    'figure.figsize': (10, 6),
    'lines.linewidth': 2,
    'lines.markersize': 8
})

def extract_metric(metric_name):
    """Extract metric values for all algorithms across N values."""
    data = {algo: [] for algo in ALGORITHMS}
    for n in N_VALUES:
        n_str = str(n)
        for algo in ALGORITHMS:
            if n_str in summary and algo in summary[n_str]:
                data[algo].append(summary[n_str][algo].get(metric_name, 0))
            else:
                data[algo].append(0)
    return data

# ============ ABLATION PLOT 1: Algorithm Component Analysis ============
print("Generating Ablation Plot 1: Component Contribution Analysis...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Get data
served_data = extract_metric('served_mean')
lu_data = extract_metric('lu_cost_mean')
runtime_data = extract_metric('runtime_mean')

# Plot 1a: Served Requests - Component Impact
ax = axes[0, 0]
x = np.arange(len(N_VALUES))
width = 0.2
for i, algo in enumerate(ALGORITHMS):
    offset = (i - 1.5) * width
    ax.bar(x + offset, served_data[algo], width, label=algo, color=COLORS[algo])
ax.set_xlabel('Number of Requests (N)')
ax.set_ylabel('Requests Served')
ax.set_title('(a) Impact of Algorithm Strategy on Served Requests')
ax.set_xticks(x)
ax.set_xticklabels(N_VALUES)
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3, axis='y')

# Plot 1b: LU Cost Efficiency
ax = axes[0, 1]
# Calculate LU cost per served request
lu_per_served = {algo: [] for algo in ALGORITHMS}
for i, n in enumerate(N_VALUES):
    for algo in ALGORITHMS:
        served = served_data[algo][i]
        lu = lu_data[algo][i]
        if served > 0:
            lu_per_served[algo].append(lu / served)
        else:
            lu_per_served[algo].append(0)

for i, algo in enumerate(ALGORITHMS):
    offset = (i - 1.5) * width
    ax.bar(x + offset, lu_per_served[algo], width, label=algo, color=COLORS[algo])
ax.set_xlabel('Number of Requests (N)')
ax.set_ylabel('LU Cost per Served Request')
ax.set_title('(b) LU Cost Efficiency (Lower is Better)')
ax.set_xticks(x)
ax.set_xticklabels(N_VALUES)
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3, axis='y')

# Plot 1c: Runtime Efficiency (requests served per second)
ax = axes[1, 0]
efficiency = {algo: [] for algo in ALGORITHMS}
for i, n in enumerate(N_VALUES):
    for algo in ALGORITHMS:
        served = served_data[algo][i]
        runtime_sec = runtime_data[algo][i] / 1000  # Convert to seconds
        if runtime_sec > 0:
            efficiency[algo].append(served / runtime_sec)
        else:
            efficiency[algo].append(0)

for i, algo in enumerate(ALGORITHMS):
    offset = (i - 1.5) * width
    ax.bar(x + offset, efficiency[algo], width, label=algo, color=COLORS[algo])
ax.set_xlabel('Number of Requests (N)')
ax.set_ylabel('Requests Served per Second')
ax.set_title('(c) Runtime Efficiency (Higher is Better)')
ax.set_xticks(x)
ax.set_xticklabels(N_VALUES)
ax.legend(loc='upper right')
ax.set_yscale('log')
ax.grid(True, alpha=0.3, axis='y', which='both')

# Plot 1d: Quality-Time Trade-off
ax = axes[1, 1]
for algo in ALGORITHMS:
    runtimes_sec = [r/1000 for r in runtime_data[algo]]
    ax.scatter(runtimes_sec, served_data[algo], s=100, label=algo, 
               color=COLORS[algo], marker='o', alpha=0.7)
    # Add N labels
    for i, n in enumerate(N_VALUES):
        if served_data[algo][i] > 0:
            ax.annotate(f'N={n}', (runtimes_sec[i], served_data[algo][i]),
                       textcoords="offset points", xytext=(5,5), fontsize=8)
ax.set_xlabel('Runtime (seconds)')
ax.set_ylabel('Requests Served')
ax.set_title('(d) Quality vs Time Trade-off')
ax.set_xscale('log')
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('plots/ablation_component_analysis.png', dpi=300, bbox_inches='tight')
plt.savefig('plots/ablation_component_analysis.pdf', bbox_inches='tight')
plt.close()

# ============ ABLATION PLOT 2: Per-N Detailed Comparison ============
print("Generating Ablation Plot 2: Per-N Detailed Analysis...")

for n in [10, 20, 40, 60]:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    n_str = str(n)
    
    algos_with_data = [a for a in ALGORITHMS if n_str in summary and a in summary[n_str]]
    
    # Get data for this N
    served = [summary[n_str][a]['served_mean'] for a in algos_with_data]
    served_std = [summary[n_str][a]['served_std'] for a in algos_with_data]
    lu = [summary[n_str][a]['lu_cost_mean'] for a in algos_with_data]
    lu_std = [summary[n_str][a]['lu_cost_std'] for a in algos_with_data]
    runtime = [summary[n_str][a]['runtime_mean']/1000 for a in algos_with_data]
    counts = [summary[n_str][a]['count'] for a in algos_with_data]
    
    colors = [COLORS[a] for a in algos_with_data]
    
    # Plot a: Served Requests
    ax = axes[0]
    bars = ax.bar(algos_with_data, served, yerr=served_std, capsize=5, color=colors, alpha=0.8)
    ax.set_ylabel('Requests Served')
    ax.set_title(f'N={n}: Requests Served')
    ax.grid(True, alpha=0.3, axis='y')
    # Add count annotations
    for bar, count in zip(bars, counts):
        ax.annotate(f'n={count}', (bar.get_x() + bar.get_width()/2, bar.get_height()),
                   ha='center', va='bottom', fontsize=9)
    
    # Plot b: LU Cost
    ax = axes[1]
    ax.bar(algos_with_data, lu, yerr=lu_std, capsize=5, color=colors, alpha=0.8)
    ax.set_ylabel('LU Cost')
    ax.set_title(f'N={n}: LU Cost')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot c: Runtime
    ax = axes[2]
    ax.bar(algos_with_data, runtime, color=colors, alpha=0.8)
    ax.set_ylabel('Runtime (seconds)')
    ax.set_title(f'N={n}: Runtime')
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3, axis='y', which='both')
    
    plt.tight_layout()
    plt.savefig(f'plots/ablation_n{n}.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'plots/ablation_n{n}.pdf', bbox_inches='tight')
    plt.close()

# ============ ABLATION PLOT 3: Constraint Impact Analysis ============
print("Generating Ablation Plot 3: Constraint Impact Analysis...")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# LIFO vs non-LIFO comparison
ax = axes[0]
lifo_based = ['ExactLIFO', 'FoodMatch']
non_lifo = ['OptLoad', 'Insertion']

lifo_served = [np.mean([summary[str(n)][a]['served_mean'] for a in lifo_based 
                        if str(n) in summary and a in summary[str(n)]]) for n in N_VALUES]
nonlifo_served = [np.mean([summary[str(n)][a]['served_mean'] for a in non_lifo 
                          if str(n) in summary and a in summary[str(n)]]) for n in N_VALUES]

ax.plot(N_VALUES, nonlifo_served, 'o-', label='Non-LIFO (OptLoad, Insertion)', 
        color='#2ecc71', linewidth=2, markersize=8)
ax.plot(N_VALUES, lifo_served, 's-', label='LIFO-based (ExactLIFO, FoodMatch)', 
        color='#e74c3c', linewidth=2, markersize=8)
ax.set_xlabel('Number of Requests (N)')
ax.set_ylabel('Average Requests Served')
ax.set_title('(a) Impact of LIFO Constraint on Solution Quality')
ax.legend()
ax.grid(True, alpha=0.3)
ax.set_xticks(N_VALUES)

# Exact vs Heuristic comparison
ax = axes[1]
exact = ['OptLoad', 'ExactLIFO']
heuristic = ['Insertion', 'FoodMatch']

exact_served = [np.mean([summary[str(n)][a]['served_mean'] for a in exact 
                        if str(n) in summary and a in summary[str(n)]]) for n in N_VALUES]
heur_served = [np.mean([summary[str(n)][a]['served_mean'] for a in heuristic 
                       if str(n) in summary and a in summary[str(n)]]) for n in N_VALUES]

ax.plot(N_VALUES, exact_served, 'o-', label='Exact (OptLoad, ExactLIFO)', 
        color='#3498db', linewidth=2, markersize=8)
ax.plot(N_VALUES, heur_served, 's-', label='Heuristic (Insertion, FoodMatch)', 
        color='#9b59b6', linewidth=2, markersize=8)
ax.set_xlabel('Number of Requests (N)')
ax.set_ylabel('Average Requests Served')
ax.set_title('(b) Impact of Search Strategy (Exact vs Heuristic)')
ax.legend()
ax.grid(True, alpha=0.3)
ax.set_xticks(N_VALUES)

plt.tight_layout()
plt.savefig('plots/ablation_constraint_impact.png', dpi=300, bbox_inches='tight')
plt.savefig('plots/ablation_constraint_impact.pdf', bbox_inches='tight')
plt.close()

# ============ ABLATION PLOT 4: OptLoad Advantage Breakdown ============
print("Generating Ablation Plot 4: OptLoad Advantage Breakdown...")

fig, ax = plt.subplots(figsize=(10, 6))

# Calculate percentage improvement of OptLoad over each competitor
competitors = ['Insertion', 'ExactLIFO', 'FoodMatch']
improvements = {comp: [] for comp in competitors}

for n in N_VALUES:
    n_str = str(n)
    optload_served = summary[n_str]['OptLoad']['served_mean']
    for comp in competitors:
        comp_served = summary[n_str][comp]['served_mean']
        if comp_served > 0:
            pct_improvement = ((optload_served - comp_served) / comp_served) * 100
            improvements[comp].append(pct_improvement)
        else:
            improvements[comp].append(0)

x = np.arange(len(N_VALUES))
width = 0.25
comp_colors = {'Insertion': '#3498db', 'ExactLIFO': '#e74c3c', 'FoodMatch': '#9b59b6'}

for i, comp in enumerate(competitors):
    offset = (i - 1) * width
    ax.bar(x + offset, improvements[comp], width, label=f'vs {comp}', 
           color=comp_colors[comp], alpha=0.8)

ax.set_xlabel('Number of Requests (N)')
ax.set_ylabel('OptLoad Improvement (%)')
ax.set_title('OptLoad Performance Improvement Over Competitors')
ax.set_xticks(x)
ax.set_xticklabels(N_VALUES)
ax.legend()
ax.grid(True, alpha=0.3, axis='y')
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

plt.tight_layout()
plt.savefig('plots/ablation_optload_improvement.png', dpi=300, bbox_inches='tight')
plt.savefig('plots/ablation_optload_improvement.pdf', bbox_inches='tight')
plt.close()

# ============ Summary ============
print("\n" + "="*70)
print("ABLATION STUDY PLOTS GENERATED")
print("="*70)
print("\nPlots saved to experiments/plots/:")
print("  1. ablation_component_analysis.png - 4-panel component contribution")
print("  2. ablation_n10.png - Detailed N=10 comparison")
print("  3. ablation_n20.png - Detailed N=20 comparison")
print("  4. ablation_n40.png - Detailed N=40 comparison")
print("  5. ablation_n60.png - Detailed N=60 comparison")
print("  6. ablation_constraint_impact.png - LIFO vs non-LIFO, Exact vs Heuristic")
print("  7. ablation_optload_improvement.png - OptLoad advantage breakdown")
print("\nPDF versions also generated for all plots.")
print("="*70)
