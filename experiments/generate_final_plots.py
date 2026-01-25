#!/usr/bin/env python3
"""
Generate publication-quality plots for GeoInformatica submission.
4 algorithms: OptLoad, Insertion Heuristic, ExactLIFO, FoodMatch
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import os

# Create output directory
os.makedirs('results/charts', exist_ok=True)

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
MARKERS = {'OptLoad': 'o', 'Insertion': 's', 'ExactLIFO': '^', 'FoodMatch': 'D'}

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

def extract_metric_with_count(metric_name):
    """Extract metric values and counts for error bars."""
    data = {algo: {'values': [], 'stds': [], 'counts': []} for algo in ALGORITHMS}
    for n in N_VALUES:
        n_str = str(n)
        for algo in ALGORITHMS:
            if n_str in summary and algo in summary[n_str]:
                data[algo]['values'].append(summary[n_str][algo].get(metric_name, 0))
                data[algo]['stds'].append(summary[n_str][algo].get(f'{metric_name.replace("_mean", "_std")}', 0))
                data[algo]['counts'].append(summary[n_str][algo].get('count', 0))
            else:
                data[algo]['values'].append(0)
                data[algo]['stds'].append(0)
                data[algo]['counts'].append(0)
    return data

# ============ PLOT 1: Requests Served vs N ============
print("Generating Plot 1: Requests Served vs N...")
fig, ax = plt.subplots()

served_data = extract_metric('served_mean')
for algo in ALGORITHMS:
    ax.plot(N_VALUES, served_data[algo], 
            marker=MARKERS[algo], color=COLORS[algo], 
            label=algo, linewidth=2, markersize=8)

ax.set_xlabel('Number of Requests (N)')
ax.set_ylabel('Average Requests Served')
ax.set_title('Scalability: Requests Served vs Problem Size')
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
ax.set_xticks(N_VALUES)
plt.tight_layout()
plt.savefig('results/charts/requests_served_vs_N.png', dpi=300, bbox_inches='tight')
plt.savefig('results/charts/requests_served_vs_N.pdf', bbox_inches='tight')
plt.close()

# ============ PLOT 2: LU Cost vs N ============
print("Generating Plot 2: LU Cost vs N...")
fig, ax = plt.subplots()

lu_data = extract_metric('lu_cost_mean')
for algo in ALGORITHMS:
    ax.plot(N_VALUES, lu_data[algo], 
            marker=MARKERS[algo], color=COLORS[algo], 
            label=algo, linewidth=2, markersize=8)

ax.set_xlabel('Number of Requests (N)')
ax.set_ylabel('Average LU Cost')
ax.set_title('Scalability: Loading/Unloading Cost vs Problem Size')
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
ax.set_xticks(N_VALUES)
plt.tight_layout()
plt.savefig('results/charts/lu_cost_vs_N.png', dpi=300, bbox_inches='tight')
plt.savefig('results/charts/lu_cost_vs_N.pdf', bbox_inches='tight')
plt.close()

# ============ PLOT 3: Runtime vs N (Log Scale) ============
print("Generating Plot 3: Runtime vs N...")
fig, ax = plt.subplots()

runtime_data = extract_metric('runtime_mean')
for algo in ALGORITHMS:
    # Convert ms to seconds
    runtimes_sec = [r/1000 for r in runtime_data[algo]]
    ax.plot(N_VALUES, runtimes_sec, 
            marker=MARKERS[algo], color=COLORS[algo], 
            label=algo, linewidth=2, markersize=8)

ax.set_xlabel('Number of Requests (N)')
ax.set_ylabel('Average Runtime (seconds)')
ax.set_title('Scalability: Runtime vs Problem Size')
ax.set_yscale('log')
ax.legend(loc='best')
ax.grid(True, alpha=0.3, which='both')
ax.set_xticks(N_VALUES)
plt.tight_layout()
plt.savefig('results/charts/runtime_vs_N.png', dpi=300, bbox_inches='tight')
plt.savefig('results/charts/runtime_vs_N.pdf', bbox_inches='tight')
plt.close()

# ============ PLOT 4: Completion Rate (OptLoad Focus) ============
print("Generating Plot 4: Completion Rate...")
fig, ax = plt.subplots()

completion_rates = {algo: [] for algo in ALGORITHMS}
for n in N_VALUES:
    n_str = str(n)
    for algo in ALGORITHMS:
        if n_str in summary and algo in summary[n_str]:
            count = summary[n_str][algo].get('count', 0)
            total = summary[n_str][algo].get('total', 100)
            completion_rates[algo].append(100 * count / total)
        else:
            completion_rates[algo].append(0)

x = np.arange(len(N_VALUES))
width = 0.2

for i, algo in enumerate(ALGORITHMS):
    offset = (i - 1.5) * width
    ax.bar(x + offset, completion_rates[algo], width, label=algo, color=COLORS[algo])

ax.set_xlabel('Number of Requests (N)')
ax.set_ylabel('Completion Rate (%)')
ax.set_title('Algorithm Completion Rate (300s timeout)')
ax.set_xticks(x)
ax.set_xticklabels(N_VALUES)
ax.legend(loc='upper right')
ax.set_ylim(0, 110)
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('results/charts/completion_rate.png', dpi=300, bbox_inches='tight')
plt.savefig('results/charts/completion_rate.pdf', bbox_inches='tight')
plt.close()

# ============ PLOT 5: Bar Chart - Served Requests Comparison ============
print("Generating Plot 5: Bar Chart Comparison...")
fig, ax = plt.subplots(figsize=(12, 6))

x = np.arange(len(N_VALUES))
width = 0.2

for i, algo in enumerate(ALGORITHMS):
    offset = (i - 1.5) * width
    ax.bar(x + offset, served_data[algo], width, label=algo, color=COLORS[algo])

ax.set_xlabel('Number of Requests (N)')
ax.set_ylabel('Average Requests Served')
ax.set_title('Algorithm Comparison: Requests Served by Problem Size')
ax.set_xticks(x)
ax.set_xticklabels(N_VALUES)
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('results/charts/served_comparison_bar.png', dpi=300, bbox_inches='tight')
plt.savefig('results/charts/served_comparison_bar.pdf', bbox_inches='tight')
plt.close()

# ============ PLOT 6: OptLoad Performance Advantage ============
print("Generating Plot 6: OptLoad Advantage Ratio...")
fig, ax = plt.subplots()

# Calculate ratio of OptLoad vs best competitor
ratios = {'vs_Insertion': [], 'vs_ExactLIFO': [], 'vs_FoodMatch': []}
for i, n in enumerate(N_VALUES):
    optload_served = served_data['OptLoad'][i]
    if optload_served > 0:
        ratios['vs_Insertion'].append(optload_served / max(served_data['Insertion'][i], 0.1))
        ratios['vs_ExactLIFO'].append(optload_served / max(served_data['ExactLIFO'][i], 0.1))
        ratios['vs_FoodMatch'].append(optload_served / max(served_data['FoodMatch'][i], 0.1))
    else:
        ratios['vs_Insertion'].append(0)
        ratios['vs_ExactLIFO'].append(0)
        ratios['vs_FoodMatch'].append(0)

ax.plot(N_VALUES, ratios['vs_Insertion'], marker='s', color='#3498db', label='vs Insertion', linewidth=2)
ax.plot(N_VALUES, ratios['vs_ExactLIFO'], marker='^', color='#e74c3c', label='vs ExactLIFO', linewidth=2)
ax.plot(N_VALUES, ratios['vs_FoodMatch'], marker='D', color='#9b59b6', label='vs FoodMatch', linewidth=2)
ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, label='Equal Performance')

ax.set_xlabel('Number of Requests (N)')
ax.set_ylabel('OptLoad / Competitor Ratio')
ax.set_title('OptLoad Performance Advantage (Requests Served)')
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
ax.set_xticks(N_VALUES)
plt.tight_layout()
plt.savefig('results/charts/optload_advantage.png', dpi=300, bbox_inches='tight')
plt.savefig('results/charts/optload_advantage.pdf', bbox_inches='tight')
plt.close()

# ============ Generate Summary Table ============
print("\n" + "="*80)
print("EXPERIMENT SUMMARY TABLE")
print("="*80)

print(f"\n{'N':<6} {'Algorithm':<12} {'Completed':<12} {'Served':<12} {'LU Cost':<12} {'Runtime(s)':<12}")
print("-" * 66)

for n in N_VALUES:
    n_str = str(n)
    for algo in ALGORITHMS:
        if n_str in summary and algo in summary[n_str]:
            d = summary[n_str][algo]
            completed = f"{d['count']}/{d['total']}"
            served = f"{d['served_mean']:.1f}±{d['served_std']:.1f}"
            lu = f"{d['lu_cost_mean']:.1f}±{d['lu_cost_std']:.1f}"
            runtime = f"{d['runtime_mean']/1000:.2f}"
            print(f"{n:<6} {algo:<12} {completed:<12} {served:<12} {lu:<12} {runtime:<12}")
    print("-" * 66)

# Calculate overall statistics
print("\n" + "="*80)
print("KEY FINDINGS")
print("="*80)

# OptLoad advantage calculation
total_optload_served = sum(served_data['OptLoad'])
total_insertion_served = sum(served_data['Insertion'])
total_lifo_served = sum(served_data['ExactLIFO'])
total_foodmatch_served = sum(served_data['FoodMatch'])

print(f"\nTotal Requests Served (across all N):")
print(f"  OptLoad:    {total_optload_served:.1f}")
print(f"  Insertion:  {total_insertion_served:.1f}")
print(f"  ExactLIFO:  {total_lifo_served:.1f}")
print(f"  FoodMatch:  {total_foodmatch_served:.1f}")

print(f"\nOptLoad Performance Advantage:")
print(f"  vs Insertion:  {total_optload_served/total_insertion_served:.2f}x more requests served")
print(f"  vs ExactLIFO:  {total_optload_served/total_lifo_served:.2f}x more requests served")
print(f"  vs FoodMatch:  {total_optload_served/total_foodmatch_served:.2f}x more requests served")

print("\n" + "="*80)
print(f"All plots saved to: results/charts/")
print("="*80)
