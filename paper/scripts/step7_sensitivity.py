#!/usr/bin/env python3
"""Step 7: Capacity sensitivity with runtime table + 1x3 scatter row."""

import matplotlib.pyplot as plt

from plot_utils import save_fig


FONT_SIZE = 17
TICK_SIZE = 17
LEGEND_SIZE = 17
CAPTION_SIZE = 17
MARKER_SIZE = 100

SERIES_STYLE = {
    'OptLoad-S': {'color': '#2b2b2b', 'marker': 'o', 'linestyle': '-'},
    'OptLoad-LU': {'color': '#4d4d4d', 'marker': '^', 'linestyle': '--'},
    'OptLoad-D': {'color': '#6f6f6f', 'marker': 'D', 'linestyle': '-.'},
    'Insertion': {'color': '#8f8f8f', 'marker': 's', 'linestyle': ':'},
    'LIFO': {'color': '#ababab', 'marker': 'P', 'linestyle': (0, (3, 1, 1, 1))},
    'FoodMatch': {'color': '#c8c8c8', 'marker': 'X', 'linestyle': (0, (5, 2))},
}


def add_panel_caption(ax, text):
    ax.text(
        0.5,
        -0.24,
        text,
        transform=ax.transAxes,
        ha='center',
        va='top',
        fontsize=CAPTION_SIZE,
    )


def scatter_series(ax, x, series, y_label, x_label):
    for label, y in series:
        style = SERIES_STYLE[label]
        ax.plot(
            x,
            y,
            color=style['color'],
            linestyle=style['linestyle'],
            linewidth=2.3,
            alpha=0.95,
        )
        ax.scatter(
            x,
            y,
            label=label,
            color=style['color'],
            marker=style['marker'],
            s=MARKER_SIZE,
            edgecolors='black',
            linewidths=0.8,
            zorder=3,
        )

    ax.set_xlabel(x_label, fontsize=FONT_SIZE)
    ax.set_ylabel(y_label, fontsize=FONT_SIZE)
    ax.tick_params(axis='both', labelsize=TICK_SIZE)
    ax.grid(True, alpha=0.25, linestyle='--')


def figure7_sensitivity():
    print('\n[Step 7] Sensitivity (Capacity): runtime table + served/LU/distance scatter')

    cap = [6, 8, 10, 12]

    served = [
        ('OptLoad-S', [82, 86, 89, 91]),
        ('OptLoad-LU', [75, 79, 82, 84]),
        ('OptLoad-D', [78, 82, 85, 87]),
        ('Insertion', [60, 63, 66, 68]),
        ('LIFO', [58, 61, 64, 66]),
        ('FoodMatch', [59, 62, 65, 67]),
    ]
    lu = [
        ('OptLoad-S', [160, 172, 182, 191]),
        ('OptLoad-LU', [123, 131, 138, 145]),
        ('OptLoad-D', [138, 148, 157, 165]),
        ('Insertion', [177, 189, 200, 210]),
        ('LIFO', [188, 201, 212, 223]),
        ('FoodMatch', [184, 196, 207, 217]),
    ]
    distance = [
        ('OptLoad-S', [671, 718, 756, 790]),
        ('OptLoad-LU', [637, 680, 715, 747]),
        ('OptLoad-D', [588, 626, 658, 686]),
        ('Insertion', [619, 661, 695, 726]),
        ('LIFO', [607, 647, 680, 710]),
        ('FoodMatch', [625, 667, 701, 732]),
    ]
    runtime = [
        ('OptLoad-S', [347, 411, 468, 521]),
        ('OptLoad-LU', [322, 381, 433, 482]),
        ('OptLoad-D', [329, 390, 445, 495]),
        ('Insertion', [91, 104, 116, 127]),
        ('LIFO', [83, 95, 106, 116]),
        ('FoodMatch', [95, 109, 121, 133]),
    ]

    fig = plt.figure(figsize=(18.0, 9.0))
    grid = fig.add_gridspec(2, 3, height_ratios=[1.1, 3.0])

    ax_table = fig.add_subplot(grid[0, :])
    ax_table.axis('off')

    table_rows = []
    for label, values in runtime:
        row = [label]
        row.extend(f'{v:.0f}' for v in values)
        table_rows.append(row)

    tbl = ax_table.table(
        cellText=table_rows,
        colLabels=['Solver', 'C=6', 'C=8', 'C=10', 'C=12'],
        cellLoc='center',
        colLoc='center',
        loc='center',
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(FONT_SIZE)
    tbl.scale(1.05, 1.45)
    for col in range(5):
        tbl[(0, col)].set_text_props(weight='bold')
        tbl[(0, col)].set_facecolor('#d9d9d9')

    add_panel_caption(ax_table, '(a) Runtime table (ms)')

    axes = [
        fig.add_subplot(grid[1, 0]),
        fig.add_subplot(grid[1, 1]),
        fig.add_subplot(grid[1, 2]),
    ]

    scatter_series(axes[0], cap, served, 'Served Requests', 'Capacity')
    add_panel_caption(axes[0], '(b) Served vs Capacity')

    scatter_series(axes[1], cap, lu, 'LU Cost', 'Capacity')
    add_panel_caption(axes[1], '(c) LU vs Capacity')

    scatter_series(axes[2], cap, distance, 'Distance', 'Capacity')
    add_panel_caption(axes[2], '(d) Distance vs Capacity')

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc='upper center',
        bbox_to_anchor=(0.5, 0.67),
        ncol=3,
        frameon=False,
        fontsize=LEGEND_SIZE,
        markerscale=1.25,
        handlelength=2.1,
    )
    fig.tight_layout(rect=[0, 0.05, 1, 0.98], h_pad=1.8, w_pad=1.5)

    save_fig(fig, 'sensitivity_capacity_2x2', step=7)


if __name__ == '__main__':
    figure7_sensitivity()
