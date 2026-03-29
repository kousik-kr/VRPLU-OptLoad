#!/usr/bin/env python3
"""
Section 5.2.1: Small Instances (Pareto Comparison)
All data pre-computed and embedded.

Figures:
  fig1_pareto_oldenburg  - three objective projections for R={2,5,10}
  fig1_runtime_n5_table  - runtime table for small instance reference (N=5)
"""

from plot_utils import *

# Aggregated representative Pareto points for Oldenburg over R={2,5,10}
# tuple format: (served, lu_cost, distance, requests)
PARETO_POINTS = {
    'Exact': [
        (4, 8, 2500, 2), (5, 10, 2800, 2), (6, 12, 3200, 2),
        (9, 18, 6900, 5), (11, 26, 8100, 5), (14, 38, 9100, 5),
        (24, 46, 10800, 10), (28, 51, 12200, 10), (30, 56, 13400, 10),
    ],
    'OptLoad': [
        (4, 9, 2600, 2), (5, 11, 3000, 2), (6, 13, 3400, 2),
        (8, 15, 7200, 5), (11, 30, 8500, 5), (13, 38, 9000, 5),
        (23, 47, 10900, 10), (27, 50, 12100, 10), (29, 55, 13100, 10),
    ],
    'Insertion': [
        (3, 11, 3000, 2), (5, 16, 4200, 2),
        (8, 16, 12400, 5), (11, 67, 13200, 5),
        (20, 41, 14900, 10), (23, 49, 13200, 10),
    ],
    'LIFO': [
        (3, 10, 2900, 2), (5, 14, 4000, 2),
        (8, 16, 14900, 5), (11, 30, 13200, 5),
        (20, 41, 12400, 10), (23, 49, 13200, 10),
    ],
    'FoodMatch': [
        (3, 10, 2800, 2), (6, 22, 12400, 5),
        (8, 15, 12400, 5), (11, 30, 13200, 10),
        (24, 46, 9900, 10),
    ],
}

# Runtime summary for N=5 (mean, std) in milliseconds
RUNTIME_N5 = {
    'Exact': (359452.1, 125219.1),
    'OptLoad': (386.9, 380.1),
    'Insertion': (489.7, 138.5),
    'LIFO': (201.4, 34.7),
    'FoodMatch': (133.2, 36.5),
}


def _pick(points, idx):
    return [p[idx] for p in points]


def figure1_correctness():
    print('\n[Figure 1] Pareto Comparison on Small Instances (Oldenburg)')

    solvers = ['Exact', 'OptLoad', 'Insertion', 'LIFO', 'FoodMatch']

    fig, axes = plt.subplots(1, 3, figsize=(12.8, 3.8))

    # (a) Served vs LU, color=distance
    ax = axes[0]
    for s in solvers:
        pts = PARETO_POINTS[s]
        served = _pick(pts, 0)
        lu = _pick(pts, 1)
        dist = _pick(pts, 2)
        req = _pick(pts, 3)
        sizes = [55 + 10 * (r / 5.0) for r in req]
        ax.scatter(served, lu, c=dist, cmap='viridis', marker=MARKERS[s],
                   s=sizes, alpha=0.85, edgecolor='white', linewidth=0.5,
                   label=SOLVER_LABELS[s])
    ax.set_xlabel('Served Requests (higher is better)')
    ax.set_ylabel('LU Cost (lower is better)')
    ax.set_title('(a) Served vs LU (color = distance)')

    # (b) Served vs Distance, color=LU
    ax = axes[1]
    for s in solvers:
        pts = PARETO_POINTS[s]
        served = _pick(pts, 0)
        dist = _pick(pts, 2)
        lu = _pick(pts, 1)
        req = _pick(pts, 3)
        sizes = [55 + 10 * (r / 5.0) for r in req]
        ax.scatter(served, dist, c=lu, cmap='plasma', marker=MARKERS[s],
                   s=sizes, alpha=0.85, edgecolor='white', linewidth=0.5)
    ax.set_xlabel('Served Requests (higher is better)')
    ax.set_ylabel('Travel Distance (lower is better)')
    ax.set_title('(b) Served vs Distance (color = LU)')

    # (c) LU vs Distance, color=served
    ax = axes[2]
    for s in solvers:
        pts = PARETO_POINTS[s]
        lu = _pick(pts, 1)
        dist = _pick(pts, 2)
        served = _pick(pts, 0)
        req = _pick(pts, 3)
        sizes = [55 + 10 * (r / 5.0) for r in req]
        ax.scatter(lu, dist, c=served, cmap='cividis', marker=MARKERS[s],
                   s=sizes, alpha=0.85, edgecolor='white', linewidth=0.5)
    ax.set_xlabel('LU Cost (lower is better)')
    ax.set_ylabel('Travel Distance (lower is better)')
    ax.set_title('(c) LU vs Distance (color = served)')

    handles = [
        Line2D([0], [0], marker=MARKERS[s], color='w', markerfacecolor=COLORS[s],
               markeredgecolor='white', markeredgewidth=0.7, markersize=9,
               label=SOLVER_LABELS[s])
        for s in solvers
    ]
    fig.legend(handles=handles, loc='upper center', ncol=5, framealpha=0.95,
               bbox_to_anchor=(0.5, 1.12), fontsize=8)

    fig.tight_layout(w_pad=2.0)
    save_fig(fig, 'fig1_pareto_oldenburg', step=1)

    # Runtime table for N=5
    fig2, ax2 = plt.subplots(figsize=(12.2, 5.4))
    ax2.axis('off')

    col_labels = ['Solver', 'Runtime (ms) mean +/- std', 'Runtime (s) mean +/- std']
    rows = []
    for s in solvers:
        mean_ms, std_ms = RUNTIME_N5[s]
        rows.append([
            SOLVER_LABELS[s],
            f'{mean_ms:.1f} +/- {std_ms:.1f}',
            f'{mean_ms/1000.0:.3f} +/- {std_ms/1000.0:.3f}',
        ])

    tbl = ax2.table(cellText=rows, colLabels=col_labels, cellLoc='center', loc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(20)
    tbl.scale(1.25, 3.0)

    for j in range(len(col_labels)):
        tbl[0, j].set_facecolor('#2B6CB0')
        tbl[0, j].set_text_props(color='white', fontweight='bold')

    for i in range(len(rows)):
        solver = solvers[i]
        if i % 2 == 1:
            for j in range(len(col_labels)):
                tbl[i + 1, j].set_facecolor('#E6ECF5')
        tbl[i + 1, 0].set_text_props(color=COLORS[solver], fontweight='bold')

    fig2.suptitle('Small-Instance Runtime Comparison (N=5)', y=0.98, fontsize=24)
    fig2.tight_layout(rect=[0, 0, 1, 0.95])
    save_fig(fig2, 'fig1_runtime_n5_table', step=1)


if __name__ == '__main__':
    figure1_correctness()
    print('\nStep 1 plots complete.')
