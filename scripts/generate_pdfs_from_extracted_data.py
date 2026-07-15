#!/usr/bin/env python3
"""Generate PDF plots from extracted JSON data files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt

from plot_pipeline_config import DATA_DIR, PDF_DIR, PLOT_JOBS, image_stem, pdf_stem


LABEL_FONT_SIZE = 22
TICK_FONT_SIZE = 20
LEGEND_FONT_SIZE = 18
LINE_WIDTH = 1.5
MARKER_SIZE = 6
FIGURE_WIDTH_INCH = 6.0
FIGURE_HEIGHT_INCH = 4.8
AXES_RECT = [0.20, 0.17, 0.76, 0.78]
#Y_TOP_PADDING_RATIO = 0.08


def load_payload(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


# def padded_y_limits(payload: dict) -> tuple[float, float]:
#     """Increase y-axis top limit so all plots have extra headroom."""
#     y_min, y_max_cfg = payload["y_limits"]
#     y_min = float(y_min)
#     y_max_cfg = float(y_max_cfg)

#     series_max = max(float(max(series["y"])) for series in payload["series"] if series["y"])
#     base_max = max(y_max_cfg, series_max)

#     span = max(base_max - y_min, 1e-9)
#     y_max = base_max + span * Y_TOP_PADDING_RATIO
#     return y_min, y_max


def plot_from_payload(payload: dict, output_path: Path) -> None:
    """Create one PDF using extracted data and stored style metadata."""
    fig = plt.figure(figsize=(FIGURE_WIDTH_INCH, FIGURE_HEIGHT_INCH), dpi=100)
    ax = fig.add_axes(AXES_RECT)
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    x_values = payload["x_values"]
    for series in payload["series"]:
        if series["kind"] == "scatter":
            ax.scatter(
                x_values,
                series["y"],
                c=series["color"],
                s=MARKER_SIZE**2,
                marker=series["marker"],
                label=series["name"],
                zorder=3,
            )
            continue

        line_kwargs = {
            "color": series["color"],
            "linestyle": series["linestyle"],
            "linewidth": LINE_WIDTH,
            "label": series["name"],
        }
        if series["marker"] is not None:
            line_kwargs["marker"] = series["marker"]
            line_kwargs["markersize"] = MARKER_SIZE

        ax.plot(
            x_values,
            series["y"],
            **line_kwargs,
        )

    ax.set_xlabel(payload["x_label"], fontsize=LABEL_FONT_SIZE)
    ax.set_ylabel(payload["y_label"], fontsize=LABEL_FONT_SIZE)
    ax.set_xticks(payload["x_values"])
    ax.set_yticks(payload["y_ticks"])
    #y_min, y_max = padded_y_limits(payload)
    #ax.set_ylim((y_min, y_max))
    ax.tick_params(axis="both", labelsize=TICK_FONT_SIZE)

    x_values = payload["x_values"]
    x_span = max(x_values) - min(x_values)
    x_pad = x_span * 0.04 if x_span > 0 else 0.5
    ax.set_xlim(min(x_values) - x_pad, max(x_values) + x_pad)

    for spine in ax.spines.values():
        spine.set_color("black")
        spine.set_linewidth(1.8)

    ax.legend(
        loc=payload.get("legend_loc", "best"),
        fontsize=LEGEND_FONT_SIZE,
        framealpha=0.9,
    )
    ax.grid(False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="pdf", dpi=100, transparent=True)
    plt.close(fig)


def generate_all_pdfs(data_dir: Path, output_dir: Path, image_name: str | None = None) -> None:
    """Generate PDFs for one image or all configured images."""
    jobs = [job for job in PLOT_JOBS if image_name is None or job.image_name == image_name]
    if not jobs:
        raise ValueError(f"No configured image matched: {image_name}")

    total = len(jobs)
    for index, job in enumerate(jobs, start=1):
        data_path = data_dir / f"{image_stem(job.image_name)}.json"
        if not data_path.exists():
            raise FileNotFoundError(f"Missing extracted data file: {data_path}")

        payload = load_payload(data_path)
        output_path = output_dir / f"{pdf_stem(job.image_name)}.pdf"

        print(f"[{index}/{total}] Generating PDF for {job.image_name}")
        plot_from_payload(payload, output_path)
        print(f"  -> wrote {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate PDF plots from extracted JSON data files."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR,
        help=f"Input folder with JSON data files (default: {DATA_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PDF_DIR,
        help=f"Output folder for generated PDFs (default: {PDF_DIR})",
    )
    parser.add_argument(
        "--image-name",
        default=None,
        help="Generate only one image by exact filename.",
    )
    args = parser.parse_args()

    generate_all_pdfs(data_dir=args.data_dir, output_dir=args.output_dir, image_name=args.image_name)


if __name__ == "__main__":
    main()
