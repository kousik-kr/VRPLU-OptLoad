#!/usr/bin/env python3
"""Generate the runtime-vs-categories plot matching the provided style."""

from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import numpy as np


def generate_plot(output_path: str, show: bool) -> None:
    """Create and save the comparison plot with matching visual style."""
    categories = np.array([2, 3, 4, 5, 6])

    # Values chosen to match the plotted curves from the reference figure.
    po_min_envy_gtp = np.array([0.8, 1.3, 2.0, 2.9, 4.1])
    brutforce = np.array([0.0, 0.0, 0.2, 1.8, 54.0])
    gnn = np.array([1.2, 2.6, 4.6, 6.8, 9.2])

    fig, ax = plt.subplots(figsize=(5.12, 4.11), dpi=100)
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    ax.plot(
        categories,
        po_min_envy_gtp,
        color="tab:blue",
        linewidth=1.5,
        label="PO-minEnvyGTP",
    )
    ax.plot(
        categories,
        brutforce,
        color="red",
        marker="o",
        markersize=6,
        linewidth=1.5,
        label="Brutforce",
    )
    ax.plot(
        categories,
        gnn,
        color="green",
        linestyle="--",
        linewidth=1.5,
        label="GNN",
    )

    # Use a darker border so axes are clearly visible in PDF output.
    for spine in ax.spines.values():
        spine.set_color("black")
        spine.set_linewidth(1.8)

    ax.set_xlabel("Number of categories", fontsize=20)
    ax.set_ylabel("Running time", fontsize=20)
    ax.set_xticks(categories)
    ax.set_yticks([0, 20, 40])
    ax.set_ylim(-2, 56)
    ax.tick_params(axis="both", labelsize=20)
    ax.grid(False)  
    legend = ax.legend(loc="upper left", fontsize=18, framealpha=0.9)

    fig.tight_layout()
    fig.savefig(output_path, dpi=100, transparent=True)

    if show:
        plt.show()
    else:
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the runtime-vs-categories comparison plot."
    )
    parser.add_argument(
        "--output",
        default="runtime_categories_plot.pdf",
        help="Output image path (default: runtime_categories_plot.pdf)",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not open a plot window after saving the figure.",
    )
    args = parser.parse_args()

    generate_plot(output_path=args.output, show=not args.no_show)


if __name__ == "__main__":
    main()