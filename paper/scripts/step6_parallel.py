#!/usr/bin/env python3
"""
Step 6: Parallel Performance
All data pre-computed and embedded — no CSV dependency.

Figures:
  fig6_parallel — 1×2 (runtime vs threads, speedup with ideal-linear)
"""

from plot_utils import *

# ───────────────────────────────────────────────────────────────────
# Embedded data — {threads: mean_runtime_ms}
# ───────────────────────────────────────────────────────────────────
RUNTIME_MS = {1: 485.7, 2: 491.7, 4: 479.0, 8: 487.0, 16: 494.8, 24: 478.5}


def figure6_parallel():
    print('\n[Figure 6] Step 6 — Parallel Performance')

    thread_vals = sorted(RUNTIME_MS.keys())
    t1_rt = RUNTIME_MS[1]

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))

    # (a) Runtime vs Threads
    ax = axes[0]
    rts = [RUNTIME_MS[t] / 1000.0 for t in thread_vals]
    ax.plot(thread_vals, rts, 'o-', color=COLORS['OptLoad'], linewidth=2)
    ax.set_xlabel('Number of Threads')
    ax.set_ylabel('Runtime (s)')
    ax.set_title('(a) Runtime vs. Threads')
    ax.set_xticks(thread_vals)

    # (b) Speedup
    ax = axes[1]
    speedups = [t1_rt / RUNTIME_MS[t] for t in thread_vals]
    ax.plot(thread_vals, speedups, 'o-', color=COLORS['OptLoad'],
            linewidth=2, label='Measured')
    ax.plot(thread_vals, thread_vals, '--', color='gray', alpha=0.5,
            label='Ideal Linear')
    ax.set_xlabel('Number of Threads')
    ax.set_ylabel('Speedup (T₁ / Tₚ)')
    ax.set_title('(b) Parallel Speedup')
    ax.set_xticks(thread_vals)
    ax.legend(fontsize=8)

    fig.tight_layout(w_pad=2.0)
    save_fig(fig, 'fig6_parallel', step=6)


if __name__ == '__main__':
    figure6_parallel()
    print('\nStep 6 plots complete.')
