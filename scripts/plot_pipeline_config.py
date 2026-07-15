#!/usr/bin/env python3
"""Shared configuration for rebuilding plots from images in New folder."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class PlotJob:
    image_name: str
    plot_family: str
    x_values: tuple[float, ...]
    x_label: str
    y_label: str
    y_limits: tuple[float, float]
    y_ticks: tuple[float, ...]
    worst_label: str = "Worst"
    legend_loc: str = "best"


REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = REPO_ROOT / "New folder"
DATA_DIR = INPUT_DIR / "extracted_data"
PDF_DIR = INPUT_DIR / "regenerated_pdf"

CATEGORY_X = (2.0, 3.0, 4.0, 5.0, 6.0)
AGENT_X = (5.0, 10.0, 15.0, 20.0, 25.0, 30.0)

COPY_SUFFIX_PATTERN = re.compile(r"\s*\(\d+\)$")


def image_stem(image_name: str) -> str:
    return Path(image_name).stem


def pdf_stem(image_name: str) -> str:
    """Normalize image stem for PDF output filenames."""
    return COPY_SUFFIX_PATTERN.sub("", image_stem(image_name)).strip()


PLOT_JOBS: tuple[PlotJob, ...] = (
    PlotJob(
        image_name="POF_agentsfixed (1).png",
        plot_family="fairness",
        x_values=CATEGORY_X,
        x_label="Number of categories",
        y_label="Price of Fairness",
        y_limits=(1.10, 1.85),
        y_ticks=(1.2, 1.4, 1.6, 1.8),
        worst_label="Worst",
        legend_loc="upper right",
    ),
    PlotJob(
        image_name="POF_clustersfixed (1).png",
        plot_family="fairness",
        x_values=AGENT_X,
        x_label="Number of agents",
        y_label="Price of Fairness",
        y_limits=(1.15, 1.83),
        y_ticks=(1.2, 1.4, 1.6, 1.8),
        worst_label="Worst POF",
        legend_loc="center left",
    ),
    PlotJob(
        image_name="RUNTIME_AGENT_FIXED (1).png",
        plot_family="runtime",
        x_values=CATEGORY_X,
        x_label="Number of categories",
        y_label="Running time",
        y_limits=(-2.0, 55.0),
        y_ticks=(0.0, 20.0, 40.0),
        legend_loc="upper left",
    ),
    PlotJob(
        image_name="RUNTIME_CLUSTER_FIXED (1).png",
        plot_family="runtime",
        x_values=AGENT_X,
        x_label="Number of agents",
        y_label="Running time",
        y_limits=(0.0, 70.0),
        y_ticks=(20.0, 40.0, 60.0),
        legend_loc="upper left",
    ),
    PlotJob(
        image_name="pof_agent_fixed_OL_min_max_distance (1).png",
        plot_family="fairness",
        x_values=CATEGORY_X,
        x_label="Number of categories",
        y_label="Price of Fairness",
        y_limits=(1.02, 1.35),
        y_ticks=(1.1, 1.2, 1.3),
        worst_label="Worst",
        legend_loc="center right",
    ),
    PlotJob(
        image_name="pof_agent_fixed_OL_prop (1).png",
        plot_family="fairness",
        x_values=CATEGORY_X,
        x_label="Number of categories",
        y_label="Price of Fairness",
        y_limits=(1.12, 1.58),
        y_ticks=(1.2, 1.3, 1.4, 1.5),
        worst_label="Worst",
        legend_loc="center left",
    ),
    PlotJob(
        image_name="pof_agent_fixed_tg (1).png",
        plot_family="fairness",
        x_values=CATEGORY_X,
        x_label="Number of categories",
        y_label="Price of Fairness",
        y_limits=(1.15, 1.86),
        y_ticks=(1.2, 1.4, 1.6, 1.8),
        worst_label="Worst",
        legend_loc="upper right",
    ),
    PlotJob(
        image_name="pof_agent_fixed_tg_minmax (1).png",
        plot_family="fairness",
        x_values=CATEGORY_X,
        x_label="Number of categories",
        y_label="Price of Fairness",
        y_limits=(1.02, 1.35),
        y_ticks=(1.1, 1.2, 1.3),
        worst_label="Worst",
        legend_loc="center right",
    ),
    PlotJob(
        image_name="pof_agent_fixed_tg_prop (1).png",
        plot_family="fairness",
        x_values=CATEGORY_X,
        x_label="Number of categories",
        y_label="Price of Fairness",
        y_limits=(1.06, 1.80),
        y_ticks=(1.2, 1.4, 1.6, 1.8),
        worst_label="Worst",
        legend_loc="center right",
    ),
    PlotJob(
        image_name="pof_category_fixed_ol_minmax (1).png",
        plot_family="fairness",
        x_values=AGENT_X,
        x_label="Number of Agents",
        y_label="Price of Fairness",
        y_limits=(1.02, 1.41),
        y_ticks=(1.1, 1.2, 1.3, 1.4),
        worst_label="Worst",
        legend_loc="center left",
    ),
    PlotJob(
        image_name="pof_category_fixed_ol_prop (1).png",
        plot_family="fairness",
        x_values=AGENT_X,
        x_label="Number of Agents",
        y_label="Price of Fairness",
        y_limits=(1.20, 2.20),
        y_ticks=(1.2, 1.4, 1.6, 1.8, 2.0, 2.2),
        worst_label="Worst",
        legend_loc="center right",
    ),
    PlotJob(
        image_name="pof_category_fixed_tg (1).png",
        plot_family="fairness",
        x_values=AGENT_X,
        x_label="Number of agents",
        y_label="Price of Fairness",
        y_limits=(1.20, 2.55),
        y_ticks=(1.5, 2.0, 2.5),
        worst_label="Worst POF",
        legend_loc="center right",
    ),
    PlotJob(
        image_name="pof_category_fixed_tg_minmax (1).png",
        plot_family="fairness",
        x_values=AGENT_X,
        x_label="Number of agents",
        y_label="Price of Fairness",
        y_limits=(1.02, 1.68),
        y_ticks=(1.2, 1.4, 1.6),
        worst_label="Worst POF",
        legend_loc="upper center",
    ),
    PlotJob(
        image_name="pof_category_fixed_tg_prop (1).png",
        plot_family="fairness",
        x_values=AGENT_X,
        x_label="Number of agents",
        y_label="Price of Fairness",
        y_limits=(1.20, 2.32),
        y_ticks=(1.25, 1.5, 1.75, 2.0, 2.25),
        worst_label="Worst POF",
        legend_loc="center right",
    ),
    PlotJob(
        image_name="runtime_agent_fixed_tg (2).png",
        plot_family="runtime",
        x_values=CATEGORY_X,
        x_label="Number of categories",
        y_label="Running time",
        y_limits=(-3.0, 52.0),
        y_ticks=(0.0, 10.0, 20.0, 30.0, 40.0, 50.0),
        legend_loc="upper left",
    ),
    PlotJob(
        image_name="runtime_category_fixed_tg (1).png",
        plot_family="runtime",
        x_values=AGENT_X,
        x_label="Number of agents",
        y_label="Running time",
        y_limits=(0.0, 205.0),
        y_ticks=(50.0, 100.0, 150.0, 200.0),
        legend_loc="upper left",
    ),
)
