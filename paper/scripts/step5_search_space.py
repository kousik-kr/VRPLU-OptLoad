#!/usr/bin/env python3
"""
Step 5: Search Space Reduction Analysis
All data pre-computed and embedded - no CSV dependency.

Figures:
  fig5_search_space - 1x3 (clusters, search effort, ordering complexity)
  fig5b_pruning     - pruning rate + LU bound tightness
"""

from plot_utils import *

# Embedded data - {n: value} or {n: (mean, lo, hi)}
CLUSTERS = {
    5: (5.2, 4.7476, 5.6524), 10: (6.6, 5.7603, 7.4397),
    15: (13.5, 12.227, 14.773), 20: (10.6, 9.0844, 12.1156),
    25: (21.7, 20.2281, 23.1719), 30: (24.8, 23.2255, 26.3745),
    35: (29.8, 28.0871, 31.5129), 40: (19.5, 17.2316, 21.7684),
}

PREFIXES_EXPLORED = {5: 15.8, 10: 16.9, 15: 24.8, 20: 8.2, 25: 22.1, 30: 26.0, 35: 20.5, 40: 13.9}
BACKTRACK_CALLS = {5: 16.0, 10: 17.2, 15: 25.1, 20: 8.2, 25: 22.3, 30: 26.1, 35: 20.7, 40: 13.9}

CLUSTER_ORDERINGS = {5: 6.5, 10: 6.8, 15: 10.2, 20: 3.0, 25: 10.3, 30: 11.6, 35: 9.4, 40: 5.3}
CROSS_PRODUCT = {5: 2.8, 10: 4.5, 15: 6.8, 20: 1.5, 25: 0.0, 30: 0.0, 35: 0.0, 40: 4.0}
VALID_ORDERINGS = {5: 2.6, 10: 4.5, 15: 6.8, 20: 1.5, 25: 0.0, 30: 0.0, 35: 0.0, 40: 4.0}

PRUNE_PCT = {5: 1.25, 10: 1.7442, 15: 1.1952, 20: 0.0, 25: 0.8969, 30: 0.3831, 35: 0.9662, 40: 0.0}
SEED_LB_RATIO = {5: 2.3667, 10: 5.3797, 15: 5.1601, 20: 9.7886, 25: 7.5772, 30: 7.8011, 35: 9.297, 40: 19.3849}


def figure5_search_space():
    print('\n[Figure 5] Step 5 - Search Space Reduction')

    n_vals = [5, 10, 15, 20, 25, 30, 35, 40]

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.8))

    # (a) Clusters vs N
    ax = axes[0]
    means = [CLUSTERS[n][0] for n in n_vals]
    lows = [CLUSTERS[n][1] for n in n_vals]
    highs = [CLUSTERS[n][2] for n in n_vals]
    ax.plot(n_vals, means, 'o-', color=COLORS['OptLoad'], linewidth=2)
    ax.fill_between(n_vals, lows, highs, alpha=0.15, color=COLORS['OptLoad'])
    ax.plot(
        n_vals,
        [2 * n for n in n_vals],
        's--',
        color='gray',
        alpha=0.5,
        label='2N (no clustering)',
        markersize=4,
    )
    ax.set_xlabel('Number of Requests (N)')
    ax.set_ylabel('Average Number of Clusters')
    ax.set_title('(a) Clustering Effectiveness')
    ax.legend(fontsize=7)

    # (b) Search effort
    ax = axes[1]
    ax.plot(
        n_vals,
        [PREFIXES_EXPLORED[n] for n in n_vals],
        marker='o',
        color=COLORS['OptLoad'],
        label='Prefixes Explored',
        linestyle='-',
    )
    ax.plot(
        n_vals,
        [BACKTRACK_CALLS[n] for n in n_vals],
        marker='s',
        color=COLORS['OptLoad'],
        label='Backtrack Calls',
        linestyle='--',
    )
    ax.set_xlabel('Number of Requests (N)')
    ax.set_ylabel('Average Count')
    ax.set_title('(b) Search Effort vs. N')
    ax.legend(fontsize=7)

    # (c) Ordering complexity
    ax = axes[2]
    ax.plot(
        n_vals,
        [CLUSTER_ORDERINGS[n] for n in n_vals],
        marker='o',
        color=COLORS['OptLoad'],
        label='Cluster Orderings',
    )
    ax.plot(
        n_vals,
        [CROSS_PRODUCT[n] for n in n_vals],
        marker='s',
        color=COLORS['Insertion'],
        label='Cross Product',
    )
    ax.plot(
        n_vals,
        [VALID_ORDERINGS[n] for n in n_vals],
        marker='^',
        color=COLORS['Exact'],
        label='Valid Orderings',
    )
    ax.set_xlabel('Number of Requests (N)')
    ax.set_ylabel('Average Count')
    ax.set_title('(c) Ordering Complexity')
    ax.legend(fontsize=7)

    fig.tight_layout(w_pad=1.5)
    save_fig(fig, 'fig5_search_space', step=5)

    # Pruning rate
    fig2, ax2 = plt.subplots(figsize=(3.5, 2.6))
    ax2_twin = ax2.twinx()
    ax2.bar(
        n_vals,
        [PRUNE_PCT[n] for n in n_vals],
        width=2.5,
        alpha=0.6,
        color=COLORS['OptLoad'],
        label='Pruning Rate (%)',
    )
    ax2_twin.plot(
        n_vals,
        [SEED_LB_RATIO[n] for n in n_vals],
        'D-',
        color=COLORS['Insertion'],
        label='Seed LU / LB LU',
    )
    ax2.set_xlabel('Number of Requests (N)')
    ax2.set_ylabel('Average Pruning Rate (%)')
    ax2_twin.set_ylabel('Average LU Bound Tightness')
    ax2_twin.axvline(x=n_vals[-1] + 1.5, color='black', linewidth=0.8)
    ax2_twin.spines['right'].set_visible(True)
    ax2_twin.spines['right'].set_linewidth(1.2)
    ax2_twin.spines['right'].set_color('black')
    ax2_twin.tick_params(axis='y', direction='out', length=5)
    ax2.set_title('Search Space Reduction Metrics')
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc='upper left')
    fig2.tight_layout()
    save_fig(fig2, 'fig5b_pruning', step=5)


if __name__ == '__main__':
    figure5_search_space()
    print('\nStep 5 plots complete.')
