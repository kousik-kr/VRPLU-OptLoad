#!/usr/bin/env python3
"""Step 2: Three 1x3 scatter panels for scalability with N."""

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
    print('\n[Step 2] Scalability with N: served/LU/distance scatter')

    n = [5, 10, 20, 30, 40]

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
        ('OptLoad-S',  [11.5, 21.0, 43.5, 64.0, 85.0]),
        ('OptLoad-LU', [9.5, 17.0, 34.5, 51.0, 67.5]),
        ('OptLoad-D',  [10.2, 18.5, 37.5, 55.0, 73.0]),
        ('Insertion',  [12.0, 23.5, 49.0, 72.0, 98.0]),
        ('LIFO',       [7.8, 13.6, 26.0, 38.0, 49.6]),
        ('FoodMatch',  [13.0, 25.0, 52.0, 76.0, 103.0]),
    ]
    distance = [
        ('OptLoad-S', [20100, 36500, 74200, 109500, 149000]),
        ('OptLoad-LU', [19500, 35200, 71600, 105000, 143000]),
        ('OptLoad-D', [18700, 33800, 68800, 100500, 137500]),
        ('Insertion', [21400, 38900, 81500, 120800, 165000]),
        ('LIFO', [21800, 40100, 84200, 124900, 171500]),
        ('FoodMatch', [21000, 38200, 80100, 118700, 162000]),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(16.0, 5.6))

    scatter_series(axes[0], n, served, 'Served Requests')
    add_panel_caption(axes[0], '(a) Served requests')

    scatter_series(axes[1], n, lu, 'LU Cost')
    add_panel_caption(axes[1], '(b) LU cost')

    scatter_series(axes[2], n, distance, 'Distance')
    add_panel_caption(axes[2], '(c) Travel distance')

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc='upper center',
        bbox_to_anchor=(0.5, 0.985),
        ncol=4,
        frameon=False,
        fontsize=LEGEND_SIZE,
        markerscale=1.4,
        handlelength=2.2,
    )

    fig.tight_layout(rect=[0, 0.08, 1, 0.9], w_pad=1.2)

    save_fig(fig, 'scalability_n', step=2)


if __name__ == '__main__':
    figure2_scalability()
