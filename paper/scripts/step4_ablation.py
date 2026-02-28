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
    'OptLoad':     {5: 6.3159, 10: 0.6016, 15: 11.2502, 20: 0.463, 25: 13.415, 30: 17.3342, 35: 16.234, 40: 0.6027},
    'NoCluster':   {5: 410.8322, 10: 121.2852, 15: 58.2464, 20: 4.4706, 25: 117.9, 30: 125.068, 35: 151.6496, 40: 9.9376},
    'NoLUPruning': {5: 6.4612, 10: 0.5886, 15: 11.3087, 20: 0.4922, 25: 13.5283, 30: 17.6219, 35: 17.5817, 40: 0.6018},
}

# {solver: {n: mean_prefixes}}
PREFIXES = {
    'OptLoad':     {5: 15.8, 10: 16.9, 15: 24.8, 20: 8.2, 25: 22.1, 30: 26.0, 35: 20.5, 40: 13.9},
    'NoCluster':   {5: 83.2857, 10: 3.6667, 15: 1.0, 20: 1.0, 25: 1.0, 30: 1.0, 35: 1.0, 40: 1.0},
    'NoLUPruning': {5: 15.8, 10: 16.9, 15: 24.8, 20: 8.2, 25: 22.1, 30: 26.0, 35: 20.5, 40: 13.9},
}

# Runtime ratios: [(n, ratio)]
RATIO_NC = [(5, 65.0473), (10, 201.6044), (15, 5.1774), (20, 9.6557), (25, 8.7887), (30, 7.2151), (35, 9.3415), (40, 16.4885)]
RATIO_NL = [(5, 1.023), (10, 0.9784), (15, 1.0052), (20, 1.0631), (25, 1.0084), (30, 1.0166), (35, 1.083), (40, 0.9985)]


def figure4_ablation():
    print('\n[Figure 4] Step 4 — Ablation Study')

    solvers = ['OptLoad', 'NoCluster', 'NoLUPruning']
    n_vals = [5, 10, 15, 20, 25, 30, 35, 40]

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.8))

    # (a) Runtime vs N
    ax = axes[0]
    for s in solvers:
        ns = sorted(RUNTIME[s].keys())
        vals = [RUNTIME[s][n] for n in ns]
        ax.plot(ns, vals, marker=MARKERS[s], color=COLORS[s], label=SOLVER_LABELS[s])
    ax.set_yscale('log')
    ax.set_xlabel('Number of Requests (N)')
    ax.set_ylabel('Runtime (s)')
    ax.set_title('(a) Computation Time')
    ax.legend(fontsize=7)

    # (b) Prefixes explored
    ax = axes[1]
    for s in solvers:
        ns = sorted(PREFIXES[s].keys())
        vals = [PREFIXES[s][n] for n in ns]
        ax.plot(ns, vals, marker=MARKERS[s], color=COLORS[s], label=SOLVER_LABELS[s])
    ax.set_xlabel('Number of Requests (N)')
    ax.set_ylabel('Prefixes Explored')
    ax.set_title('(b) Search Effort')

    # (c) Runtime ratio
    ax = axes[2]
    ns_nc = [p[0] for p in RATIO_NC]
    rs_nc = [p[1] for p in RATIO_NC]
    ns_nl = [p[0] for p in RATIO_NL]
    rs_nl = [p[1] for p in RATIO_NL]
    ax.plot(ns_nc, rs_nc, marker=MARKERS['NoCluster'], color=COLORS['NoCluster'],
            label='No Clustering / OptLoad')
    ax.plot(ns_nl, rs_nl, marker=MARKERS['NoLUPruning'], color=COLORS['NoLUPruning'],
            label='No LU Pruning / OptLoad')
    ax.axhline(y=1.0, color='gray', linestyle=':', linewidth=1, alpha=0.7)
    ax.set_xlabel('Number of Requests (N)')
    ax.set_ylabel('Runtime Ratio')
    ax.set_title('(c) Component Impact')
    ax.legend(fontsize=7)

    fig.tight_layout(w_pad=1.5)
    save_fig(fig, 'fig4_ablation', step=4)


if __name__ == '__main__':
    figure4_ablation()
    print('\nStep 4 plots complete.')
