#!/usr/bin/env python3
"""Step 6: Combined time-window and capacity sensitivity as a 2x3 figure."""

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
    print('\n[Step 6] Sensitivity (Time Window + Capacity): combined served/LU/distance scatter')

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
    cap = [6, 8, 10, 12]
    served_cap = [
        ('OptLoad-S', [82, 86, 89, 91]),
        ('OptLoad-LU', [75, 79, 82, 84]),
        ('OptLoad-D', [78, 82, 85, 87]),
        ('Insertion', [60, 63, 66, 68]),
        ('LIFO', [58, 61, 64, 66]),
        ('FoodMatch', [59, 62, 65, 67]),
    ]
    lu_cap = [
        ('OptLoad-S', [160, 172, 182, 191]),
        ('OptLoad-LU', [123, 131, 138, 145]),
        ('OptLoad-D', [138, 148, 157, 165]),
        ('Insertion', [177, 189, 200, 210]),
        ('LIFO', [188, 201, 212, 223]),
        ('FoodMatch', [184, 196, 207, 217]),
    ]
    distance_cap = [
        ('OptLoad-S', [671, 718, 756, 790]),
        ('OptLoad-LU', [637, 680, 715, 747]),
        ('OptLoad-D', [588, 626, 658, 686]),
        ('Insertion', [619, 661, 695, 726]),
        ('LIFO', [607, 647, 680, 710]),
        ('FoodMatch', [625, 667, 701, 732]),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(16.5, 9.2))

    scatter_series(axes[0, 0], tw, served, 'Served Requests', 'Time Window')
    add_panel_caption(axes[0, 0], '(a) Served vs TW')

    scatter_series(axes[0, 1], tw, lu, 'LU Cost', 'Time Window')
    add_panel_caption(axes[0, 1], '(b) LU vs TW')

    scatter_series(axes[0, 2], tw, distance, 'Distance', 'Time Window')
    add_panel_caption(axes[0, 2], '(c) Distance vs TW')

    scatter_series(axes[1, 0], cap, served_cap, 'Served Requests', 'Capacity')
    add_panel_caption(axes[1, 0], '(d) Served vs Capacity')

    scatter_series(axes[1, 1], cap, lu_cap, 'LU Cost', 'Capacity')
    add_panel_caption(axes[1, 1], '(e) LU vs Capacity')

    scatter_series(axes[1, 2], cap, distance_cap, 'Distance', 'Capacity')
    add_panel_caption(axes[1, 2], '(f) Distance vs Capacity')

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc='upper center',
        bbox_to_anchor=(0.5, 0.995),
        ncol=4,
        frameon=False,
        fontsize=LEGEND_SIZE,
        markerscale=1.25,
        handlelength=2.1,
    )
    fig.tight_layout(rect=[0, 0.03, 1, 0.93], h_pad=1.8, w_pad=1.3)

    save_fig(fig, 'sensitivity_tw_capacity', step=6)


if __name__ == '__main__':
    figure6_parallel()
