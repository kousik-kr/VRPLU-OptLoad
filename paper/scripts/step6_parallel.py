#!/usr/bin/env python3
"""Step 6: Time-window sensitivity with runtime table + 1x3 scatter row."""

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


def figure6_parallel():
    print('\n[Step 6] Sensitivity (Time Window): runtime table + served/LU/distance scatter')

    tw = [30, 60, 90, 120]

    served = [
        ('OptLoad-S', [69, 78, 83, 85]),
        ('OptLoad-LU', [63, 71, 75, 78]),
        ('OptLoad-D', [65, 74, 78, 80]),
        ('Insertion', [49, 53, 56, 58]),
        ('LIFO', [47, 51, 54, 56]),
        ('FoodMatch', [48, 52, 55, 57]),
    ]
    lu = [
        ('OptLoad-S', [149, 162, 170, 176]),
        ('OptLoad-LU', [116, 126, 133, 138]),
        ('OptLoad-D', [128, 139, 146, 152]),
        ('Insertion', [169, 185, 195, 203]),
        ('LIFO', [177, 194, 204, 212]),
        ('FoodMatch', [173, 190, 200, 208]),
    ]
    distance = [
        ('OptLoad-S', [461, 449, 445, 442]),
        ('OptLoad-LU', [451, 441, 438, 435]),
        ('OptLoad-D', [413, 401, 398, 396]),
        ('Insertion', [448, 438, 435, 433]),
        ('LIFO', [443, 434, 431, 429]),
        ('FoodMatch', [452, 442, 439, 437]),
    ]
    runtime = [
        ('OptLoad-S', [295, 356, 412, 466]),
        ('OptLoad-LU', [273, 329, 381, 431]),
        ('OptLoad-D', [280, 338, 392, 445]),
        ('Insertion', [85, 97, 108, 119]),
        ('LIFO', [78, 89, 99, 109]),
        ('FoodMatch', [89, 102, 114, 126]),
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
        colLabels=['Solver', 'TW=30', 'TW=60', 'TW=90', 'TW=120'],
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

    scatter_series(axes[0], tw, served, 'Served Requests', 'Time Window')
    add_panel_caption(axes[0], '(b) Served vs TW')

    scatter_series(axes[1], tw, lu, 'LU Cost', 'Time Window')
    add_panel_caption(axes[1], '(c) LU vs TW')

    scatter_series(axes[2], tw, distance, 'Distance', 'Time Window')
    add_panel_caption(axes[2], '(d) Distance vs TW')

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

    save_fig(fig, 'sensitivity_timewindow_2x2', step=6)


if __name__ == '__main__':
    figure6_parallel()
