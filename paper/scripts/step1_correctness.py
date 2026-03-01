#!/usr/bin/env python3
"""
Step 1: Correctness Validation (Small Instances)
All data pre-computed and embedded — no CSV dependency.

Figures:
  fig1_correctness    — 1×5 bar chart (quality, LU cost, distance, runtime, Pareto size)
  fig1b_pareto_front  — Pareto front scatter example (N=5)
"""

from plot_utils import *

# ───────────────────────────────────────────────────────────────────
# Embedded data — {solver: {n: (mean, err)}}
# ───────────────────────────────────────────────────────────────────
SERVED = {
    'Exact':     {2: (14.9, 3.7012), 5: (21.2, 2.1274)},
    'OptLoad':   {2: (14.0, 2.5453), 5: (15.8, 2.8715)},
    'Insertion': {2: (3.7, 1.8176), 5: (6.5, 2.5066)},
    'LIFO':      {2: (6.1, 1.4872), 5: (9.4, 1.6589)},
    'FoodMatch': {2: (3.2, 1.8715), 5: (5.2, 1.3904)},
}

LU_COST = {
    'Exact':     {2: (40.6, 4.3212), 5: (51.6, 2.6839)},
    'OptLoad':   {2: (48.5, 5.1779), 5: (57.6667, 3.0598)},
    'Insertion': {2: (80.2, 4.5469), 5: (101.2, 4.8711)},
    'LIFO':      {2: (34.8, 2.4712), 5: (39.6, 3.6222)},
    'FoodMatch': {2: (11.4, 4.5394), 5: (11.3, 4.0754)},
}

RUNTIME_MS = {
    'Exact':     {2: (180.5, 40.0312), 5: (359452.1, 125219.1011)},
    'OptLoad':   {2: (195.2, 33.2804), 5: (386.9, 380.0731)},
    'Insertion': {2: (119.8, 29.6491), 5: (489.7, 138.4759)},
    'LIFO':      {2: (84.3, 19.6302), 5: (201.4, 34.7409)},
    'FoodMatch': {2: (74.4, 18.4704), 5: (133.2, 36.5051)},
}

DISTANCE = {
    'Exact':     {2: (12202.7, 5621.5293), 5: (8071.8, 2234.4141)},
    'OptLoad':   {2: (16337.4, 1676.3924), 5: (23552.0, 9630.9593)},
    'Insertion': {2: (15050.2, 4547.7031), 5: (29658.4, 6119.2939)},
    'LIFO':      {2: (19159.4, 6785.7320), 5: (33053.3, 4639.1527)},
    'FoodMatch': {2: (14460.0, 6798.0153), 5: (12929.5, 6011.1115)},
}

PARETO_SIZE = {
    'Exact':     {2: (10.6, 2.5002), 5: (29.6, 2.5946)},
    'OptLoad':   {2: (2.6, 1.1002), 5: (7.8, 2.2895)},
    'Insertion': {2: (1.0, 1.0),    5: (1.0, 1.0)},
    'LIFO':      {2: (1.0, 1.0),    5: (1.0, 1.0)},
    'FoodMatch': {2: (1.0, 1.0),    5: (1.0, 1.0)},
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
    'Insertion': [(68.0, 11.0)],
    'LIFO':      [(16.0, 8.0)],
    'FoodMatch': [(22.0, 6.0)],
}


def figure1_correctness():
    print('\n[Figure 1] Step 1 — Correctness Validation')

    solvers_order = ['Exact', 'OptLoad', 'Insertion', 'LIFO', 'FoodMatch']
    n_values = [2, 5]

    panels = [
        ('(a) Solution Quality',        'Best Requests Served', SERVED),
        ('(b) Loading/Unloading Cost',   'LU Cost (best route)', LU_COST),
        ('(c) Travel Distance',          'Distance (best route)', DISTANCE),
        ('(d) Runtime',                  'Runtime (ms)',          RUNTIME_MS),
        ('(e) Trade-off Diversity',      'Pareto Set Size',       PARETO_SIZE),
    ]

    fig, axes = plt.subplots(1, 5, figsize=(15, 2.8))
    x = np.arange(len(n_values))
    w = 0.15

    for ax, (title, ylabel, data) in zip(axes, panels):
        for i, s in enumerate(solvers_order):
            vals = [data[s][n][0] for n in n_values]
            ax.bar(x + i * w, vals, w,
                   color=COLORS[s], label=SOLVER_LABELS[s],
                   edgecolor='white', linewidth=0.5)
        ax.set_xticks(x + 2 * w)
        ax.set_xticklabels([f'N={n}' for n in n_values])
        ax.set_ylabel(ylabel)
        ax.set_title(title)

    # Log scale for runtime (Exact N=5 is ~360 s vs others ~0.1–0.5 s)
    axes[3].set_yscale('log')
    axes[3].set_ylabel('Runtime (ms, log)')

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