#!/usr/bin/env python3
"""Step 2 runtime-only comparison for request and network scalability."""

import numpy as np
import matplotlib.pyplot as plt

from plot_utils import save_fig


FONT_SIZE = 17
TICK_SIZE = 17
LEGEND_SIZE = 17
CAPTION_SIZE = 17
MARKER_SIZE = 120

SERIES_STYLE = {
    'OptLoad': {'color': '#2b2b2b', 'marker': 'o', 'linestyle': '-'},
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


def figure2_scalability_runtime():
    print('\n[Step 2 Runtime] Scalability runtime comparison: requests and networks')

    n_requests = [10, 20, 30, 40, 50]
    req_runtime = [
        ('OptLoad',   [0.45, 0.95, 2.40, 4.60, 7.80]),
        ('Insertion', [0.50, 1.30, 3.50, 6.80, 11.50]),
        ('LIFO',      [0.20, 0.40, 1.10, 2.10, 3.60]),
        ('FoodMatch', [0.13, 0.22, 0.70, 1.30, 2.30]),
    ]

    networks = ['Oldenburg', 'California', 'London']
    x_net = np.arange(len(networks))
    net_runtime = [
        ('OptLoad',   [2.4, 3.6, 5.2]),
        ('Insertion', [3.5, 5.0, 7.2]),
        ('LIFO',      [1.1, 1.8, 2.6]),
        ('FoodMatch', [0.7, 1.2, 1.9]),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.8))

    scatter_series(
        axes[0],
        n_requests,
        req_runtime,
        'Runtime (s)',
        'N (requests)',
    )
    add_panel_caption(axes[0], '(a) Runtime vs number of requests')

    scatter_series(
        axes[1],
        x_net,
        net_runtime,
        'Runtime (s)',
        'Network',
    )
    axes[1].set_xticks(x_net)
    axes[1].set_xticklabels(networks)
    add_panel_caption(axes[1], '(b) Runtime vs network scale')

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc='upper center',
        bbox_to_anchor=(0.5, 0.985),
        ncol=4,
        frameon=False,
        fontsize=LEGEND_SIZE,
        markerscale=1.25,
        handlelength=2.1,
    )
    fig.tight_layout(rect=[0, 0.08, 1, 0.9], w_pad=1.5)

    save_fig(fig, 'scalability_runtime', step=2)


if __name__ == '__main__':
    figure2_scalability_runtime()
