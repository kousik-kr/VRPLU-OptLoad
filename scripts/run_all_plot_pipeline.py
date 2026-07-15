#!/usr/bin/env python3
"""One-click runner for full plot rebuild pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from extract_plot_data_from_images import run_extraction
from generate_pdfs_from_extracted_data import generate_all_pdfs
from monitor_plot_pipeline import print_status_report
from plot_pipeline_config import DATA_DIR, INPUT_DIR, PDF_DIR


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run full plot rebuild pipeline: extract data from images, "
            "generate PDFs, and print status report."
        )
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
        "--image-name",
        default=None,
        help="Run pipeline for one image by exact filename.",
    )
    args = parser.parse_args()

    print("Step 1/3: Extracting numeric data from images")
    run_extraction(input_dir=args.input_dir, data_dir=args.data_dir, image_name=args.image_name)

    print("Step 2/3: Generating vector PDFs from extracted data")
    generate_all_pdfs(data_dir=args.data_dir, output_dir=args.pdf_dir, image_name=args.image_name)

    print("Step 3/3: Pipeline status")
    print_status_report(input_dir=args.input_dir, data_dir=args.data_dir, pdf_dir=args.pdf_dir)


if __name__ == "__main__":
    main()
