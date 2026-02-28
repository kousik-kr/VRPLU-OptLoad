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
    'OptLoad':   {5: (7.0141, 5.0429, 8.9853), 10: (0.6358, 0.3817, 0.8899), 15: (12.6718, 7.7104, 17.6332), 20: (0.5447, 0.377, 0.7124), 25: (13.9705, 12.3184, 15.6226), 30: (19.9656, 16.8969, 23.0343), 35: (17.5034, 15.1434, 19.8634), 40: (0.6868, 0.4925, 0.8811)},
    'Insertion': {5: (10.4104, 6.4695, 14.3513), 10: (3.4318, 1.7311, 5.1325), 15: (126.7604, 92.1771, 161.3437), 20: (8.381, 4.3186, 12.4434), 25: (210.3455, 165.0315, 255.6595), 30: (252.0114, 209.8766, 294.1462), 35: (218.4505, 174.5812, 262.3198), 40: (25.3896, 11.0092, 39.77)},
    'FoodMatch': {5: (2.3253, 1.8094, 2.8412), 10: (0.43, 0.2661, 0.5939), 15: (7.8613, 5.7107, 10.0119), 20: (0.7316, 0.3792, 1.084), 25: (13.2505, 11.2342, 15.2668), 30: (16.5594, 13.5322, 19.5866), 35: (17.2792, 12.0663, 22.4921), 40: (2.5227, 0.4792, 4.5662)},
    'LIFO':      {5: (3.5774, 2.8427, 4.3121), 10: (0.3912, 0.2007, 0.5817), 15: (14.025, 12.286, 15.764), 20: (0.8848, 0.4367, 1.3329), 25: (23.5878, 19.6494, 27.5262), 30: (28.2731, 26.3502, 30.196), 35: (32.7977, 29.2524, 36.343), 40: (2.7307, 0.7928, 4.6686)},
}

BEST_SERVED = {
    'OptLoad':   {5: (5.1, 1.7882, 8.4118), 10: (8.1, 3.5575, 12.6425), 15: (2.1, -1.1072, 5.3072), 20: (6.3, 3.1357, 9.4643), 25: (0.0, 0.0, 0.0), 30: (0.0, 0.0, 0.0), 35: (0.0, 0.0, 0.0), 40: (6.2, 2.1421, 10.2579)},
    'Insertion': {5: (6.1, 3.5663, 8.6337), 10: (14.4, 11.251, 17.549), 15: (11.3, 9.0618, 13.5382), 20: (14.1, 10.7882, 17.4118), 25: (14.1, 11.4781, 16.7219), 30: (12.9, 9.9132, 15.8868), 35: (10.1, 7.9289, 12.2711), 40: (17.1, 13.7371, 20.4629)},
    'FoodMatch': {5: (5.2, 3.2395, 7.1605), 10: (11.3, 8.3592, 14.2408), 15: (8.9, 5.4044, 12.3956), 20: (8.8, 5.534, 12.066), 25: (8.5, 6.9825, 10.0175), 30: (10.5, 8.4418, 12.5582), 35: (7.5, 5.874, 9.126), 40: (13.0, 10.5219, 15.4781)},
    'LIFO':      {5: (9.8, 7.8395, 11.7605), 10: (14.1, 11.2897, 16.9103), 15: (15.0, 12.3662, 17.6338), 20: (13.7, 10.8978, 16.5022), 25: (15.3, 13.0618, 17.5382), 30: (15.7, 12.8575, 18.5425), 35: (16.0, 13.8145, 18.1855), 40: (17.0, 14.3022, 19.6978)},
}

# {solver: {n: mean}}
SERVICE_RATIO = {
    'OptLoad':   {5: 1.02, 10: 0.81, 15: 0.14, 20: 0.315, 25: 0.0, 30: 0.0, 35: 0.0, 40: 0.155},
    'Insertion': {5: 1.22, 10: 1.44, 15: 0.7533, 20: 0.705, 25: 0.564, 30: 0.43, 35: 0.2886, 40: 0.4275},
    'FoodMatch': {5: 1.04, 10: 1.13, 15: 0.5933, 20: 0.44, 25: 0.34, 30: 0.35, 35: 0.2143, 40: 0.325},
    'LIFO':      {5: 1.96, 10: 1.41, 15: 1.0, 20: 0.685, 25: 0.612, 30: 0.5233, 35: 0.4571, 40: 0.425},
}

PARETO = {
    'OptLoad':   {5: 2.2, 10: 2.8, 15: 2.8, 20: 1.3, 25: 0.0, 30: 0.0, 35: 0.0, 40: 1.3},
    'Insertion': {5: 1.0, 10: 1.0, 15: 1.0, 20: 1.0, 25: 1.0, 30: 1.0, 35: 1.0, 40: 1.0},
    'FoodMatch': {5: 1.0, 10: 1.0, 15: 1.0, 20: 1.0, 25: 1.0, 30: 1.0, 35: 1.0, 40: 1.0},
    'LIFO':      {5: 1.0, 10: 1.0, 15: 1.0, 20: 1.0, 25: 1.0, 30: 1.0, 35: 1.0, 40: 1.0},
}

# {solver: {n: pct}}
FEASIBILITY = {
    'OptLoad':   {5: 70.0, 10: 70.0, 15: 20.0, 20: 70.0, 25: 0.0, 30: 0.0, 35: 0.0, 40: 60.0},
    'Insertion': {5: 100.0, 10: 100.0, 15: 100.0, 20: 100.0, 25: 100.0, 30: 100.0, 35: 100.0, 40: 100.0},
    'FoodMatch': {5: 100.0, 10: 100.0, 15: 100.0, 20: 100.0, 25: 100.0, 30: 100.0, 35: 100.0, 40: 100.0},
    'LIFO':      {5: 100.0, 10: 100.0, 15: 100.0, 20: 100.0, 25: 100.0, 30: 100.0, 35: 100.0, 40: 100.0},
}


def figure2_scalability():
    print('\n[Figure 2] Step 2 — Scalability with Requests')

    solvers = ['OptLoad', 'Insertion', 'FoodMatch', 'LIFO']
    n_vals = [5, 10, 15, 20, 25, 30, 35, 40]

    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.4))

    # (a) Runtime vs N (log scale)
    ax = axes[0, 0]
    for s in solvers:
        ns = sorted(RUNTIME[s].keys())
        means = [RUNTIME[s][n][0] for n in ns]
        lows  = [RUNTIME[s][n][1] for n in ns]
        highs = [RUNTIME[s][n][2] for n in ns]
        ax.plot(ns, means, marker=MARKERS[s], color=COLORS[s], label=SOLVER_LABELS[s])
        ax.fill_between(ns, lows, highs, alpha=0.12, color=COLORS[s])
    ax.set_yscale('log')
    ax.set_xlabel('Number of Requests (N)')
    ax.set_ylabel('Runtime (s)')
    ax.set_title('(a) Computation Time')
    ax.legend(fontsize=7.5)

    # (b) Best served
    ax = axes[0, 1]
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

    # (c) Service ratio
    ax = axes[1, 0]
    for s in solvers:
        ns = sorted(SERVICE_RATIO[s].keys())
        vals = [SERVICE_RATIO[s][n] for n in ns]
        ax.plot(ns, vals, marker=MARKERS[s], color=COLORS[s], label=SOLVER_LABELS[s])
    ax.set_xlabel('Number of Requests (N)')
    ax.set_ylabel('Service Ratio (served / N)')
    ax.set_title('(c) Normalised Service Rate')
    ax.set_ylim(-0.05, 1.05)

    # (d) Pareto size
    ax = axes[1, 1]
    for s in solvers:
        ns = sorted(PARETO[s].keys())
        vals = [PARETO[s][n] for n in ns]
        ax.plot(ns, vals, marker=MARKERS[s], color=COLORS[s], label=SOLVER_LABELS[s])
    ax.set_xlabel('Number of Requests (N)')
    ax.set_ylabel('Pareto Set Size')
    ax.set_title('(d) Trade-off Diversity')

    fig.tight_layout(h_pad=2.0, w_pad=1.5)
    save_fig(fig, 'fig2_scalability_requests', step=2)

    # ---- Feasibility rate ----
    fig2, ax2 = plt.subplots(figsize=(3.5, 2.6))
    for s in solvers:
        ns = sorted(FEASIBILITY[s].keys())
        rates = [FEASIBILITY[s][n] for n in ns]
        ax2.plot(ns, rates, marker=MARKERS[s], color=COLORS[s], label=SOLVER_LABELS[s])
    ax2.set_xlabel('Number of Requests (N)')
    ax2.set_ylabel('Feasibility Rate (%)')
    ax2.set_title('Queries with Feasible Solutions')
    ax2.set_ylim(-5, 105)
    ax2.legend(fontsize=7)
    fig2.tight_layout()
    save_fig(fig2, 'fig2b_feasibility', step=2)


if __name__ == '__main__':
    figure2_scalability()
    print('\nStep 2 plots complete.')
