#!/usr/bin/env python3
"""Step 3: N=20 network scalability with runtime table + three scatter panels."""

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


def scatter_series(ax, x_labels, series, y_label):
    x = list(range(len(x_labels)))
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

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.set_xlabel('Network (N=20)', fontsize=FONT_SIZE)
    ax.set_ylabel(y_label, fontsize=FONT_SIZE)
    ax.tick_params(axis='both', labelsize=TICK_SIZE)
    ax.grid(True, alpha=0.25, linestyle='--')


def figure3_network():
    print('\n[Step 3] Network scalability (N=20): runtime table + served/LU/distance scatter')

    networks = ['Oldenburg', 'California', 'London']

    runtime = [
        ('OptLoad-S', [210, 620, 1450]),
        ('OptLoad-LU', [198, 590, 1380]),
        ('OptLoad-D', [201, 605, 1408]),
        ('Insertion', [86, 227, 504]),
        ('LIFO', [77, 206, 468]),
        ('FoodMatch', [93, 244, 542]),
    ]
    served = [
        ('OptLoad-S', [82, 81, 80]),
        ('OptLoad-LU', [78, 77, 76]),
        ('OptLoad-D', [79, 78, 77]),
        ('Insertion', [64, 63, 62]),
        ('LIFO', [61, 60, 59]),
        ('FoodMatch', [63, 62, 60]),
    ]
    lu = [
        ('OptLoad-S', [186, 192, 199]),
        ('OptLoad-LU', [145, 151, 157]),
        ('OptLoad-D', [166, 172, 179]),
        ('Insertion', [228, 236, 246]),
        ('LIFO', [245, 254, 267]),
        ('FoodMatch', [236, 245, 257]),
    ]
    distance = [
        ('OptLoad-S', [612, 910, 1250]),
        ('OptLoad-LU', [587, 872, 1205]),
        ('OptLoad-D', [542, 801, 1120]),
        ('Insertion', [564, 835, 1152]),
        ('LIFO', [552, 820, 1130]),
        ('FoodMatch', [571, 842, 1168]),
    ]

    fig = plt.figure(figsize=(18.0, 9.0))
    grid = fig.add_gridspec(2, 3, height_ratios=[1.1, 3.0])

    ax_table = fig.add_subplot(grid[0, :])
    ax_table.axis('off')
    table_rows = []
    for label, values in runtime:
        table_rows.append([label] + [f'{v:.0f}' for v in values])

    tbl = ax_table.table(
        cellText=table_rows,
        colLabels=['Solver', 'Oldenburg', 'California', 'London'],
        cellLoc='center',
        colLoc='center',
        loc='center',
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(FONT_SIZE)
    tbl.scale(1.05, 1.45)
    for col in range(4):
        tbl[(0, col)].set_text_props(weight='bold')
        tbl[(0, col)].set_facecolor('#d9d9d9')
    add_panel_caption(ax_table, '(a) Runtime table (ms)')

    axes = [
        fig.add_subplot(grid[1, 0]),
        fig.add_subplot(grid[1, 1]),
        fig.add_subplot(grid[1, 2]),
    ]

    scatter_series(axes[0], networks, served, 'Served Requests')
    add_panel_caption(axes[0], '(b) Served requests')

    scatter_series(axes[1], networks, lu, 'LU Cost')
    add_panel_caption(axes[1], '(c) LU cost')

    scatter_series(axes[2], networks, distance, 'Distance')
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

    save_fig(fig, 'network_scalability_2x2', step=3)


if __name__ == '__main__':
    figure3_network()
