#!/usr/bin/env python3
"""
Standalone Plot Generator Script
================================

Generates all experiment plots from results data.
Can be run independently after Phase D completes.

Usage:
    python generate_plots.py                     # Generate all plots
    python generate_plots.py --type distance     # Generate specific plot type
    python generate_plots.py --n 60              # Plots for specific N value
    python generate_plots.py --output ./myplots  # Custom output directory
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.config import CONFIG, RESULTS_DIR, PLOTS_DIR
from experiments.phase_f_plot_generation import PlotGenerator, DataLoader, MATPLOTLIB_AVAILABLE

def main():
    parser = argparse.ArgumentParser(
        description="Generate experiment plots",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--type', '-t',
        nargs='+',
        choices=['distance', 'lu_cost', 'served', 'runtime', 'pareto', 'ablation', 'scalability', 'all'],
        default=['all'],
        help='Type of plots to generate'
    )
    
    parser.add_argument(
        '--n', '-N',
        type=int,
        nargs='+',
        help='N values for Pareto and ablation plots'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output directory for plots'
    )
    
    parser.add_argument(
        '--format', '-f',
        nargs='+',
        choices=['png', 'pdf', 'svg', 'eps'],
        default=['png', 'pdf'],
        help='Output formats'
    )
    
    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        help='DPI for raster output'
    )
    
    args = parser.parse_args()
    
    if not MATPLOTLIB_AVAILABLE:
        print("Error: matplotlib is required. Install with: pip install matplotlib")
        sys.exit(1)
    
    # Update output directory
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = PLOTS_DIR
    
    # Update config
    CONFIG.plot.DPI = args.dpi
    
    # Load data
    loader = DataLoader()
    algo_results = loader.load_algorithm_results()
    scalability_results = loader.load_scalability_results()
    
    if not algo_results:
        print("No algorithm results found. Run Phase D first.")
        print(f"Expected results file: {RESULTS_DIR / 'algorithm_results.json'}")
        sys.exit(1)
    
    organized = loader.organize_by_n_and_algorithm(algo_results)
    print(f"Loaded results for algorithms: {list(organized.keys())}")
    
    # Create generator
    generator = PlotGenerator()
    
    plot_types = args.type
    if 'all' in plot_types:
        plot_types = ['distance', 'lu_cost', 'served', 'runtime', 'pareto', 'ablation', 'scalability']
    
    # N values for specific plots
    n_values = args.n if args.n else [40, 60, 80]
    
    # Generate requested plots
    for plot_type in plot_types:
        print(f"Generating {plot_type} plot...")
        
        if plot_type == 'distance':
            generator.plot_distance_vs_n(organized)
            
        elif plot_type == 'lu_cost':
            generator.plot_lu_cost_vs_n(organized)
            
        elif plot_type == 'served':
            generator.plot_served_requests_vs_n(organized)
            
        elif plot_type == 'runtime':
            generator.plot_runtime_boxplots(organized)
            
        elif plot_type == 'pareto':
            for n in n_values:
                if any(n in algo_data for algo_data in organized.values()):
                    generator.plot_pareto_fronts(organized, n)
                else:
                    print(f"  No data for N={n}, skipping")
                    
        elif plot_type == 'ablation':
            for n in n_values:
                generator.plot_ablation_bar_chart(organized, n)
                
        elif plot_type == 'scalability':
            if scalability_results:
                generator.plot_scalability_comparison(scalability_results)
            else:
                print("  No scalability results found")
    
    print(f"\nPlots saved to: {output_dir}")


if __name__ == "__main__":
    main()
