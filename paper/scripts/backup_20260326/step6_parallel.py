#!/usr/bin/env python3
"""
Section 5.2.5: Parallel Scalability
All data pre-computed and embedded.

Figure:
  fig8_speedup
"""

from plot_utils import *

THREADS = [1, 2, 4, 8, 16, 24]
TIMES_S = [20.0, 10.2, 5.1, 2.6, 1.4, 0.9]


def figure6_parallel():
    print('\n[Figure 8] Parallel Speedup (London, R=60)')

    speedup = [TIMES_S[0] / t for t in TIMES_S]

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.plot(THREADS, speedup, marker='o', color=COLORS['OptLoad'], linewidth=2.6, label='Observed speedup')
    ax.plot(THREADS, THREADS, linestyle='--', color='gray', linewidth=1.8, label='Ideal linear')
    ax.set_xlabel('Number of Threads')
    ax.set_ylabel('Speedup')
    ax.set_xticks(THREADS)
    ax.set_title('Figure 8: Parallel Speedup of OptLoad')
    ax.legend(fontsize=9)
    fig.tight_layout()
    save_fig(fig, 'fig8_speedup', step=6)


if __name__ == '__main__':
    figure6_parallel()
    print('\nStep 6 plots complete.')
