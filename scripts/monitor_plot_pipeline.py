#!/usr/bin/env python3
"""Monitor extraction/generation status for all configured plot images."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from plot_pipeline_config import DATA_DIR, INPUT_DIR, PDF_DIR, PLOT_JOBS, image_stem, pdf_stem


def status_icon(flag: bool) -> str:
    return "OK" if flag else "MISS"


def print_status_report(input_dir: Path, data_dir: Path, pdf_dir: Path) -> None:
    """Print per-image status for source image, extracted data, and output PDF."""
    rows: list[tuple[str, bool, bool, bool]] = []
    for job in PLOT_JOBS:
        image_path = input_dir / job.image_name
        data_path = data_dir / f"{image_stem(job.image_name)}.json"
        pdf_path = pdf_dir / f"{pdf_stem(job.image_name)}.pdf"
        rows.append((job.image_name, image_path.exists(), data_path.exists(), pdf_path.exists()))

    print("Image | Source | Data JSON | PDF")
    print("-" * 72)
    for image_name, src_ok, data_ok, pdf_ok in rows:
        print(
            f"{image_name} | {status_icon(src_ok):>4} | "
            f"{status_icon(data_ok):>8} | {status_icon(pdf_ok):>4}"
        )

    total = len(rows)
    source_ready = sum(1 for _, src_ok, _, _ in rows if src_ok)
    data_ready = sum(1 for _, _, data_ok, _ in rows if data_ok)
    pdf_ready = sum(1 for _, _, _, pdf_ok in rows if pdf_ok)
    print("-" * 72)
    print(f"Summary: source={source_ready}/{total}, data={data_ready}/{total}, pdf={pdf_ready}/{total}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show pipeline status for all plot images in New folder."
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
        help=f"Extracted JSON folder (default: {DATA_DIR})",
    )
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        default=PDF_DIR,
        help=f"Generated PDF folder (default: {PDF_DIR})",
    )
    parser.add_argument(
        "--watch",
        type=int,
        default=0,
        help="Refresh interval in seconds. Use 0 for single report.",
    )
    args = parser.parse_args()

    if args.watch <= 0:
        print_status_report(input_dir=args.input_dir, data_dir=args.data_dir, pdf_dir=args.pdf_dir)
        return

    while True:
        print("\n" + "=" * 72)
        print_status_report(input_dir=args.input_dir, data_dir=args.data_dir, pdf_dir=args.pdf_dir)
        time.sleep(args.watch)


if __name__ == "__main__":
    main()
