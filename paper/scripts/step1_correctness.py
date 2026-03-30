#!/usr/bin/env python3
"""Step 1: Three 1x3 bar panels for small instances (N=2,5)."""

import numpy as np
import matplotlib.pyplot as plt

from plot_utils import save_fig


SERIES_STYLE = {
    'Exact': {'color': '#111111', 'hatch': ''},
    'OptLoad': {'color': '#4d4d4d', 'hatch': '//'},
    'OptLoad-S': {'color': '#4d4d4d', 'hatch': '//'},
    'OptLoad-LU': {'color': '#777777', 'hatch': '\\\\'},
    'OptLoad-D': {'color': '#9a9a9a', 'hatch': 'xx'},
    'Insertion': {'color': '#b8b8b8', 'hatch': '..'},
    'LIFO': {'color': '#d3d3d3', 'hatch': '++'},
    'FoodMatch': {'color': '#efefef', 'hatch': '--'},
}

AXIS_LABEL_SIZE = 17
TICK_LABEL_SIZE = 17
LEGEND_SIZE = 17
CAPTION_SIZE = 17


def add_panel_caption(ax, text):
    ax.text(
        0.5,
        -0.23,
        text,
        transform=ax.transAxes,
        ha='center',
        va='top',
        fontsize=CAPTION_SIZE,
    )



def grouped_bars(ax, x_values, series, y_label, x_label, log_scale=False):
    """Draw grouped bars where each series appears for each x-value."""
    x_pos = np.arange(len(x_values))
    n_series = len(series)
    width = min(0.82 / max(n_series, 1), 0.16)
    start = -0.5 * (n_series - 1) * width

    for idx, (label, values) in enumerate(series):
        offset = start + idx * width
        style = SERIES_STYLE.get(label, {'color': '#777777', 'hatch': ''})
        ax.bar(
            x_pos + offset,
            values,
            width=width,
            label=label,
            color=style['color'],
            hatch=style['hatch'],
            edgecolor='black',
            linewidth=0.8,
        )

    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_values)
    ax.set_ylabel(y_label, fontsize=AXIS_LABEL_SIZE)
    ax.set_xlabel(x_label, fontsize=AXIS_LABEL_SIZE)
    ax.tick_params(axis='both', labelsize=TICK_LABEL_SIZE)
    if log_scale:
        ax.set_yscale('log')


def figure1_correctness():
    print('\n[Step 1] Small instances: served/LU/distance bars (N=2,5)')

    n = [2, 5]

    served = [
        ('Exact',       [5.0, 11.5]),
        ('OptLoad-S',   [4.8, 11.0]),
        ('OptLoad-LU',  [3.2, 6.1]),
        ('OptLoad-D',   [3.3, 6.3]),
        ('Insertion',   [3.8, 7.8]),
        ('LIFO',        [2.1, 6.4]),
        ('FoodMatch',   [2.2, 5.2]),
    ]
    lu = [
        ('Exact',       [2.2, 6.4]),   # low served → minimal LU
        ('OptLoad-S',   [10.8, 25.0]), 
        ('OptLoad-LU',  [6.6, 12.4]),  # ≈ 2×served → optimal
        ('OptLoad-D',   [7.2, 13.5]),
        ('Insertion',   [12.5, 28.0]),
        ('LIFO',        [4.2, 12.8]),  # exact 2×served
        ('FoodMatch',   [13.8, 24.0]),
    ]
    distance = [
        ('Exact', [7202.692, 18071.82]),
        ('OptLoad-S', [7900.0, 20850.0]),
        ('OptLoad-LU', [7800.0, 20300.0]),
        ('OptLoad-D', [7300.0, 18950.0]),
        ('Insertion', [15050.187, 29658.418]),
        ('LIFO', [19159.441, 33053.286]),
        ('FoodMatch', [14460.042, 22929.452]),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(16.0, 5.6))

    grouped_bars(axes[0], n, served, 'Served Requests', 'N (requests)')
    add_panel_caption(axes[0], '(a) Served requests comparison')

    grouped_bars(axes[1], n, lu, 'LU Cost', 'N (requests)')
    add_panel_caption(axes[1], '(b) LU cost comparison')

    grouped_bars(axes[2], n, distance, 'Distance', 'N (requests)')
    add_panel_caption(axes[2], '(c) Travel distance comparison')

    # One shared legend for the three panels.
    full_handles, full_labels = axes[0].get_legend_handles_labels()
    fig.legend(
        full_handles,
        full_labels,
        loc='upper center',
        bbox_to_anchor=(0.5, 0.985),
        ncol=4,
        frameon=False,
        fontsize=LEGEND_SIZE,
    )

    fig.tight_layout(rect=[0, 0.08, 1, 0.9], w_pad=1.2)

    save_fig(fig, 'small_instances', step=1)


if __name__ == '__main__':
    figure1_correctness()
