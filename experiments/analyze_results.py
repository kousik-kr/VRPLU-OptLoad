"""
Results Analysis and Export
===========================
Utilities for analyzing and exporting experiment results.

Features:
- Summary statistics computation
- LaTeX table generation
- CSV export
- Result comparison
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import csv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from experiments.config import CONFIG, RESULTS_DIR
from experiments.utils.logger import get_logger

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class ResultsAnalyzer:
    """
    Analyzes experiment results and generates summary statistics.
    """
    
    def __init__(self):
        self.logger = get_logger("results_analyzer")
        
    def load_results(self) -> Dict:
        """Load algorithm results."""
        results_file = RESULTS_DIR / "algorithm_results.json"
        if not results_file.exists():
            return {}
        with open(results_file, 'r') as f:
            return json.load(f)
    
    def compute_statistics(self, values: List[float]) -> Dict:
        """Compute summary statistics for a list of values."""
        if not values:
            return {"n": 0, "mean": None, "std": None, "median": None, "min": None, "max": None}
        
        clean_values = [v for v in values if v is not None]
        if not clean_values:
            return {"n": 0, "mean": None, "std": None, "median": None, "min": None, "max": None}
        
        if NUMPY_AVAILABLE:
            arr = np.array(clean_values)
            return {
                "n": len(arr),
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)),
                "median": float(np.median(arr)),
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "q25": float(np.percentile(arr, 25)),
                "q75": float(np.percentile(arr, 75)),
            }
        else:
            sorted_vals = sorted(clean_values)
            n = len(sorted_vals)
            mean = sum(sorted_vals) / n
            variance = sum((x - mean) ** 2 for x in sorted_vals) / n
            std = variance ** 0.5
            median = sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2
            return {
                "n": n,
                "mean": mean,
                "std": std,
                "median": median,
                "min": min(sorted_vals),
                "max": max(sorted_vals),
            }
    
    def summarize_by_algorithm_and_n(self, results: Dict) -> Dict:
        """
        Create summary statistics grouped by algorithm and N.
        
        Returns:
            Dict[algorithm][N] -> stats for each metric
        """
        # Organize data
        organized = defaultdict(lambda: defaultdict(list))
        
        for key, result in results.items():
            parts = key.split('_')
            if len(parts) >= 3:
                try:
                    n_value = int(parts[0][1:])
                    algorithm = parts[-1]
                    organized[algorithm][n_value].append(result)
                except (ValueError, IndexError):
                    continue
        
        # Compute statistics
        summary = {}
        metrics = ["distance", "lu_cost", "served_requests", "runtime_ms"]
        
        for algorithm, n_data in organized.items():
            summary[algorithm] = {}
            for n_value, results_list in sorted(n_data.items()):
                summary[algorithm][n_value] = {}
                
                for metric in metrics:
                    values = [r.get(metric) for r in results_list if r.get("success")]
                    summary[algorithm][n_value][metric] = self.compute_statistics(values)
                
                # Service rate
                rates = []
                for r in results_list:
                    if r.get("success") and r.get("served_requests") is not None:
                        total = r.get("total_requests", n_value)
                        if total > 0:
                            rates.append(r["served_requests"] / total * 100)
                summary[algorithm][n_value]["service_rate"] = self.compute_statistics(rates)
        
        return summary
    
    def generate_summary_table(self, summary: Dict, metric: str = "distance") -> str:
        """
        Generate a formatted summary table.
        
        Args:
            summary: Summary statistics dict
            metric: Metric to display
            
        Returns:
            Formatted table string
        """
        # Get all algorithms and N values
        algorithms = sorted(summary.keys())
        n_values = set()
        for algo_data in summary.values():
            n_values.update(algo_data.keys())
        n_values = sorted(n_values)
        
        # Header
        header = f"{'Algorithm':<15}" + "".join(f"N={n:>6}" for n in n_values)
        separator = "-" * len(header)
        
        lines = [f"\n{metric.upper()} Summary (mean ± std)", separator, header, separator]
        
        for algorithm in algorithms:
            row = f"{algorithm:<15}"
            for n in n_values:
                stats = summary.get(algorithm, {}).get(n, {}).get(metric, {})
                mean = stats.get("mean")
                std = stats.get("std")
                if mean is not None:
                    if metric == "runtime_ms":
                        row += f"{mean/1000:>5.1f}s "
                    elif metric == "service_rate":
                        row += f"{mean:>5.1f}% "
                    else:
                        row += f"{mean:>6.1f} "
                else:
                    row += "   N/A "
            lines.append(row)
        
        lines.append(separator)
        return "\n".join(lines)
    
    def export_to_csv(self, summary: Dict, output_path: Path = None):
        """Export summary statistics to CSV."""
        if output_path is None:
            output_path = RESULTS_DIR / "summary_statistics.csv"
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Algorithm", "N", "Metric",
                "N_samples", "Mean", "Std", "Median", "Min", "Max"
            ])
            
            for algorithm, n_data in summary.items():
                for n_value, metrics_data in n_data.items():
                    for metric, stats in metrics_data.items():
                        writer.writerow([
                            algorithm, n_value, metric,
                            stats.get("n", 0),
                            stats.get("mean"),
                            stats.get("std"),
                            stats.get("median"),
                            stats.get("min"),
                            stats.get("max"),
                        ])
        
        self.logger.info(f"Exported CSV to: {output_path}")
        return output_path
    
    def generate_latex_table(self, summary: Dict, metric: str = "distance") -> str:
        """
        Generate a LaTeX table for the paper.
        
        Args:
            summary: Summary statistics dict
            metric: Metric to display
            
        Returns:
            LaTeX table string
        """
        algorithms = sorted(summary.keys())
        n_values = set()
        for algo_data in summary.values():
            n_values.update(algo_data.keys())
        n_values = sorted(n_values)
        
        # LaTeX header
        n_cols = len(n_values)
        latex = [
            "\\begin{table}[htbp]",
            "\\centering",
            f"\\caption{{{metric.replace('_', ' ').title()} by Algorithm and Number of Requests}}",
            f"\\label{{tab:{metric}}}",
            "\\begin{tabular}{l" + "c" * n_cols + "}",
            "\\toprule",
            "Algorithm & " + " & ".join(f"$N={n}$" for n in n_values) + " \\\\",
            "\\midrule",
        ]
        
        for algorithm in algorithms:
            row_values = []
            for n in n_values:
                stats = summary.get(algorithm, {}).get(n, {}).get(metric, {})
                mean = stats.get("mean")
                std = stats.get("std")
                if mean is not None and std is not None:
                    if metric == "runtime_ms":
                        row_values.append(f"${mean/1000:.1f} \\pm {std/1000:.1f}$")
                    elif metric == "service_rate":
                        row_values.append(f"${mean:.1f}\\%$")
                    else:
                        row_values.append(f"${mean:.1f} \\pm {std:.1f}$")
                else:
                    row_values.append("--")
            
            latex.append(f"{algorithm} & " + " & ".join(row_values) + " \\\\")
        
        latex.extend([
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
        ])
        
        return "\n".join(latex)
    
    def compare_algorithms(self, summary: Dict, baseline: str = "Insertion") -> Dict:
        """
        Compare algorithms against a baseline.
        
        Returns relative improvement percentages.
        """
        comparisons = {}
        
        for algorithm in summary:
            if algorithm == baseline:
                continue
            
            comparisons[algorithm] = {}
            
            for n_value in summary.get(baseline, {}):
                comparisons[algorithm][n_value] = {}
                
                for metric in ["distance", "lu_cost", "runtime_ms", "service_rate"]:
                    baseline_mean = summary.get(baseline, {}).get(n_value, {}).get(metric, {}).get("mean")
                    algo_mean = summary.get(algorithm, {}).get(n_value, {}).get(metric, {}).get("mean")
                    
                    if baseline_mean and algo_mean and baseline_mean != 0:
                        # For distance, lu_cost, runtime: lower is better (negative improvement)
                        # For service_rate: higher is better (positive improvement)
                        if metric == "service_rate":
                            improvement = ((algo_mean - baseline_mean) / baseline_mean) * 100
                        else:
                            improvement = ((baseline_mean - algo_mean) / baseline_mean) * 100
                        comparisons[algorithm][n_value][metric] = improvement
        
        return comparisons


def main():
    """Run analysis as standalone script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze experiment results")
    parser.add_argument("--export-csv", action="store_true", help="Export to CSV")
    parser.add_argument("--export-latex", action="store_true", help="Export LaTeX tables")
    parser.add_argument("--metric", type=str, default="distance", 
                       help="Metric to analyze")
    parser.add_argument("--compare", type=str, default=None,
                       help="Compare against baseline algorithm")
    
    args = parser.parse_args()
    
    analyzer = ResultsAnalyzer()
    results = analyzer.load_results()
    
    if not results:
        print("No results found. Run experiments first.")
        return
    
    summary = analyzer.summarize_by_algorithm_and_n(results)
    
    # Print summary tables
    for metric in ["distance", "lu_cost", "service_rate", "runtime_ms"]:
        print(analyzer.generate_summary_table(summary, metric))
    
    # Export CSV
    if args.export_csv:
        csv_path = analyzer.export_to_csv(summary)
        print(f"\nCSV exported to: {csv_path}")
    
    # Export LaTeX
    if args.export_latex:
        for metric in ["distance", "lu_cost", "service_rate"]:
            latex = analyzer.generate_latex_table(summary, metric)
            latex_file = RESULTS_DIR / f"table_{metric}.tex"
            with open(latex_file, 'w') as f:
                f.write(latex)
            print(f"LaTeX table saved to: {latex_file}")
    
    # Compare algorithms
    if args.compare:
        print(f"\n\nComparison vs {args.compare}:")
        comparisons = analyzer.compare_algorithms(summary, args.compare)
        for algo, n_data in comparisons.items():
            print(f"\n{algo}:")
            for n, metrics in sorted(n_data.items()):
                print(f"  N={n}:", end=" ")
                for metric, improvement in metrics.items():
                    sign = "+" if improvement > 0 else ""
                    print(f"{metric}:{sign}{improvement:.1f}%", end=" ")
                print()


if __name__ == "__main__":
    main()
