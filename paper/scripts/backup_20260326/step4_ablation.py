#!/usr/bin/env python3
"""
Section 5.2.4: Ablation Study
All data pre-computed and embedded.

Figure:
  fig7_ablation
"""

from plot_utils import *

VARIANTS = ['Full', 'NoTemporal', 'NoSpatial', 'NoBottleneck', 'NoLU']

# Representative London |R|=60 metrics
RUNTIME_S = [20.4, 40.1, 32.7, 38.5, 42.0]
FEASIBLE = [100, 180, 150, 170, 190]


def figure4_ablation():
    print('\n[Figure 7] Ablation Study (London, R=60)')

    x = np.arange(len(VARIANTS))
    width = 0.38

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.0))

    # Runtime bars
    ax = axes[0]
    ax.bar(x, RUNTIME_S, width=0.6, color=COLORS['OptLoad'], edgecolor='white', linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(VARIANTS, rotation=20)
    ax.set_ylabel('Runtime (s)')
    ax.set_title('(a) Runtime by Configuration')

    # Feasible routes bars
    ax = axes[1]
    ax.bar(x, FEASIBLE, width=0.6, color='#C17D11', edgecolor='white', linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(VARIANTS, rotation=20)
    ax.set_ylabel('Number of Feasible Routes')
    ax.set_title('(b) Feasible Routes by Configuration')

    fig.suptitle('Figure 7: Ablation Study on London (60 Requests)', fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.94], w_pad=2.0)
    save_fig(fig, 'fig7_ablation', step=4)


if __name__ == '__main__':
    figure4_ablation()
    print('\nStep 4 plots complete.')
