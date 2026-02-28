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
    'OptLoad':   {'oldenburg': (0.4399, 0.0363), 'california': (2.0463, 0.3813), 'london': (0.5285, 0.1758)},
    'Insertion': {'oldenburg': (3.3996, 0.765),  'california': (0.2239, 0.0252), 'london': (9.8886, 4.8276)},
    'FoodMatch': {'oldenburg': (0.3717, 0.0536), 'california': (0.2378, 0.0534), 'london': (0.7575, 0.3897)},
    'LIFO':      {'oldenburg': (0.539, 0.0276),  'california': (0.2268, 0.0422), 'london': (0.8689, 0.4154)},
}

SERVED = {
    'OptLoad':   {'oldenburg': (1.1, 2.4884),  'california': (0.0, 0.0), 'london': (6.3, 3.1643)},
    'Insertion': {'oldenburg': (13.8, 2.7767), 'california': (0.0, 0.0), 'london': (14.1, 3.3118)},
    'FoodMatch': {'oldenburg': (7.6, 1.5527),  'california': (0.9, 1.3677), 'london': (8.8, 3.266)},
    'LIFO':      {'oldenburg': (20.4, 1.8532), 'california': (0.9, 1.3677), 'london': (13.7, 2.8022)},
}

PARETO = {
    'OptLoad':   {'oldenburg': (0.1, 0.2262),  'california': (0.0, 0.0), 'london': (1.3, 0.5889)},
    'Insertion': {'oldenburg': (1.0, 0.0),      'california': (0.0, 0.0), 'london': (1.0, 0.0)},
    'FoodMatch': {'oldenburg': (1.0, 0.0),      'california': (0.2, 0.3016), 'london': (1.0, 0.0)},
    'LIFO':      {'oldenburg': (1.0, 0.0),      'california': (1.0, 0.0), 'london': (1.0, 0.0)},
}


def figure3_network():
    print('\n[Figure 3] Step 3 — Network Scalability')

    networks = ['oldenburg', 'california', 'london']
    net_labels = {
        'oldenburg':  'Oldenburg\n(6 105)',
        'california': 'California\n(21 048)',
        'london':     'London\n(285 050)',
    }
    solvers = ['OptLoad', 'Insertion', 'FoodMatch', 'LIFO']

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.8))

    datasets = [
        (axes[0], RUNTIME,  'Runtime (s)',          '(a) Computation Time'),
        (axes[1], SERVED,   'Best Requests Served', '(b) Solution Quality'),
        (axes[2], PARETO,   'Pareto Set Size',      '(c) Trade-off Diversity'),
    ]

    x = np.arange(len(networks))
    w = 0.18

    for ax, data, ylabel, title in datasets:
        for i, s in enumerate(solvers):
            vals = [data[s][net][0] for net in networks]
            errs = [data[s][net][1] for net in networks]
            ax.bar(x + i * w, vals, w, yerr=errs, capsize=2,
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
