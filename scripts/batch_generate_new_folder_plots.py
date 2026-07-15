#!/usr/bin/env python3
"""Batch-generate styled PDFs for all figures inside New folder.

This script applies a consistent output style to every PNG in the input folder:
1) Remove flat background color to transparency.
2) Export all images as PDF in one run.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re

import matplotlib.pyplot as plt
import numpy as np


COPY_SUFFIX_PATTERN = re.compile(r"\s*\(\d+\)$")


def normalized_output_stem(path: Path) -> str:
    return COPY_SUFFIX_PATTERN.sub("", path.stem).strip()


def to_rgba_float(image: np.ndarray) -> np.ndarray:
    """Normalize input image to RGBA float format in [0, 1]."""
    if image.ndim == 2:
        image = np.stack([image, image, image], axis=-1)

    if image.ndim != 3 or image.shape[2] not in (3, 4):
        raise ValueError("Expected image with shape (H, W, 3) or (H, W, 4).")

    if image.dtype.kind in {"u", "i"}:
        rgba = image.astype(np.float32) / 255.0
    else:
        rgba = image.astype(np.float32)
        if float(rgba.max()) > 1.0:
            rgba /= 255.0

    if rgba.shape[2] == 3:
        alpha = np.ones((rgba.shape[0], rgba.shape[1], 1), dtype=np.float32)
        rgba = np.concatenate([rgba, alpha], axis=2)

    return np.clip(rgba, 0.0, 1.0)


def estimate_background_color(rgba: np.ndarray) -> np.ndarray:
    """Estimate background color from edge and corner samples."""
    height, width, _ = rgba.shape
    points = [
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
        (0, width // 2),
        (height - 1, width // 2),
        (height // 2, 0),
        (height // 2, width - 1),
    ]
    samples = np.array([rgba[y, x, :3] for y, x in points], dtype=np.float32)
    return samples.mean(axis=0)


def remove_background(rgba: np.ndarray, tolerance: float) -> np.ndarray:
    """Convert near-background pixels to transparent alpha."""
    output = rgba.copy()
    bg_color = estimate_background_color(output)
    distance = np.linalg.norm(output[:, :, :3] - bg_color, axis=2)
    bg_mask = distance <= tolerance
    output[:, :, 3] = np.where(bg_mask, 0.0, output[:, :, 3])
    return output


def save_pdf(image_rgba: np.ndarray, output_path: Path, dpi: int) -> None:
    """Save styled RGBA image as transparent PDF."""
    height, width, _ = image_rgba.shape
    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(image_rgba, interpolation="nearest")
    ax.axis("off")
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, transparent=True)
    plt.close(fig)


def process_all_images(
    input_dir: Path,
    output_dir: Path,
    background_tolerance: float,
    dpi: int,
    export_png: bool,
) -> None:
    """Process all PNG files in input_dir and export styled outputs."""
    png_files = sorted(p for p in input_dir.iterdir() if p.suffix.lower() == ".png")
    if not png_files:
        raise FileNotFoundError(f"No PNG files found in: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Found {len(png_files)} PNG files in {input_dir}")

    for src_path in png_files:
        image = plt.imread(src_path)
        rgba = to_rgba_float(image)
        rgba = remove_background(rgba, tolerance=background_tolerance)

        output_stem = normalized_output_stem(src_path)
        pdf_path = output_dir / f"{output_stem}.pdf"
        save_pdf(rgba, pdf_path, dpi=dpi)

        if export_png:
            png_path = output_dir / f"{output_stem}.png"
            plt.imsave(png_path, rgba)

        print(f"Processed: {src_path.name} -> {pdf_path.name}")


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    default_input_dir = repo_root / "New folder"
    default_output_dir = default_input_dir / "styled_pdf"

    parser = argparse.ArgumentParser(
        description=(
            "One-click batch generator for all plots in 'New folder' with "
            "transparent background."
        )
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=default_input_dir,
        help=f"Input folder with PNG plots (default: {default_input_dir})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir,
        help=f"Output folder for styled files (default: {default_output_dir})",
    )
    parser.add_argument(
        "--background-tolerance",
        type=float,
        default=0.06,
        help="Background color tolerance in [0,1] (default: 0.06)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Output DPI for PDF export (default: 300)",
    )
    parser.add_argument(
        "--export-png",
        action="store_true",
        help="Also export styled PNG files in addition to PDFs.",
    )
    args = parser.parse_args()

    process_all_images(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        background_tolerance=args.background_tolerance,
        dpi=args.dpi,
        export_png=args.export_png,
    )


if __name__ == "__main__":
    main()
