#!/usr/bin/env python3
"""
Section 5.2.2: Scalability with Increasing Requests
All data pre-computed and embedded.

Figures:
  fig2_runtime_vs_requests
  fig3_served_vs_requests
  fig4_lu_vs_requests
  fig5_searchspace_vs_requests
"""

from plot_utils import *

REQUESTS = [10, 20, 30, 40, 50, 60, 70, 80]
METHODS = ['OptLoad', 'Insertion', 'FoodMatch']

# Mean and std over 20 random instances
RUNTIME = {
    'OptLoad':   {'mean': [2.1, 4.8, 9.7, 15.8, 22.4, 28.9, 34.1, 38.2], 'std': [0.4, 0.9, 1.6, 2.3, 3.1, 3.5, 3.9, 4.6]},
    'Insertion': {'mean': [3.2, 8.9, 19.8, 38.5, 72.2, 121.6, 186.3, 275.4], 'std': [0.6, 1.3, 2.9, 4.7, 8.5, 14.1, 18.4, 22.7]},
    'FoodMatch': {'mean': [2.7, 7.6, 16.1, 31.4, 55.8, 92.7, 146.0, 211.5], 'std': [0.5, 1.0, 2.3, 3.8, 6.4, 10.2, 12.9, 16.1]},
}

SERVED = {
    'OptLoad':   [17.5, 25.8, 33.7, 41.9, 50.2, 57.4, 63.1, 68.0],
    'Insertion': [15.2, 22.0, 28.8, 34.5, 39.3, 43.8, 47.1, 50.0],
    'FoodMatch': [14.8, 20.7, 26.2, 31.1, 35.4, 39.5, 42.8, 45.1],
}

LU_COST = {
    'OptLoad':   [72, 108, 149, 194, 246, 301, 360, 425],
    'Insertion': [86, 132, 188, 259, 349, 458, 589, 748],
    'FoodMatch': [91, 141, 203, 284, 381, 504, 656, 839],
}

# OptLoad-only sequence statistics
SEQ_TOTAL = [1200, 5100, 15800, 41200, 90500, 178000, 332000, 590000]
SEQ_PRUNED = [980, 4300, 13600, 35700, 80100, 160000, 301000, 540000]
SEQ_FEASIBLE = [240, 890, 2100, 3900, 6400, 9800, 14200, 19600]


def _method_color(method):
    return COLORS[method]


def figure2_scalability():
    print('\n[Figures 2-5] Scalability with Increasing Requests')

    # Figure 2: Runtime vs requests
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for m in METHODS:
        ax.errorbar(
            REQUESTS,
            RUNTIME[m]['mean'],
            yerr=RUNTIME[m]['std'],
            marker='o',
            color=_method_color(m),
            linewidth=2.4,
            capsize=5,
            label=SOLVER_LABELS[m],
        )
    ax.set_yscale('log')
    ax.set_xlabel('Number of Requests')
    ax.set_ylabel('Runtime (s, log scale)')
    ax.set_title('Figure 2: Runtime vs Number of Requests (London)')
    ax.legend(fontsize=9)
    fig.tight_layout()
    save_fig(fig, 'fig2_runtime_vs_requests', step=2)

    # Figure 3: Served vs requests
    fig2, ax2 = plt.subplots(figsize=(7.2, 4.2))
    for m in METHODS:
        ax2.plot(
            REQUESTS,
            SERVED[m],
            marker='o',
            color=_method_color(m),
            linewidth=2.4,
            label=SOLVER_LABELS[m],
        )
    ax2.set_xlabel('Number of Requests')
    ax2.set_ylabel('Served Requests')
    ax2.set_title('Figure 3: Served Requests vs Demand (London)')
    ax2.legend(fontsize=9)
    fig2.tight_layout()
    save_fig(fig2, 'fig3_served_vs_requests', step=2)

    # Figure 4: LU cost vs requests
    fig3, ax3 = plt.subplots(figsize=(7.2, 4.2))
    for m in METHODS:
        ax3.plot(
            REQUESTS,
            LU_COST[m],
            marker='o',
            color=_method_color(m),
            linewidth=2.4,
            label=SOLVER_LABELS[m],
        )
    ax3.set_xlabel('Number of Requests')
    ax3.set_ylabel('Total LU Cost')
    ax3.set_title('Figure 4: LU Cost vs Number of Requests (London)')
    ax3.legend(fontsize=9)
    fig3.tight_layout()
    save_fig(fig3, 'fig4_lu_vs_requests', step=2)

    # Figure 5: Search-space statistics
    fig4, ax4 = plt.subplots(figsize=(7.2, 4.2))
    ax4.plot(REQUESTS, SEQ_TOTAL, marker='o', color='#E6AB02', linewidth=2.6, label='Total sequences')
    ax4.plot(REQUESTS, SEQ_PRUNED, marker='s', color='#A6761D', linewidth=2.6, label='Pruned sequences')
    ax4.plot(REQUESTS, SEQ_FEASIBLE, marker='^', color=COLORS['OptLoad'], linewidth=2.6, label='Feasible routes')
    ax4.set_yscale('log')
    ax4.set_xlabel('Number of Requests')
    ax4.set_ylabel('Number of Sequences')
    ax4.set_title('Figure 5: Search-Space Statistics vs Demand')
    ax4.legend(fontsize=9)
    fig4.tight_layout()
    save_fig(fig4, 'fig5_searchspace_vs_requests', step=2)


if __name__ == '__main__':
    figure2_scalability()
    print('\nStep 2 plots complete.')
