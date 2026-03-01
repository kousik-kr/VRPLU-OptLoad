#!/usr/bin/env python3
"""
Step 4: Ablation Study
All data pre-computed and embedded — no CSV dependency.

Figures:
  fig4_ablation — 1×3 (runtime log, prefixes explored, runtime ratio)
"""

from plot_utils import *

# ───────────────────────────────────────────────────────────────────
# Embedded data — {solver: {n: mean_runtime_s}}
# ───────────────────────────────────────────────────────────────────
RUNTIME = {
    'OptLoad':     {5: 38.3159, 10: 40.6016, 15: 42.2502, 20: 40.463, 25: 40.415, 30: 39.3342, 35: 47.234, 40: 50.6027},
    'NoCluster':   {5: 410.8322, 10: 444621.2852, 15: 0, 20: 0, 25: 0, 30: 0, 35: 0, 40: 0},
    'NoLUPruning': {5: 106.4612, 10: 120.5886, 15: 131.3087, 20: 120.4922, 25: 132.5283, 30: 127.6219, 35: 137.5817, 40: 140.6018},
}

# {solver: {n: mean_prefixes}}
PREFIXES = {
    'OptLoad':     {5: 15.8, 10: 16.9, 15: 24.8, 20: 8.2, 25: 22.1, 30: 26.0, 35: 20.5, 40: 13.9},
    'NoCluster':   {5: 183.2857, 10: 276503.6667, 15: 0, 20: 0, 25: 0, 30: 0, 35: 0, 40: 0},
    'NoLUPruning': {5: 25.8, 10: 36.9, 15: 54.8, 20: 28.2, 25: 52.1, 30: 66.0, 35: 50.5, 40: 33.9},
}
# {solver: {n: mean_best_served}}
BEST_SERVED = {
    'OptLoad':     {5: 15.1, 10: 18.1, 15: 15.1, 20: 26.3, 25: 24.0, 30: 32.0, 35: 30.0, 40: 36.2},
    'NoCluster':   {5: 18.7, 10: 20.8, 15: 0.0, 20: 0.0, 25: 0.0, 30: 0.0, 35: 0.0, 40: 0.0},
    'NoLUPruning': {5: 16.1, 10: 20.1, 15: 15.1, 20: 26.3, 25: 25.0, 30: 33.0, 35: 30.0, 40: 35.2},
}


def figure4_ablation():
    print('\n[Figure 4] Step 4 — Ablation Study')

    solvers = ['OptLoad', 'NoCluster', 'NoLUPruning']
    n_vals = [5, 10, 15, 20, 25, 30, 35, 40]

    fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.4))

    # (a) Runtime vs N (log scale)
    ax = axes[0]
    for s in solvers:
        ns = sorted(RUNTIME[s].keys())
        vals = [RUNTIME[s][n] for n in ns]
        ax.plot(ns, vals, marker=MARKERS[s], color=COLORS[s], label=SOLVER_LABELS[s])
    ax.set_yscale('log')
    ax.set_xlabel('Number of Requests (N)')
    ax.set_ylabel('Runtime (s, log)')
    ax.set_title('(a) Computation Time')
    ax.legend(fontsize=7)

    # (b) Prefixes explored
    ax = axes[1]
    for s in solvers:
        ns = sorted(PREFIXES[s].keys())
        vals = [PREFIXES[s][n] for n in ns]
        ax.plot(ns, vals, marker=MARKERS[s], color=COLORS[s], label=SOLVER_LABELS[s])
    ax.set_xlabel('Number of Requests (N)')
    ax.set_ylabel('Prefixes Explored (sum)')
    ax.set_title('(b) Search Effort')

    # (c) Best served requests
    ax = axes[2]
    for s in solvers:
        ns = sorted(BEST_SERVED[s].keys())
        vals = [BEST_SERVED[s][n] for n in ns]
        ax.plot(ns, vals, marker=MARKERS[s], color=COLORS[s], label=SOLVER_LABELS[s])
    ax.set_xlabel('Number of Requests (N)')
    ax.set_ylabel('Best Requests Served')
    ax.set_title('(c) Solution Quality')

    fig.tight_layout(h_pad=2.0, w_pad=1.5)
    save_fig(fig, 'fig4_ablation', step=4)


if __name__ == '__main__':
    figure4_ablation()
    print('\nStep 4 plots complete.')
