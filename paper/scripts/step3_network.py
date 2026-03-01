#!/usr/bin/env python3
"""
Step 3: Network Scalability
All data pre-computed and embedded — no CSV dependency.

Figures:
  fig3_network_scalability — 1×3 grouped bars (runtime, served, Pareto)
"""

from plot_utils import *

# ───────────────────────────────────────────────────────────────────
# Embedded data — {solver: {network: (mean, err)}}
# ───────────────────────────────────────────────────────────────────
RUNTIME = {
    'OptLoad':   {'oldenburg': (41.4399, 25.0363), 'california': (52.0463, 37.3813), 'london': (60.5285, 39.1758)},
    'Insertion': {'oldenburg': (56.3996, 49.765),  'california': (65.2239, 80.0252), 'london': (79.8886, 104.8276)},
    'LIFO':      {'oldenburg': (32.539, 44.0276),  'california': (42.2268, 60.0422), 'london': (53.8689, 54.4154)},
    'FoodMatch': {'oldenburg': (21.3717, 4.0536), 'california': (32.2378, 50.0534), 'london': (35.7575, 60.3897)},
}

SERVED = {
    'OptLoad':   {'oldenburg': (31.1, 2.4884),  'california': (34.5456, 0.5465), 'london': (36.3, 3.1643)},
    'Insertion': {'oldenburg': (13.8, 2.7767), 'california': (13.05464,1.0), 'london': (14.1, 3.3118)},
    'LIFO':      {'oldenburg': (20.4, 1.8532), 'california': (21.9, 1.3677), 'london': (23.7, 2.8022)},
    'FoodMatch': {'oldenburg': (10.6, 1.5527),  'california': (10.9, 1.3677), 'london': (9.8, 3.266)},
}

def figure3_network():
    print('\n[Figure 3] Step 3 — Network Scalability')

    networks = ['oldenburg', 'california', 'london']
    net_labels = {
        'oldenburg':  'OL',
        'california': 'CAL',
        'london':     'London',
    }
    solvers = ['OptLoad', 'Insertion', 'LIFO', 'FoodMatch']

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))

    datasets = [
        (axes[0], RUNTIME,  'Runtime (s)',          '(a) Computation Time'),
        (axes[1], SERVED,   'Best Requests Served', '(b) Solution Quality'),
    ]

    x = np.arange(len(networks))
    w = 0.18

    for ax, data, ylabel, title in datasets:
        for i, s in enumerate(solvers):
            vals = [data[s][net][0] for net in networks]
            ax.bar(x + i * w, vals, w,
                   color=COLORS[s], label=SOLVER_LABELS[s] if ax is axes[0] else None,
                   edgecolor='white', linewidth=0.5)
        ax.set_xticks(x + 1.5 * w)
        ax.set_xticklabels([net_labels[n] for n in networks], fontsize=8)
        ax.set_ylabel(ylabel)
        ax.set_title(title)

    axes[0].legend(fontsize=7, ncol=2, loc='upper left')
    fig.tight_layout(w_pad=1.0)
    save_fig(fig, 'fig3_network_scalability', step=3)


if __name__ == '__main__':
    figure3_network()
    print('\nStep 3 plots complete.')
