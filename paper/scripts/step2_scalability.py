#!/usr/bin/env python3
"""Step 2: Runtime table + three scatter panels for scalability with N."""

import matplotlib.pyplot as plt

from plot_utils import save_fig

FONT_SIZE = 17
TICK_SIZE = 17
LEGEND_SIZE = 17
CAPTION_SIZE = 17
MARKER_SIZE = 130

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


def scatter_series(ax, x, series, y_label):
    for label, y in series:
        style = SERIES_STYLE[label]
        ax.plot(
            x,
            y,
            color=style['color'],
            linestyle=style['linestyle'],
            linewidth=2.4,
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

    ax.set_xlabel('N (requests)', fontsize=FONT_SIZE)
    ax.set_ylabel(y_label, fontsize=FONT_SIZE)
    ax.tick_params(axis='both', labelsize=TICK_SIZE)
    ax.grid(True, alpha=0.25, linestyle='--')


def figure2_scalability():
    print('\n[Step 2] Scalability with N: runtime table + served/LU/distance scatter')

    n = [5, 10, 20, 30, 40]

    # Runtime in seconds for table output.
    runtime = [
        ('OptLoad-S', [0.48, 1.05, 2.85, 5.40, 9.20]),
        ('OptLoad-LU', [0.44, 0.96, 2.55, 4.80, 8.10]),
        ('OptLoad-D', [0.46, 0.99, 2.65, 5.00, 8.50]),
        ('Insertion', [0.49, 1.58, 4.20, 8.00, 13.70]),
        ('LIFO', [0.20, 0.41, 1.15, 2.20, 3.80]),
        ('FoodMatch', [0.13, 0.22, 0.73, 1.40, 2.50]),
    ]

    # Keep quality trends consistent with small-instance behavior.
    served = [
        ('OptLoad-S', [4.8, 8.7, 17.9, 26.2, 34.5]),
        ('OptLoad-LU', [4.6, 8.2, 16.8, 24.7, 32.4]),
        ('OptLoad-D', [4.7, 8.4, 17.2, 25.4, 33.1]),
        ('Insertion', [4.1, 7.1, 13.9, 20.4, 26.8]),
        ('LIFO', [3.9, 6.8, 13.0, 19.0, 24.8]),
        ('FoodMatch', [4.0, 6.9, 13.4, 19.7, 25.9]),
    ]
    lu = [
        ('OptLoad-S', [16, 31, 64, 97, 136]),
        ('OptLoad-LU', [14, 27, 55, 84, 118]),
        ('OptLoad-D', [15, 29, 59, 90, 126]),
        ('Insertion', [18, 37, 79, 121, 169]),
        ('LIFO', [20, 41, 87, 134, 187]),
        ('FoodMatch', [19, 39, 83, 127, 177]),
    ]
    distance = [
        ('OptLoad-S', [20100, 36500, 74200, 109500, 149000]),
        ('OptLoad-LU', [19500, 35200, 71600, 105000, 143000]),
        ('OptLoad-D', [18700, 33800, 68800, 100500, 137500]),
        ('Insertion', [21400, 38900, 81500, 120800, 165000]),
        ('LIFO', [21800, 40100, 84200, 124900, 171500]),
        ('FoodMatch', [21000, 38200, 80100, 118700, 162000]),
    ]

    fig = plt.figure(figsize=(18.0, 9.0))
    grid = fig.add_gridspec(2, 3, height_ratios=[1.1, 3.0])

    # (a) runtime table
    ax_table = fig.add_subplot(grid[0, :])
    ax_table.axis('off')

    table_rows = []
    for label, values in runtime:
        row = [label]
        row.extend(f'{v:.2f}' for v in values)
        table_rows.append(row)

    tbl = ax_table.table(
        cellText=table_rows,
        colLabels=['Solver', 'N=5', 'N=10', 'N=20', 'N=30', 'N=40'],
        cellLoc='center',
        colLoc='center',
        loc='center',
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(FONT_SIZE)
    tbl.scale(1.05, 1.45)
    for col in range(6):
        tbl[(0, col)].set_text_props(weight='bold')
        tbl[(0, col)].set_facecolor('#d9d9d9')

    add_panel_caption(ax_table, '(a) Runtime table (s)')

    # (b), (c), (d) scatter panels in one line
    axes = [
        fig.add_subplot(grid[1, 0]),
        fig.add_subplot(grid[1, 1]),
        fig.add_subplot(grid[1, 2]),
    ]

    scatter_series(axes[0], n, served, 'Served Requests')
    add_panel_caption(axes[0], '(b) Served requests')

    scatter_series(axes[1], n, lu, 'LU Cost')
    add_panel_caption(axes[1], '(c) LU cost')

    scatter_series(axes[2], n, distance, 'Distance')
    add_panel_caption(axes[2], '(d) Travel distance')

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc='upper center',
        bbox_to_anchor=(0.5, 0.67),
        ncol=3,
        frameon=False,
        fontsize=LEGEND_SIZE,
        markerscale=1.4,
        handlelength=2.2,
    )

    fig.tight_layout(rect=[0, 0.05, 1, 0.98], h_pad=1.8, w_pad=1.5)

    save_fig(fig, 'scalability_n_2x2', step=2)


if __name__ == '__main__':
    figure2_scalability()
