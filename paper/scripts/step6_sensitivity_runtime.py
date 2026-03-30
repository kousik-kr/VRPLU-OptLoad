#!/usr/bin/env python3
"""Step 6 runtime-only comparison for time-window and capacity sensitivity."""

import matplotlib.pyplot as plt

from plot_utils import save_fig


FONT_SIZE = 17
TICK_SIZE = 17
LEGEND_SIZE = 17
CAPTION_SIZE = 17
MARKER_SIZE = 100

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


def figure6_sensitivity_runtime():
    print('\n[Step 6 Runtime] Runtime comparison: Time Window and Capacity sensitivity')

    tw = [40, 60, 80, 100]
    cap = [6, 8, 10, 12]

    runtime_tw = [
        ('OptLoad', [273, 329, 381, 431]),
        ('Insertion', [85, 97, 108, 119]),
        ('LIFO', [78, 89, 99, 109]),
        ('FoodMatch', [89, 102, 114, 126]),
    ]
    runtime_cap = [
        ('OptLoad', [322, 381, 433, 482]),
        ('Insertion', [91, 104, 116, 127]),
        ('LIFO', [83, 95, 106, 116]),
        ('FoodMatch', [95, 109, 121, 133]),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.6))

    scatter_series(axes[0], tw, runtime_tw, 'Runtime (s)', 'Time Window Duration')
    add_panel_caption(axes[0], '(a) Runtime vs Time Window')

    scatter_series(axes[1], cap, runtime_cap, 'Runtime (s)', 'Vehicle Capacity')
    add_panel_caption(axes[1], '(b) Runtime vs Capacity')

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

    save_fig(fig, 'runtime_comparison_tw_capacity', step=6)


if __name__ == '__main__':
    figure6_sensitivity_runtime()
