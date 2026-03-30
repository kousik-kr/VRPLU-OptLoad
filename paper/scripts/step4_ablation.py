#!/usr/bin/env python3
"""Step 4: Ablation over small instances (N=2,5) as a 1x2 grouped-bar panel."""

import numpy as np
import matplotlib.pyplot as plt

from plot_utils import save_fig


SERIES_STYLE = {
    'OptLoad': {'color': '#4d4d4d', 'hatch': '//'},
    'OptLoad without LU-Pruning': {'color': '#777777', 'hatch': '\\\\'},
    'OptLoad without Clustering': {'color': '#9a9a9a', 'hatch': 'xx'},
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


def grouped_bars(ax, x_values, series, y_label):
    x_pos = np.arange(len(x_values))
    n_series = len(series)
    width = min(0.82 / max(n_series, 1), 0.22)
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
    ax.set_xlabel('N (requests)', fontsize=AXIS_LABEL_SIZE)
    ax.tick_params(axis='both', labelsize=TICK_LABEL_SIZE)


def figure4_ablation():
    print('\n[Step 4] Ablation: runtime and sequence-space (N=2,5)')

    n = [2, 5]

    runtime = [
        ('OptLoad', [820, 3550]),
        ('OptLoad without LU-Pruning', [1400, 6200]),
        ('OptLoad without Clustering', [3500, 18000]),
    ]
    sequences = [
        ('OptLoad', [2100, 9200]),
        ('OptLoad without LU-Pruning', [6400, 25800]),
        ('OptLoad without Clustering', [19800, 81400]),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.6))

    grouped_bars(axes[0], n, runtime, 'Average Runtime (ms)')
    add_panel_caption(axes[0], '(a) Runtime comparison by ablation variant')

    grouped_bars(axes[1], n, sequences, 'Average Sequences Explored')
    add_panel_caption(axes[1], '(b) Search-space size by ablation variant')

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc='upper center',
        bbox_to_anchor=(0.5, 0.985),
        ncol=3,
        frameon=False,
        fontsize=LEGEND_SIZE,
    )

    fig.tight_layout(rect=[0, 0.08, 1, 0.9], w_pad=1.2)
    save_fig(fig, 'ablation', step=4)


if __name__ == '__main__':
    figure4_ablation()
