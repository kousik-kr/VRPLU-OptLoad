"""
Phase F: Plot Generation
========================
Generates publication-quality plots from experiment results.

Plots:
1. Distance vs N (number of requests)
2. LU Cost vs N
3. Requests Served vs N
4. Runtime Boxplots
5. Pareto Fronts
6. Ablation Bar Charts
7. Network Scalability Comparison
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from experiments.config import CONFIG, RESULTS_DIR, PLOTS_DIR
from experiments.utils.logger import get_logger

# Import plotting libraries with error handling
try:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    from matplotlib.patches import Patch
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not installed. Install with: pip install matplotlib")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: pandas not installed. Install with: pip install pandas")


class DataLoader:
    """Loads and preprocesses experiment results."""
    
    def __init__(self):
        self.logger = get_logger("data_loader")
        
    def load_algorithm_results(self) -> Dict:
        """Load results from Phase D."""
        results_file = RESULTS_DIR / "algorithm_results.json"
        
        if not results_file.exists():
            self.logger.warning(f"Results file not found: {results_file}")
            return {}
        
        with open(results_file, 'r') as f:
            return json.load(f)
    
    def load_scalability_results(self) -> Dict:
        """Load results from Phase E."""
        results_file = RESULTS_DIR / "scalability" / "scalability_results.json"
        
        if not results_file.exists():
            self.logger.warning(f"Scalability results not found: {results_file}")
            return {}
        
        with open(results_file, 'r') as f:
            return json.load(f)
    
    def organize_by_n_and_algorithm(self, results: Dict) -> Dict:
        """
        Reorganize results by N value and algorithm.
        
        Returns:
            Dict[algorithm][N] -> list of results
        """
        organized = {}
        
        for key, result in results.items():
            # Parse key format: N{n}_R{run}_{algorithm}
            parts = key.split('_')
            if len(parts) >= 3:
                try:
                    n_value = int(parts[0][1:])  # Remove 'N' prefix
                    algorithm = parts[-1]
                    
                    if algorithm not in organized:
                        organized[algorithm] = {}
                    if n_value not in organized[algorithm]:
                        organized[algorithm][n_value] = []
                    
                    organized[algorithm][n_value].append(result)
                except (ValueError, IndexError):
                    continue
        
        return organized
    
    def compute_statistics(self, values: List[float]) -> Dict:
        """Compute mean, std, median for a list of values."""
        if not values:
            return {"mean": 0, "std": 0, "median": 0, "min": 0, "max": 0, "count": 0}
        
        arr = np.array([v for v in values if v is not None])
        if len(arr) == 0:
            return {"mean": 0, "std": 0, "median": 0, "min": 0, "max": 0, "count": 0}
        
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "median": float(np.median(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "count": len(arr)
        }


class PlotGenerator:
    """Generates publication-quality plots."""
    
    def __init__(self, config=None):
        self.config = config or CONFIG.plot
        self.logger = get_logger("plot_generator")
        self.data_loader = DataLoader()
        
        if MATPLOTLIB_AVAILABLE:
            plt.style.use('seaborn-v0_8-whitegrid')
            plt.rcParams['font.size'] = self.config.FONT_SIZE
            plt.rcParams['axes.titlesize'] = self.config.TITLE_SIZE
    
    def _get_color(self, index: int) -> str:
        """Get color from palette."""
        return self.config.COLOR_PALETTE[index % len(self.config.COLOR_PALETTE)]
    
    def _save_plot(self, fig, name: str, formats: List[str] = ['png', 'pdf']):
        """Save plot in multiple formats."""
        for fmt in formats:
            filepath = PLOTS_DIR / f"{name}.{fmt}"
            fig.savefig(filepath, dpi=self.config.DPI, bbox_inches='tight')
            self.logger.info(f"Saved plot: {filepath}")
        plt.close(fig)
    
    def plot_metric_vs_n(self, organized_data: Dict, metric: str, 
                         ylabel: str, title: str, filename: str):
        """
        Generic plotting function for metric vs N.
        
        Args:
            organized_data: Dict[algorithm][N] -> list of results
            metric: Key to extract from results
            ylabel: Y-axis label
            title: Plot title
            filename: Output filename (without extension)
        """
        
        if not MATPLOTLIB_AVAILABLE:
            self.logger.error("matplotlib not available")
            return
        
        fig, ax = plt.subplots(figsize=self.config.FIGURE_SIZE)
        
        algorithms = sorted(organized_data.keys())
        
        for idx, algorithm in enumerate(algorithms):
            n_data = organized_data[algorithm]
            n_values = sorted(n_data.keys())
            
            means = []
            stds = []
            
            for n in n_values:
                values = [r.get(metric) for r in n_data[n] 
                         if r.get("success") and r.get(metric) is not None]
                stats = self.data_loader.compute_statistics(values)
                means.append(stats["mean"])
                stds.append(stats["std"])
            
            color = self._get_color(idx)
            
            ax.errorbar(n_values, means, yerr=stds, 
                       label=algorithm, color=color, 
                       marker='o', capsize=3, linewidth=2, markersize=6)
        
        ax.set_xlabel('Number of Requests (N)')
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        self._save_plot(fig, filename)
    
    def plot_distance_vs_n(self, organized_data: Dict):
        """Plot total distance vs number of requests."""
        self.plot_metric_vs_n(
            organized_data,
            metric="distance",
            ylabel="Total Distance",
            title="Distance vs Number of Requests",
            filename="distance_vs_n"
        )
    
    def plot_lu_cost_vs_n(self, organized_data: Dict):
        """Plot LU cost vs number of requests."""
        self.plot_metric_vs_n(
            organized_data,
            metric="lu_cost",
            ylabel="Loading/Unloading Cost",
            title="LU Cost vs Number of Requests",
            filename="lu_cost_vs_n"
        )
    
    def plot_served_requests_vs_n(self, organized_data: Dict):
        """Plot served requests vs total requests."""
        
        if not MATPLOTLIB_AVAILABLE:
            return
        
        fig, ax = plt.subplots(figsize=self.config.FIGURE_SIZE)
        
        algorithms = sorted(organized_data.keys())
        
        for idx, algorithm in enumerate(algorithms):
            n_data = organized_data[algorithm]
            n_values = sorted(n_data.keys())
            
            # Calculate service rate (served / total)
            rates = []
            stds = []
            
            for n in n_values:
                ratios = []
                for r in n_data[n]:
                    if r.get("success") and r.get("served_requests") is not None:
                        total = r.get("total_requests", n)
                        if total > 0:
                            ratios.append(r["served_requests"] / total * 100)
                
                stats = self.data_loader.compute_statistics(ratios)
                rates.append(stats["mean"])
                stds.append(stats["std"])
            
            color = self._get_color(idx)
            
            ax.errorbar(n_values, rates, yerr=stds, 
                       label=algorithm, color=color, 
                       marker='o', capsize=3, linewidth=2, markersize=6)
        
        ax.set_xlabel('Number of Requests (N)')
        ax.set_ylabel('Service Rate (%)')
        ax.set_title('Request Service Rate vs Number of Requests')
        ax.legend(loc='best', framealpha=0.9)
        ax.set_ylim(0, 105)
        ax.grid(True, alpha=0.3)
        
        self._save_plot(fig, "served_requests_vs_n")
    
    def plot_runtime_boxplots(self, organized_data: Dict):
        """Plot runtime distribution as boxplots for each N and algorithm."""
        
        if not MATPLOTLIB_AVAILABLE:
            return
        
        algorithms = sorted(organized_data.keys())
        all_n_values = set()
        for algo_data in organized_data.values():
            all_n_values.update(algo_data.keys())
        n_values = sorted(all_n_values)
        
        fig, axes = plt.subplots(1, len(n_values), figsize=(3*len(n_values), 6))
        if len(n_values) == 1:
            axes = [axes]
        
        for ax_idx, n in enumerate(n_values):
            ax = axes[ax_idx]
            
            data_for_box = []
            labels = []
            
            for algorithm in algorithms:
                if n in organized_data.get(algorithm, {}):
                    runtimes = [r.get("runtime_ms", 0) / 1000  # Convert to seconds
                               for r in organized_data[algorithm][n] 
                               if r.get("success")]
                    if runtimes:
                        data_for_box.append(runtimes)
                        labels.append(algorithm)
            
            if data_for_box:
                bp = ax.boxplot(data_for_box, labels=labels, patch_artist=True)
                
                for i, patch in enumerate(bp['boxes']):
                    patch.set_facecolor(self._get_color(i))
                    patch.set_alpha(0.7)
                
                ax.set_title(f'N = {n}')
                ax.set_ylabel('Runtime (seconds)')
                ax.tick_params(axis='x', rotation=45)
        
        fig.suptitle('Runtime Distribution by Algorithm and Request Count', fontsize=14)
        plt.tight_layout()
        
        self._save_plot(fig, "runtime_boxplots")
    
    def plot_pareto_fronts(self, organized_data: Dict, n_value: int = 60):
        """
        Plot Pareto fronts (Distance vs LU Cost) for each algorithm.
        
        Args:
            n_value: Fixed N to visualize Pareto fronts for
        """
        
        if not MATPLOTLIB_AVAILABLE:
            return
        
        fig, ax = plt.subplots(figsize=self.config.FIGURE_SIZE)
        
        algorithms = sorted(organized_data.keys())
        
        for idx, algorithm in enumerate(algorithms):
            if n_value not in organized_data.get(algorithm, {}):
                continue
            
            results = organized_data[algorithm][n_value]
            
            distances = []
            lu_costs = []
            
            for r in results:
                if r.get("success") and r.get("distance") is not None and r.get("lu_cost") is not None:
                    distances.append(r["distance"])
                    lu_costs.append(r["lu_cost"])
            
            color = self._get_color(idx)
            ax.scatter(distances, lu_costs, label=algorithm, color=color, alpha=0.6, s=50)
        
        ax.set_xlabel('Distance')
        ax.set_ylabel('LU Cost')
        ax.set_title(f'Pareto Front: Distance vs LU Cost (N = {n_value})')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        self._save_plot(fig, f"pareto_front_n{n_value}")
    
    def plot_ablation_bar_chart(self, organized_data: Dict, n_value: int = 60):
        """
        Plot ablation study results as grouped bar chart.
        
        Compares OptLoad variants:
        - OptLoad (full)
        - OptLoad-C (no clustering)
        - OptLoad-LU (no LU optimization)
        - OptLoad-TW (no time window handling)
        - OptLoad-P (no precedence)
        """
        
        if not MATPLOTLIB_AVAILABLE:
            return
        
        ablation_variants = ["OptLoad", "OptLoad-C", "OptLoad-LU", "OptLoad-TW", "OptLoad-P"]
        metrics = ["distance", "lu_cost", "served_requests"]
        metric_labels = ["Distance", "LU Cost", "Served Requests"]
        
        # Filter to available variants
        available = [v for v in ablation_variants if v in organized_data]
        
        if not available:
            self.logger.warning("No ablation variants found in results")
            return
        
        fig, axes = plt.subplots(1, len(metrics), figsize=(4*len(metrics), 5))
        if len(metrics) == 1:
            axes = [axes]
        
        x = np.arange(len(available))
        width = 0.6
        
        for ax_idx, (metric, label) in enumerate(zip(metrics, metric_labels)):
            ax = axes[ax_idx]
            
            means = []
            stds = []
            
            for variant in available:
                if n_value in organized_data.get(variant, {}):
                    values = [r.get(metric) for r in organized_data[variant][n_value]
                             if r.get("success") and r.get(metric) is not None]
                    stats = self.data_loader.compute_statistics(values)
                    means.append(stats["mean"])
                    stds.append(stats["std"])
                else:
                    means.append(0)
                    stds.append(0)
            
            colors = [self._get_color(i) for i in range(len(available))]
            
            bars = ax.bar(x, means, width, yerr=stds, capsize=3, color=colors, alpha=0.8)
            
            ax.set_ylabel(label)
            ax.set_xticks(x)
            ax.set_xticklabels(available, rotation=45, ha='right')
            ax.set_title(f'{label} (N = {n_value})')
        
        fig.suptitle('Ablation Study: Effect of Algorithm Components', fontsize=14)
        plt.tight_layout()
        
        self._save_plot(fig, f"ablation_n{n_value}")
    
    def plot_scalability_comparison(self, scalability_data: Dict):
        """Plot network scalability results."""
        
        if not MATPLOTLIB_AVAILABLE or not scalability_data:
            return
        
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        percentages = []
        algorithms = set()
        
        for key, data in scalability_data.items():
            percentages.append(data["percentage"] * 100)
            algorithms.update(data.get("algorithms", {}).keys())
        
        percentages = sorted(set(percentages))
        algorithms = sorted(algorithms)
        
        # Plot runtime vs network size
        ax1 = axes[0]
        for idx, algorithm in enumerate(algorithms):
            runtimes = []
            for pct in percentages:
                key = f"network_{int(pct)}pct"
                if key in scalability_data:
                    algo_results = scalability_data[key].get("algorithms", {}).get(algorithm, [])
                    times = [r.get("runtime_ms", 0) / 1000 for r in algo_results if r.get("success")]
                    runtimes.append(np.mean(times) if times else 0)
                else:
                    runtimes.append(0)
            
            color = self._get_color(idx)
            ax1.plot(percentages, runtimes, marker='o', label=algorithm, color=color, linewidth=2)
        
        ax1.set_xlabel('Network Size (%)')
        ax1.set_ylabel('Average Runtime (seconds)')
        ax1.set_title('Runtime vs Network Size')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot distance vs network size
        ax2 = axes[1]
        for idx, algorithm in enumerate(algorithms):
            distances = []
            for pct in percentages:
                key = f"network_{int(pct)}pct"
                if key in scalability_data:
                    algo_results = scalability_data[key].get("algorithms", {}).get(algorithm, [])
                    dists = [r.get("distance", 0) for r in algo_results if r.get("success")]
                    distances.append(np.mean(dists) if dists else 0)
                else:
                    distances.append(0)
            
            color = self._get_color(idx)
            ax2.plot(percentages, distances, marker='s', label=algorithm, color=color, linewidth=2)
        
        ax2.set_xlabel('Network Size (%)')
        ax2.set_ylabel('Average Distance')
        ax2.set_title('Distance vs Network Size')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        self._save_plot(fig, "scalability_comparison")
    
    def generate_all_plots(self):
        """Generate all experiment plots."""
        
        self.logger.section("Phase F: Plot Generation")
        
        # Load data
        algo_results = self.data_loader.load_algorithm_results()
        scalability_results = self.data_loader.load_scalability_results()
        
        if not algo_results:
            self.logger.warning("No algorithm results to plot. Run Phase D first.")
            return
        
        # Organize data
        organized = self.data_loader.organize_by_n_and_algorithm(algo_results)
        
        if not organized:
            self.logger.warning("Could not organize results. Check data format.")
            return
        
        self.logger.info(f"Loaded results for {len(organized)} algorithms")
        
        # Generate plots
        self.logger.info("Generating Distance vs N plot...")
        self.plot_distance_vs_n(organized)
        
        self.logger.info("Generating LU Cost vs N plot...")
        self.plot_lu_cost_vs_n(organized)
        
        self.logger.info("Generating Served Requests vs N plot...")
        self.plot_served_requests_vs_n(organized)
        
        self.logger.info("Generating Runtime boxplots...")
        self.plot_runtime_boxplots(organized)
        
        # Generate Pareto fronts for different N values
        for n in [40, 60, 80]:
            if any(n in algo_data for algo_data in organized.values()):
                self.logger.info(f"Generating Pareto front for N={n}...")
                self.plot_pareto_fronts(organized, n)
        
        self.logger.info("Generating Ablation bar chart...")
        self.plot_ablation_bar_chart(organized)
        
        # Scalability plots
        if scalability_results:
            self.logger.info("Generating Scalability comparison...")
            self.plot_scalability_comparison(scalability_results)
        
        self.logger.info(f"All plots saved to: {PLOTS_DIR}")


def main():
    """Run plot generation as standalone script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate experiment plots")
    parser.add_argument("--plots", type=str, nargs="+", default=None,
                       help="Specific plots to generate")
    
    args = parser.parse_args()
    
    if not MATPLOTLIB_AVAILABLE:
        print("Error: matplotlib is required. Install with: pip install matplotlib")
        sys.exit(1)
    
    generator = PlotGenerator()
    generator.generate_all_plots()
    
    print(f"\nPlots saved to: {PLOTS_DIR}")


if __name__ == "__main__":
    main()
