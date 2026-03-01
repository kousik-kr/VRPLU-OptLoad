#!/usr/bin/env python3
"""
Step 2: Scalability with Number of Requests
All data pre-computed and embedded — no CSV dependency.

Figures:
  fig2_scalability_requests — 2×2 grid (runtime, served, service ratio, Pareto)
  fig2b_feasibility         — feasibility rate line plot
"""

from plot_utils import *

# ───────────────────────────────────────────────────────────────────
# Embedded data — {solver: {n: (mean, lo, hi)}}
# ───────────────────────────────────────────────────────────────────
RUNTIME = {
    'OptLoad':   {5: (38.0141, 37.0429, 48.9853), 10: (40.6358, 38.3817, 50.8899), 15: (42.6718, 37.7104, 47.6332), 20: (40.5447, 38.377, 50.7124), 25: (40.9705, 37.3184, 45.6226), 30: (39.9656, 36.8969, 43.0343), 35: (47.5034, 45.1434, 54.8634), 40: (50.6868, 48.4925, 55.8811)},
    'Insertion': {5: (10.4104, 6.4695, 14.3513), 10: (13.4318, 11.7311, 15.1325), 15: (26.7604, 22.1771, 31.3437), 20: (48.381, 40.3186, 52.4434), 25: (61.3455, 55.0315, 65.6595), 30: (62.0114, 59.8766, 64.1462), 35: (68.4505, 64.5812, 72.3198), 40: (75.3896, 71.0092, 79.77)},
    'LIFO':      {5: (3.5774, 2.8427, 4.3121), 10: (10.3912, 8.2007, 12.5817), 15: (14.025, 12.286, 15.764), 20: (20.8848, 10.4367, 25.3329), 25: (23.5878, 19.6494, 27.5262), 30: (28.2731, 26.3502, 30.196), 35: (32.7977, 29.2524, 36.343), 40: (42.7307, 40.7928, 44.6686)},
    'FoodMatch': {5: (2.3253, 1.8094, 2.8412), 10: (3.43, 2.2661, 5.5939), 15: (7.8613, 5.7107, 10.0119), 20: (10.7316, 8.3792, 12.084), 25: (13.2505, 11.2342, 15.2668), 30: (16.5594, 13.5322, 19.5866), 35: (27.2792, 22.0663, 32.4921), 40: (32.5227, 30.4792, 40.5662)},
}

BEST_SERVED = {
    'OptLoad':   {5: (15.1, 11.7882, 18.4118), 10: (18.1, 13.5575, 22.6425), 15: (15.1, 11.1072, 25.3072), 20: (26.3, 23.1357, 29.4643), 25: (24.1, 21.4781, 26.7219), 30: (32.9, 29.9132, 35.8868), 35: (30.1, 27.9289, 32.2711), 40: (36.2, 32.1421, 40.2579)},
    'Insertion': {5: (6.1, 3.5663, 8.6337), 10: (14.4, 11.251, 17.549), 15: (11.3, 9.0618, 13.5382), 20: (14.1, 10.7882, 17.4118), 25: (14.1, 11.4781, 16.7219), 30: (12.9, 9.9132, 15.8868), 35: (10.1, 7.9289, 12.2711), 40: (17.1, 13.7371, 20.4629)},
    'LIFO':      {5: (9.8, 7.8395, 11.7605), 10: (14.1, 11.2897, 16.9103), 15: (15.0, 12.3662, 17.6338), 20: (13.7, 10.8978, 16.5022), 25: (15.3, 13.0618, 17.5382), 30: (15.7, 12.8575, 18.5425), 35: (16.0, 13.8145, 18.1855), 40: (17.0, 14.3022, 19.6978)},
    'FoodMatch': {5: (5.2, 3.2395, 7.1605), 10: (11.3, 8.3592, 14.2408), 15: (8.9, 5.4044, 12.3956), 20: (8.8, 5.534, 12.066), 25: (8.5, 6.9825, 10.0175), 30: (10.5, 8.4418, 12.5582), 35: (7.5, 5.874, 9.126), 40: (13.0, 10.5219, 15.4781)},
}


def figure2_scalability():
    print('\n[Figure 2] Step 2 — Scalability with Requests')

    solvers = ['OptLoad', 'Insertion', 'LIFO', 'FoodMatch']
    n_vals = [5, 10, 15, 20, 25, 30, 35, 40]

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))

    # (a) Runtime vs N (log scale)
    ax = axes[0]
    for s in solvers:
        ns = sorted(RUNTIME[s].keys())
        means = [RUNTIME[s][n][0] for n in ns]
        lows  = [RUNTIME[s][n][1] for n in ns]
        highs = [RUNTIME[s][n][2] for n in ns]
        ax.plot(ns, means, marker=MARKERS[s], color=COLORS[s], label=SOLVER_LABELS[s])
        ax.fill_between(ns, lows, highs, alpha=0.12, color=COLORS[s])
    ax.set_yscale('log')
    ax.set_xlabel('Number of Requests (N)')
    ax.set_ylabel('Runtime (ms, log)')
    ax.set_title('(a) Computation Time')
    ax.legend(fontsize=7.5)

    # (b) Best served
    ax = axes[1]
    for s in solvers:
        ns = sorted(BEST_SERVED[s].keys())
        means = [BEST_SERVED[s][n][0] for n in ns]
        lows  = [BEST_SERVED[s][n][1] for n in ns]
        highs = [BEST_SERVED[s][n][2] for n in ns]
        ax.plot(ns, means, marker=MARKERS[s], color=COLORS[s], label=SOLVER_LABELS[s])
        ax.fill_between(ns, lows, highs, alpha=0.12, color=COLORS[s])
    ax.set_xlabel('Number of Requests (N)')
    ax.set_ylabel('Best Requests Served')
    ax.set_title('(b) Solution Quality')

    fig.tight_layout(h_pad=2.0, w_pad=1.5)
    save_fig(fig, 'fig2_scalability_requests', step=2)

   

if __name__ == '__main__':
    figure2_scalability()
    print('\nStep 2 plots complete.')
