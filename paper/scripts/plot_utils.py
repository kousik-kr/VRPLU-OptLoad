#!/usr/bin/env python3
"""Shared plotting helpers for the 22-panel experimental figure set."""

import warnings
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'serif'],
    'font.size': 10,
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 8,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'axes.grid': True,
    'grid.alpha': 0.25,
    'grid.linestyle': '--',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'lines.linewidth': 1.8,
    'lines.markersize': 5,
})

COLORS = {
    'Exact': '#000000',
    'OptLoad-S': '#1f77b4',
    'OptLoad-LU': '#2ca02c',
    'OptLoad-D': '#ff7f0e',
    'OptLoad': '#1f77b4',
    'Insertion': '#9467bd',
    'LIFO': '#e377c2',
    'FoodMatch': '#8c564b',
    'NoLU': '#d62728',
    'NoCluster': '#17becf',
}

MARKERS = {
    'Exact': 's',
    'OptLoad-S': 'o',
    'OptLoad-LU': '^',
    'OptLoad-D': 'D',
    'OptLoad': 'o',
    'Insertion': 'v',
    'LIFO': 'P',
    'FoodMatch': 'X',
    'NoLU': '^',
    'NoCluster': 'D',
}

SCRIPT_DIR = Path(__file__).parent
PAPER_DIR = SCRIPT_DIR.parent
FIGURES_DIR = PAPER_DIR / 'figures'

STEP_DIRS = {
    1: FIGURES_DIR / 'step1_correctness',
    2: FIGURES_DIR / 'step2_scalability',
    3: FIGURES_DIR / 'step3_network',
    4: FIGURES_DIR / 'step4_ablation',
    5: FIGURES_DIR / 'step5_search_space',
    6: FIGURES_DIR / 'step6_parallel',
    7: FIGURES_DIR / 'step7_sensitivity',
}
for out in STEP_DIRS.values():
    out.mkdir(parents=True, exist_ok=True)


def save_fig(fig, name, step):
    out_dir = STEP_DIRS[step]
    fig.savefig(out_dir / f'{name}.pdf')
    fig.savefig(out_dir / f'{name}.png')
    plt.close(fig)
    print(f'Saved {out_dir.relative_to(PAPER_DIR)}/{name}.pdf / .png')


def plot_series(ax, x, series, y_label, x_label):
    for label, y in series:
        ax.plot(
            x,
            y,
            label=label,
            color=COLORS.get(label, '#333333'),
            marker=MARKERS.get(label, 'o'),
        )
    ax.set_ylabel(y_label)
    ax.set_xlabel(x_label)


def add_bottom_caption(ax, text):
    ax.text(
        0.5,
        -0.33,
        text,
        transform=ax.transAxes,
        ha='center',
        va='top',
        fontsize=9,
    )
