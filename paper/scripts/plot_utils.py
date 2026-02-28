#!/usr/bin/env python3
"""
Shared plotting utilities for VRPLU-OptLoad publication figures.
Style, colors, markers, labels, and save helper.
No data-loading — each step script embeds its own pre-computed data.
"""

import warnings
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
from pathlib import Path

warnings.filterwarnings('ignore')

# ───────────────────────────────────────────────────────────────────
# Global style — publication quality
# ───────────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'serif'],
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 8.5,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'lines.linewidth': 1.5,
    'lines.markersize': 6,
})

# ───────────────────────────────────────────────────────────────────
# Color palette — consistent across all figures
# ───────────────────────────────────────────────────────────────────
COLORS = {
    'OptLoad':     '#2166AC',
    'Exact':       '#1B9E77',
    'Insertion':   '#D95F02',
    'LIFO':        '#E7298A',
    'FoodMatch':   '#7570B3',
    'NoCluster':   '#E6AB02',
    'NoLUPruning': '#A6761D',
}

MARKERS = {
    'OptLoad': 'o', 'Exact': 's', 'Insertion': '^',
    'LIFO': 'D', 'FoodMatch': 'v',
    'NoCluster': 'P', 'NoLUPruning': 'X',
}

SOLVER_LABELS = {
    'OptLoad': 'OptLoad',
    'Exact': 'Exact',
    'Insertion': 'Insertion',
    'LIFO': 'LIFO',
    'FoodMatch': 'FoodMatch',
    'NoCluster': 'No Clustering',
    'NoLUPruning': 'No LU Pruning',
}

# ───────────────────────────────────────────────────────────────────
# Paths
# ───────────────────────────────────────────────────────────────────
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
    'summary': FIGURES_DIR / 'summary',
}
for d in STEP_DIRS.values():
    d.mkdir(parents=True, exist_ok=True)


def save_fig(fig, name, step=None):
    """Save as both PDF (vector) and PNG into the step directory."""
    out_dir = STEP_DIRS.get(step, FIGURES_DIR)
    fig.savefig(out_dir / f'{name}.pdf')
    fig.savefig(out_dir / f'{name}.png')
    plt.close(fig)
    print(f'  Saved {out_dir.relative_to(PAPER_DIR)}/{name}.pdf / .png')
