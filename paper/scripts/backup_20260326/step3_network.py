#!/usr/bin/env python3
"""
Section 5.2.3: Scalability with Network Size
All data pre-computed and embedded.

Figure:
  fig6_runtime_vs_network
"""

from plot_utils import *

NETWORKS = ['Oldenburg', 'California', 'London']
METHODS = ['OptLoad', 'Insertion', 'FoodMatch']

# Runtime at fixed |R|=20 (mean over 20 instances)
RUNTIME = {
    'OptLoad':   [1.1, 2.9, 5.6],
    'Insertion': [2.5, 6.8, 15.7],
    'FoodMatch': [3.2, 7.4, 16.8],
}


def figure3_network():
    print('\n[Figure 6] Runtime vs Network Size (R=20)')

    x = np.arange(len(NETWORKS))
    width = 0.25

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for i, m in enumerate(METHODS):
        ax.bar(
            x + i * width,
            RUNTIME[m],
            width,
            label=SOLVER_LABELS[m],
            color=COLORS[m],
            edgecolor='white',
            linewidth=0.6,
        )

    ax.set_xticks(x + width)
    ax.set_xticklabels(NETWORKS)
    ax.set_xlabel('Road Network')
    ax.set_ylabel('Runtime (s)')
    ax.set_title('Figure 6: Runtime on Different Networks (|R|=20)')
    ax.legend(fontsize=9)

    fig.tight_layout()
    save_fig(fig, 'fig6_runtime_vs_network', step=3)


if __name__ == '__main__':
    figure3_network()
    print('\nStep 3 plots complete.')
