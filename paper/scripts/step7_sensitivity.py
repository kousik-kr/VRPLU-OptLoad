#!/usr/bin/env python3
"""
Step 7: Sensitivity Analysis
All data pre-computed and embedded — no CSV dependency.

Figures:
  fig7_sensitivity        — 2×2 (capacity→quality/runtime, TW→quality/runtime)
  fig7b_pareto_sensitivity — 1×2 Pareto diversity vs capacity & TW
"""

from plot_utils import *

# ───────────────────────────────────────────────────────────────────
# Embedded data — {param_value: (mean, lo, hi)}
# ───────────────────────────────────────────────────────────────────
CAP_SERVED  = {6: (0.0, 0.0, 0.0), 8: (0.0, 0.0, 0.0), 10: (0.6, -0.7573, 1.9573), 12: (0.6, -0.7573, 1.9573)}
CAP_RUNTIME = {6: (9.762, 8.492, 11.032), 8: (11.3561, 9.4513, 13.2609), 10: (10.6959, 8.5625, 12.8293), 12: (12.4484, 10.5934, 14.3034)}
CAP_PARETO  = {6: (0.2, -0.1016, 0.5016), 8: (0.1, -0.1262, 0.3262), 10: (0.2, -0.2524, 0.6524), 12: (0.5, -0.408, 1.408)}

TW_SERVED   = {30: (0.0, 0.0, 0.0), 60: (1.1, -1.3884, 3.5884), 90: (0.5, -0.6311, 1.6311), 120: (4.0, 0.4955, 7.5045)}
TW_RUNTIME  = {30: (11.6434, 10.4285, 12.8583), 60: (14.6026, 10.8539, 18.3513), 90: (13.3251, 11.3654, 15.2848), 120: (13.1501, 9.6189, 16.6813)}
TW_PARETO   = {30: (0.2, -0.1016, 0.5016), 60: (0.9, -0.8987, 2.6987), 90: (0.3, -0.1828, 0.7828), 120: (1.0, 0.3256, 1.6744)}


def figure7_sensitivity():
    print('\n[Figure 7] Step 7 — Sensitivity Analysis')

    cap_vals = sorted(CAP_SERVED.keys())
    tw_vals  = sorted(TW_SERVED.keys())

    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.0))

    # (a) Served vs Capacity
    ax = axes[0, 0]
    means = [CAP_SERVED[c][0] for c in cap_vals]
    lows  = [CAP_SERVED[c][1] for c in cap_vals]
    highs = [CAP_SERVED[c][2] for c in cap_vals]
    ax.bar(range(len(cap_vals)), means,
           yerr=[np.array(means)-np.array(lows), np.array(highs)-np.array(means)],
           capsize=3, color=COLORS['OptLoad'], alpha=0.8, edgecolor='white')
    ax.set_xticks(range(len(cap_vals)))
    ax.set_xticklabels([f'C={c}' for c in cap_vals])
    ax.set_ylabel('Best Requests Served')
    ax.set_title('(a) Capacity → Quality')

    # (b) Runtime vs Capacity
    ax = axes[0, 1]
    means = [CAP_RUNTIME[c][0] for c in cap_vals]
    lows  = [CAP_RUNTIME[c][1] for c in cap_vals]
    highs = [CAP_RUNTIME[c][2] for c in cap_vals]
    ax.bar(range(len(cap_vals)), means,
           yerr=[np.array(means)-np.array(lows), np.array(highs)-np.array(means)],
           capsize=3, color=COLORS['OptLoad'], alpha=0.8, edgecolor='white')
    ax.set_xticks(range(len(cap_vals)))
    ax.set_xticklabels([f'C={c}' for c in cap_vals])
    ax.set_ylabel('Runtime (s)')
    ax.set_title('(b) Capacity → Runtime')

    # (c) Served vs Time Window
    ax = axes[1, 0]
    means = [TW_SERVED[tw][0] for tw in tw_vals]
    lows  = [TW_SERVED[tw][1] for tw in tw_vals]
    highs = [TW_SERVED[tw][2] for tw in tw_vals]
    ax.bar(range(len(tw_vals)), means,
           yerr=[np.array(means)-np.array(lows), np.array(highs)-np.array(means)],
           capsize=3, color=COLORS['Exact'], alpha=0.8, edgecolor='white')
    ax.set_xticks(range(len(tw_vals)))
    ax.set_xticklabels([f'TW={tw}' for tw in tw_vals])
    ax.set_ylabel('Best Requests Served')
    ax.set_title('(c) Time Window → Quality')

    # (d) Runtime vs Time Window
    ax = axes[1, 1]
    means = [TW_RUNTIME[tw][0] for tw in tw_vals]
    lows  = [TW_RUNTIME[tw][1] for tw in tw_vals]
    highs = [TW_RUNTIME[tw][2] for tw in tw_vals]
    ax.bar(range(len(tw_vals)), means,
           yerr=[np.array(means)-np.array(lows), np.array(highs)-np.array(means)],
           capsize=3, color=COLORS['Exact'], alpha=0.8, edgecolor='white')
    ax.set_xticks(range(len(tw_vals)))
    ax.set_xticklabels([f'TW={tw}' for tw in tw_vals])
    ax.set_ylabel('Runtime (s)')
    ax.set_title('(d) Time Window → Runtime')

    fig.tight_layout(h_pad=2.0, w_pad=2.0)
    save_fig(fig, 'fig7_sensitivity', step=7)

    # ---- Pareto diversity ----
    fig2, axes2 = plt.subplots(1, 2, figsize=(7.2, 2.6))

    ax = axes2[0]
    means = [CAP_PARETO[c][0] for c in cap_vals]
    ax.bar(range(len(cap_vals)), means, color=COLORS['OptLoad'], alpha=0.8, edgecolor='white')
    ax.set_xticks(range(len(cap_vals)))
    ax.set_xticklabels([f'C={c}' for c in cap_vals])
    ax.set_ylabel('Avg Pareto Set Size')
    ax.set_title('(a) Capacity → Pareto Diversity')

    ax = axes2[1]
    means = [TW_PARETO[tw][0] for tw in tw_vals]
    ax.bar(range(len(tw_vals)), means, color=COLORS['Exact'], alpha=0.8, edgecolor='white')
    ax.set_xticks(range(len(tw_vals)))
    ax.set_xticklabels([f'TW={tw}' for tw in tw_vals])
    ax.set_ylabel('Avg Pareto Set Size')
    ax.set_title('(b) Time Window → Pareto Diversity')

    fig2.tight_layout(w_pad=2.0)
    save_fig(fig2, 'fig7b_pareto_sensitivity', step=7)


if __name__ == '__main__':
    figure7_sensitivity()
    print('\nStep 7 plots complete.')
