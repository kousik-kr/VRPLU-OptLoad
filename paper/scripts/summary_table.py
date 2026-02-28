#!/usr/bin/env python3
"""
Summary Table: Comparison of all solvers on key metrics.
All data pre-computed and embedded — no CSV dependency.

Figures:
  table_summary — rendered table figure (PDF + PNG)
"""

from plot_utils import *

# ───────────────────────────────────────────────────────────────────
# Embedded data
# ───────────────────────────────────────────────────────────────────
SUMMARY_DATA = [
    {'solver': 'OptLoad',   'avg_served': 3.475,  'avg_runtime_s': 9.1241,   'avg_pareto': 1.3, 'feasibility_pct': 36.25},
    {'solver': 'Insertion', 'avg_served': 12.5125, 'avg_runtime_s': 106.8976, 'avg_pareto': 1.0, 'feasibility_pct': 100.0},
    {'solver': 'FoodMatch', 'avg_served': 9.2125,  'avg_runtime_s': 7.62,     'avg_pareto': 1.0, 'feasibility_pct': 100.0},
    {'solver': 'LIFO',      'avg_served': 14.575,  'avg_runtime_s': 13.2835,  'avg_pareto': 1.0, 'feasibility_pct': 100.0},
]

SOLVER_DISPLAY = {
    'OptLoad': 'OptLoad', 'Insertion': 'Insertion',
    'FoodMatch': 'FoodMatch', 'LIFO': 'LIFO',
}


def figure_summary_table():
    print('\n[Table] Summary Comparison')

    col_labels = ['Solver', 'Avg Served', 'Avg Runtime (s)', 'Avg Pareto Size', 'Feasibility (%)']
    cell_text = []
    for row in SUMMARY_DATA:
        cell_text.append([
            SOLVER_DISPLAY[row['solver']],
            f"{row['avg_served']:.1f}",
            f"{row['avg_runtime_s']:.1f}",
            f"{row['avg_pareto']:.1f}",
            f"{row['feasibility_pct']:.0f}",
        ])

    # Print to console
    header = '  '.join(f'{c:>16s}' for c in col_labels)
    print(header)
    for r in cell_text:
        print('  '.join(f'{v:>16s}' for v in r))

    # Render as figure
    fig, ax = plt.subplots(figsize=(5.5, 1.8))
    ax.axis('off')

    tbl = ax.table(cellText=cell_text, colLabels=col_labels, loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.0, 1.5)
    for j in range(len(col_labels)):
        tbl[0, j].set_facecolor('#2166AC')
        tbl[0, j].set_text_props(color='white', fontweight='bold')
    for i in range(len(cell_text)):
        for j in range(len(col_labels)):
            if i % 2 == 1:
                tbl[i+1, j].set_facecolor('#E8F0FE')

    fig.tight_layout()
    save_fig(fig, 'table_summary', step='summary')


if __name__ == '__main__':
    figure_summary_table()
    print('\nSummary table complete.')
