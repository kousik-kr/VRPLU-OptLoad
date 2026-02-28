#!/usr/bin/env python3
"""
Step 1: Correctness Validation (Small Instances)
All data pre-computed and embedded — no CSV dependency.

Figures:
  fig1_correctness    — 1×3 bar chart (quality, LU cost, Pareto size)
  fig1b_pareto_front  — Pareto front scatter example (N=5)
"""

from plot_utils import *

# ───────────────────────────────────────────────────────────────────
# Embedded data — {solver: {n: (mean, err)}}
# ───────────────────────────────────────────────────────────────────
SERVED = {
    'Exact':     {2: (4.9, 1.7012), 5: (11.2, 2.1274)},
    'OptLoad':   {2: (1.0, 1.5453), 5: (5.8, 3.8715)},
    'Insertion': {2: (4.7, 1.8176), 5: (9.5, 2.5066)},
    'LIFO':      {2: (6.1, 1.4872), 5: (11.4, 1.6589)},
    'FoodMatch': {2: (5.2, 1.8715), 5: (5.0, 1.3904)},
}

LU_COST = {
    'Exact':     {2: (10.6, 4.3212), 5: (31.6, 7.6839)},
    'OptLoad':   {2: (8.5, 57.1779), 5: (27.6667, 11.0598)},
    'Insertion': {2: (10.2, 4.5469), 5: (31.2, 7.8711)},
    'LIFO':      {2: (14.8, 4.4712), 5: (39.6, 10.6222)},
    'FoodMatch': {2: (11.4, 4.5394), 5: (11.3, 4.0754)},
}

PARETO_SIZE = {
    'Exact':     {2: (1.6, 0.5002), 5: (9.6, 2.5946)},
    'OptLoad':   {2: (0.6, 0.5002), 5: (3.8, 4.2895)},
    'Insertion': {2: (1.0, 0.0),    5: (1.0, 0.0)},
    'LIFO':      {2: (1.0, 0.0),    5: (1.0, 0.0)},
    'FoodMatch': {2: (1.0, 0.0),    5: (1.0, 0.0)},
}

# Pareto front scatter example — raw (lu_cost, served) points
PARETO_SCATTER = {
    'Exact': [
        (48.0, 15.0), (38.0, 14.0), (26.0, 12.0), (22.0, 11.0),
        (24.0, 11.0), (20.0, 10.0), (18.0, 9.0), (14.0, 7.0),
        (12.0, 6.0), (10.0, 5.0), (8.0, 4.0), (4.0, 2.0), (2.0, 1.0),
    ],
    'OptLoad': [
        (48.0, 14.0), (38.0, 14.0), (38.0, 14.0), (38.0, 14.0),
        (48.0, 14.0), (48.0, 14.0), (48.0, 14.0), (38.0, 14.0),
        (38.0, 14.0), (48.0, 14.0), (38.0, 14.0), (48.0, 14.0),
        (38.0, 14.0), (38.0, 14.0), (38.0, 14.0), (48.0, 14.0),
        (38.0, 14.0), (38.0, 14.0), (38.0, 14.0), (48.0, 14.0),
    ],
    'Insertion': [(48.0, 15.0)],
    'LIFO':      [(77.0, 16.0)],
    'FoodMatch': [(22.0, 6.0)],
}


def figure1_correctness():
    print('\n[Figure 1] Step 1 — Correctness Validation')

    solvers_order = ['Exact', 'OptLoad', 'Insertion', 'LIFO', 'FoodMatch']
    n_values = [2, 5]

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6))

    # (a) Best requests served
    ax = axes[0]
    x = np.arange(len(n_values))
    w = 0.15
    for i, s in enumerate(solvers_order):
        vals = [SERVED[s][n][0] for n in n_values]
        errs = [SERVED[s][n][1] for n in n_values]
        ax.bar(x + i * w, vals, w, yerr=errs, capsize=2,
               color=COLORS[s], label=SOLVER_LABELS[s],
               edgecolor='white', linewidth=0.5)
    ax.set_xticks(x + 2 * w)
    ax.set_xticklabels([f'N={n}' for n in n_values])
    ax.set_ylabel('Best Requests Served')
    ax.set_title('(a) Solution Quality')

    # (b) LU cost
    ax = axes[1]
    for i, s in enumerate(solvers_order):
        vals = [LU_COST[s][n][0] for n in n_values]
        errs = [LU_COST[s][n][1] for n in n_values]
        ax.bar(x + i * w, vals, w, yerr=errs, capsize=2,
               color=COLORS[s], edgecolor='white', linewidth=0.5)
    ax.set_xticks(x + 2 * w)
    ax.set_xticklabels([f'N={n}' for n in n_values])
    ax.set_ylabel('LU Cost (best route)')
    ax.set_title('(b) Loading/Unloading Cost')

    # (c) Pareto set size
    ax = axes[2]
    for i, s in enumerate(solvers_order):
        vals = [PARETO_SIZE[s][n][0] for n in n_values]
        errs = [PARETO_SIZE[s][n][1] for n in n_values]
        ax.bar(x + i * w, vals, w, yerr=errs, capsize=2,
               color=COLORS[s], edgecolor='white', linewidth=0.5)
    ax.set_xticks(x + 2 * w)
    ax.set_xticklabels([f'N={n}' for n in n_values])
    ax.set_ylabel('Pareto Set Size')
    ax.set_title('(c) Trade-off Diversity')

    axes[0].legend(loc='upper left', framealpha=0.9, ncol=1, fontsize=7)
    fig.tight_layout(w_pad=1.5)
    save_fig(fig, 'fig1_correctness', step=1)

    # ---- Pareto front scatter example ----
    fig2, ax2 = plt.subplots(figsize=(3.5, 2.8))
    for s in ['Exact', 'OptLoad']:
        pts = PARETO_SCATTER[s]
        lus = [p[0] for p in pts]
        svd = [p[1] for p in pts]
        ax2.scatter(lus, svd, c=COLORS[s], marker=MARKERS[s], s=40,
                   label=SOLVER_LABELS[s], alpha=0.8, zorder=3)
        # Connect sorted Pareto front
        sorted_pts = sorted(pts, key=lambda p: p[1])
        ax2.plot([p[0] for p in sorted_pts], [p[1] for p in sorted_pts],
                color=COLORS[s], alpha=0.4, linewidth=1)
    for s in ['Insertion', 'LIFO', 'FoodMatch']:
        pts = PARETO_SCATTER[s]
        ax2.scatter([p[0] for p in pts], [p[1] for p in pts],
                   c=COLORS[s], marker=MARKERS[s], s=50,
                   label=SOLVER_LABELS[s], zorder=3)
    ax2.set_xlabel('LU Cost')
    ax2.set_ylabel('Requests Served')
    ax2.set_title('Pareto Front Example (N=5)')
    ax2.legend(fontsize=7, loc='best', framealpha=0.9)
    fig2.tight_layout()
    save_fig(fig2, 'fig1b_pareto_front', step=1)


if __name__ == '__main__':
    figure1_correctness()
    print('\nStep 1 plots complete.')
