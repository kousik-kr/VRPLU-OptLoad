#!/usr/bin/env python3
"""Extract numeric plot data from every image in New folder.

This script processes images one by one, digitizes the visible series, and stores
the extracted data as JSON files for vector-quality PDF regeneration.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage

from plot_pipeline_config import DATA_DIR, INPUT_DIR, PLOT_JOBS, PlotJob


BLUE_TARGET = np.array([31.0 / 255.0, 119.0 / 255.0, 180.0 / 255.0], dtype=np.float32)
RED_TARGET = np.array([1.0, 0.0, 0.0], dtype=np.float32)
GREEN_TARGET = np.array([0.0, 0.5, 0.0], dtype=np.float32)


def load_rgb(image_path: Path) -> np.ndarray:
    """Load image and normalize to float RGB in [0, 1]."""
    image = plt.imread(image_path)
    if image.ndim == 2:
        image = np.stack([image, image, image], axis=-1)
    rgb = image[:, :, :3].astype(np.float32)
    if float(rgb.max()) > 1.0:
        rgb /= 255.0
    return np.clip(rgb, 0.0, 1.0)


def detect_frame_bounds(rgb: np.ndarray) -> tuple[int, int, int, int]:
    """Detect plot frame bounds: (left, right, top, bottom)."""
    height, width, _ = rgb.shape
    black = rgb.mean(axis=2) < 0.2

    rows = np.array([], dtype=np.int64)
    cols = np.array([], dtype=np.int64)

    for row_ratio in (0.50, 0.45, 0.40, 0.35):
        rows = np.where(black.sum(axis=1) > width * row_ratio)[0]
        if rows.size >= 2:
            break

    for col_ratio in (0.45, 0.40, 0.35, 0.30):
        cols = np.where(black.sum(axis=0) > height * col_ratio)[0]
        if cols.size >= 2:
            break

    if rows.size < 2 or cols.size < 2:
        raise RuntimeError("Could not detect chart frame bounds from image.")

    top = int(rows.min())
    bottom = int(rows.max())
    left = int(cols.min())
    right = int(cols.max())
    return left, right, top, bottom


def interior_mask(shape: tuple[int, int], frame: tuple[int, int, int, int]) -> np.ndarray:
    """Create a boolean mask for the chart interior."""
    left, right, top, bottom = frame
    mask = np.zeros(shape, dtype=bool)
    mask[max(0, top + 2) : max(0, bottom - 1), max(0, left + 2) : max(0, right - 1)] = True
    return mask


def color_mask(
    rgb: np.ndarray,
    target: np.ndarray,
    threshold: float,
    frame: tuple[int, int, int, int],
) -> np.ndarray:
    """Build a mask for pixels near the target color within chart interior."""
    mask = np.linalg.norm(rgb - target, axis=2) < threshold
    return mask & interior_mask(mask.shape, frame)


def find_marker_components(red_mask: np.ndarray) -> list[tuple[float, float, int]]:
    """Find connected marker components from red series mask."""
    best_components: list[tuple[float, float, int]] = []

    for erosion_iterations in (2, 1, 0):
        if erosion_iterations > 0:
            working = ndimage.binary_erosion(red_mask, iterations=erosion_iterations)
        else:
            working = red_mask

        labels, count = ndimage.label(working)
        if count == 0:
            continue

        components: list[tuple[float, float, int]] = []
        for comp_id, component_slice in enumerate(ndimage.find_objects(labels), start=1):
            if component_slice is None:
                continue

            component_mask = labels[component_slice] == comp_id
            area = int(component_mask.sum())
            if area < 6:
                continue

            ys, xs = np.where(component_mask)
            center_x = float(xs.mean() + component_slice[1].start)
            center_y = float(ys.mean() + component_slice[0].start)
            components.append((center_x, center_y, area))

        if len(components) > len(best_components):
            best_components = components

    return sorted(best_components, key=lambda item: item[0])


def choose_evenly_spaced_markers(
    components: list[tuple[float, float, int]],
    expected_count: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Choose marker centers that best match evenly spaced x positions."""
    if len(components) < expected_count:
        raise RuntimeError(
            f"Not enough marker components. Expected {expected_count}, found {len(components)}."
        )

    if len(components) > 12:
        components = sorted(components, key=lambda item: item[2], reverse=True)[:12]
        components = sorted(components, key=lambda item: item[0])

    if len(components) == expected_count:
        xs = np.array([item[0] for item in components], dtype=np.float64)
        ys = np.array([item[1] for item in components], dtype=np.float64)
        return xs, ys

    x_values = np.array([item[0] for item in components], dtype=np.float64)
    best_score: float | None = None
    best_idx: tuple[int, ...] | None = None

    index_axis = np.arange(expected_count, dtype=np.float64)

    for combo in itertools.combinations(range(len(components)), expected_count):
        selected_x = x_values[list(combo)]
        slope, intercept = np.polyfit(index_axis, selected_x, 1)
        predicted_x = slope * index_axis + intercept
        residual = float(np.mean((selected_x - predicted_x) ** 2))
        span = float(selected_x[-1] - selected_x[0])
        score = residual - 0.01 * span

        if best_score is None or score < best_score:
            best_score = score
            best_idx = combo

    if best_idx is None:
        raise RuntimeError("Could not choose marker components for x positions.")

    chosen = [components[i] for i in best_idx]
    chosen = sorted(chosen, key=lambda item: item[0])
    xs = np.array([item[0] for item in chosen], dtype=np.float64)
    ys = np.array([item[1] for item in chosen], dtype=np.float64)
    return xs, ys


def extract_line_y_values(
    series_mask: np.ndarray,
    x_positions_px: np.ndarray,
    frame: tuple[int, int, int, int],
) -> np.ndarray:
    """Extract line y-values at each x using bottom-most matching pixels."""
    _, _, top, bottom = frame
    ys, xs = np.where(series_mask)
    if ys.size == 0:
        raise RuntimeError("No pixels found for line color mask.")

    y_values: list[float] = []
    for x_pos in x_positions_px:
        y_px = np.nan
        for window in (2, 4, 6, 8, 12, 16, 20):
            candidates = ys[np.abs(xs - x_pos) <= window]
            candidates = candidates[(candidates >= top + 1) & (candidates <= bottom - 1)]
            if candidates.size > 0:
                y_px = float(candidates.max())
                break

        if np.isnan(y_px):
            raise RuntimeError(f"Could not sample line y-value around x={x_pos:.2f}.")

        y_values.append(y_px)

    return np.array(y_values, dtype=np.float64)


def pixel_to_data_y(
    y_pixels: np.ndarray,
    frame: tuple[int, int, int, int],
    y_limits: tuple[float, float],
) -> np.ndarray:
    """Map pixel-space y coordinates to configured data-space y values."""
    _, _, top, bottom = frame
    y_min, y_max = y_limits
    return y_min + (bottom - y_pixels) / (bottom - top) * (y_max - y_min)


def build_series_payload(job: PlotJob, y_blue: np.ndarray, y_red: np.ndarray, y_green: np.ndarray | None) -> list[dict]:
    """Create series section for output JSON."""
    if job.plot_family == "runtime":
        if y_green is None:
            raise RuntimeError("Runtime plot requires green series values.")
        return [
            {
                "name": "PO-minEnvyGTP",
                "kind": "line",
                "color": "#1f77b4",
                "linestyle": "-",
                "marker": None,
                "linewidth": 1.5,
                "markersize": None,
                "y": np.round(y_blue, 6).tolist(),
            },
            {
                "name": "Brutforce",
                "kind": "line",
                "color": "#ff0000",
                "linestyle": "-",
                "marker": "o",
                "linewidth": 1.5,
                "markersize": 6.0,
                "y": np.round(y_red, 6).tolist(),
            },
            {
                "name": "GNN",
                "kind": "line",
                "color": "#008000",
                "linestyle": "--",
                "marker": None,
                "linewidth": 1.5,
                "markersize": None,
                "y": np.round(y_green, 6).tolist(),
            },
        ]

    return [
        {
            "name": "Average",
            "kind": "line",
            "color": "#1f77b4",
            "linestyle": "-",
            "marker": None,
            "linewidth": 1.5,
            "markersize": None,
            "y": np.round(y_blue, 6).tolist(),
        },
        {
            "name": job.worst_label,
            "kind": "scatter",
            "color": "#ff0000",
            "linestyle": "None",
            "marker": "o",
            "linewidth": 0.0,
            "markersize": 6.0,
            "y": np.round(y_red, 6).tolist(),
        },
    ]


def extract_data_for_job(job: PlotJob, input_dir: Path, data_dir: Path) -> Path:
    """Extract one image and write one JSON file."""
    image_path = input_dir / job.image_name
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    rgb = load_rgb(image_path)
    frame = detect_frame_bounds(rgb)
    left, right, top, bottom = frame

    red_mask = color_mask(rgb, RED_TARGET, threshold=0.45, frame=frame)
    components = find_marker_components(red_mask)
    x_pixels, red_y_pixels = choose_evenly_spaced_markers(components, expected_count=len(job.x_values))

    blue_mask = color_mask(rgb, BLUE_TARGET, threshold=0.23, frame=frame)
    blue_y_pixels = extract_line_y_values(blue_mask, x_pixels, frame)

    green_y_pixels: np.ndarray | None = None
    if job.plot_family == "runtime":
        green_mask = color_mask(rgb, GREEN_TARGET, threshold=0.30, frame=frame)
        green_y_pixels = extract_line_y_values(green_mask, x_pixels, frame)

    red_y_data = pixel_to_data_y(red_y_pixels, frame, job.y_limits)
    blue_y_data = pixel_to_data_y(blue_y_pixels, frame, job.y_limits)
    green_y_data = pixel_to_data_y(green_y_pixels, frame, job.y_limits) if green_y_pixels is not None else None

    payload = {
        "image_name": job.image_name,
        "plot_family": job.plot_family,
        "x_values": list(job.x_values),
        "x_label": job.x_label,
        "y_label": job.y_label,
        "y_limits": list(job.y_limits),
        "y_ticks": list(job.y_ticks),
        "legend_loc": job.legend_loc,
        "figure_size_px": [int(rgb.shape[1]), int(rgb.shape[0])],
        "frame_px": {
            "left": left,
            "right": right,
            "top": top,
            "bottom": bottom,
        },
        "x_positions_px": np.round(x_pixels, 3).tolist(),
        "series": build_series_payload(job, blue_y_data, red_y_data, green_y_data),
    }

    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = data_dir / f"{Path(job.image_name).stem}.json"
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)

    return output_path


def run_extraction(input_dir: Path, data_dir: Path, image_name: str | None = None) -> None:
    """Run extraction for one image or all configured images."""
    jobs = [job for job in PLOT_JOBS if image_name is None or job.image_name == image_name]
    if not jobs:
        raise ValueError(f"No configured image matched: {image_name}")

    total = len(jobs)
    for index, job in enumerate(jobs, start=1):
        print(f"[{index}/{total}] Extracting data from {job.image_name}")
        output_path = extract_data_for_job(job, input_dir=input_dir, data_dir=data_dir)
        print(f"  -> wrote {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract numeric data from plot images in New folder."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=INPUT_DIR,
        help=f"Input image folder (default: {INPUT_DIR})",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR,
        help=f"Output folder for extracted JSON data (default: {DATA_DIR})",
    )
    parser.add_argument(
        "--image-name",
        default=None,
        help="Extract only one image by exact filename.",
    )
    args = parser.parse_args()

    run_extraction(input_dir=args.input_dir, data_dir=args.data_dir, image_name=args.image_name)


if __name__ == "__main__":
    main()
