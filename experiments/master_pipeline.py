#!/usr/bin/env python3
"""
Master Experiment Pipeline
==========================

Orchestrates the full experiment workflow with proper checkpointing:

1. Verify queries exist
2. Run all algorithms on all queries
3. Generate charts
4. Produce final report

Usage:
    python master_pipeline.py                    # Run full pipeline
    python master_pipeline.py --status          # Show current status
    python master_pipeline.py --reset           # Reset and start over
    python master_pipeline.py --charts-only     # Just generate charts
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.absolute()))

from config import CONFIG, QUERIES_DIR, RESULTS_DIR, CHECKPOINTS_DIR, PROJECT_ROOT
from utils.logger import get_logger


class ExperimentPipeline:
    """Master orchestrator for the experiment pipeline."""
    
    def __init__(self):
        self.logger = get_logger("pipeline")
        self.checkpoint_file = CHECKPOINTS_DIR / "pipeline_state.json"
        self.state = self._load_state()
    
    def _load_state(self):
        """Load pipeline state from checkpoint."""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        return {
            "queries_verified": False,
            "algorithms_started": False,
            "algorithms_completed": [],
            "charts_generated": False,
            "last_update": None,
            "start_time": None,
        }
    
    def _save_state(self):
        """Save pipeline state."""
        CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
        self.state["last_update"] = datetime.now().isoformat()
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def show_status(self):
        """Display current pipeline status."""
        print("\n" + "="*60)
        print("PIPELINE STATUS")
        print("="*60)
        
        # Check queries
        query_index = QUERIES_DIR / "query_index.json"
        if query_index.exists():
            with open(query_index, 'r') as f:
                queries = json.load(f)
            print(f"✓ Queries: {len(queries)} available")
        else:
            print("✗ Queries: Not generated")
        
        # Check results
        results_file = RESULTS_DIR / "experiment_results.json"
        if results_file.exists():
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            # Count by algorithm
            algo_counts = {}
            for key, val in results.items():
                algo = val["algorithm"]
                algo_counts[algo] = algo_counts.get(algo, 0) + 1
            
            total = len(results)
            print(f"\n✓ Results: {total} experiments completed")
            for algo, count in sorted(algo_counts.items()):
                print(f"    {algo}: {count}")
        else:
            print("\n✗ Results: No experiments run yet")
        
        # Check charts
        charts_dir = RESULTS_DIR / "charts"
        if charts_dir.exists():
            chart_files = list(charts_dir.glob("*.png"))
            csv_files = list(charts_dir.glob("*.csv"))
            print(f"\n✓ Charts: {len(chart_files)} images, {len(csv_files)} CSV files")
        else:
            print("\n✗ Charts: Not generated")
        
        print("\n" + "="*60)
    
    def verify_queries(self):
        """Verify that queries are generated."""
        self.logger.info("Verifying queries...")
        
        query_index = QUERIES_DIR / "query_index.json"
        if not query_index.exists():
            self.logger.error("Query index not found. Please run query generation first.")
            self.logger.info("Run: python tour_query_generator.py")
            return False
        
        with open(query_index, 'r') as f:
            queries = json.load(f)
        
        expected = 600  # 100 runs × 6 N values
        if len(queries) < expected:
            self.logger.warning(f"Found {len(queries)} queries, expected {expected}")
        
        # Verify files exist
        missing = 0
        for query_id, query_path in queries.items():
            if not Path(query_path).exists():
                missing += 1
        
        if missing > 0:
            self.logger.error(f"{missing} query files missing")
            return False
        
        self.logger.info(f"✓ All {len(queries)} queries verified")
        self.state["queries_verified"] = True
        self._save_state()
        return True
    
    def run_algorithms(self):
        """Run all algorithms on all queries."""
        self.logger.section("Running Algorithms")
        
        from run_full_experiments import RobustExperimentRunner
        
        runner = RobustExperimentRunner()
        self.state["algorithms_started"] = True
        self._save_state()
        
        runner.run_all_experiments(timeout_per_query=300)
        
        self.state["algorithms_completed"] = list(runner.algorithms.keys())
        self._save_state()
    
    def generate_charts(self):
        """Generate all charts."""
        self.logger.section("Generating Charts")
        
        from generate_charts import main as generate_charts_main
        
        generate_charts_main()
        
        self.state["charts_generated"] = True
        self._save_state()
    
    def generate_report(self):
        """Generate final report."""
        self.logger.section("Generating Final Report")
        
        report_file = RESULTS_DIR / "FINAL_REPORT.md"
        
        # Load results
        results_file = RESULTS_DIR / "experiment_results.json"
        if not results_file.exists():
            self.logger.error("No results to report")
            return
        
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        # Aggregate statistics
        from collections import defaultdict
        stats = defaultdict(lambda: defaultdict(lambda: {
            "served": [], "lu_cost": [], "runtime": [], "success": 0, "total": 0
        }))
        
        for key, result in results.items():
            algo = result["algorithm"]
            n_val = result["query_id"].split("_")[0]
            
            stats[algo][n_val]["served"].append(result["served_requests"])
            stats[algo][n_val]["lu_cost"].append(result["lu_cost"])
            stats[algo][n_val]["runtime"].append(result["runtime_ms"])
            stats[algo][n_val]["total"] += 1
            if result["served_requests"] > 0:
                stats[algo][n_val]["success"] += 1
        
        # Write report
        with open(report_file, 'w') as f:
            f.write("# VRP-LU Experiment Final Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Experiments:** {len(results)}\n")
            f.write(f"- **Algorithms Tested:** {len(stats)}\n")
            f.write(f"- **N Values:** 10, 20, 40, 60, 80, 100\n")
            f.write(f"- **Runs per Configuration:** 100\n\n")
            
            f.write("## Results Overview\n\n")
            
            for algo in sorted(stats.keys()):
                f.write(f"### {algo}\n\n")
                
                total_served = sum(sum(stats[algo][n]["served"]) for n in stats[algo])
                total_runs = sum(stats[algo][n]["total"] for n in stats[algo])
                success_rate = sum(stats[algo][n]["success"] for n in stats[algo]) / total_runs * 100
                
                f.write(f"- Total runs: {total_runs}\n")
                f.write(f"- Success rate: {success_rate:.1f}%\n")
                f.write(f"- Total requests served: {total_served}\n\n")
                
                f.write("| N | Runs | Success | Avg Served | Avg LU Cost | Avg Runtime |\n")
                f.write("|---|------|---------|------------|-------------|-------------|\n")
                
                for n in ["N10", "N20", "N40", "N60", "N80", "N100"]:
                    if n in stats[algo]:
                        s = stats[algo][n]
                        avg_served = sum(s["served"]) / len(s["served"]) if s["served"] else 0
                        avg_lu = sum(s["lu_cost"]) / len(s["lu_cost"]) if s["lu_cost"] else 0
                        avg_rt = sum(s["runtime"]) / len(s["runtime"]) if s["runtime"] else 0
                        f.write(f"| {n[1:]} | {s['total']} | {s['success']} | {avg_served:.1f} | {avg_lu:.1f} | {avg_rt:.0f}ms |\n")
                
                f.write("\n")
            
            f.write("## Charts\n\n")
            f.write("The following charts are available in the `results/charts/` directory:\n\n")
            f.write("1. **scalability_served.png** - Requests served vs N\n")
            f.write("2. **lu_cost.png** - L-U cost vs N\n")
            f.write("3. **runtime.png** - Runtime vs N\n")
            f.write("4. **comparison_bar.png** - Algorithm comparison at N=60\n\n")
            
            f.write("## Methodology\n\n")
            f.write("### Query Generation\n")
            f.write("- Tour-based queries with realistic time windows\n")
            f.write("- A* pathfinding for accurate travel time estimation\n")
            f.write("- Working hours: 9 AM - 7 PM (540-1140 minutes)\n\n")
            
            f.write("### Execution\n")
            f.write("- Each query run with 300s timeout\n")
            f.write("- Results parsed from solver output files\n")
            f.write("- Checkpoint-based resumability\n\n")
        
        self.logger.info(f"Report saved to: {report_file}")
    
    def run_full_pipeline(self):
        """Run the complete experiment pipeline."""
        if not self.state.get("start_time"):
            self.state["start_time"] = datetime.now().isoformat()
            self._save_state()
        
        self.logger.section("Starting Full Experiment Pipeline")
        
        # Step 1: Verify queries
        if not self.state.get("queries_verified"):
            if not self.verify_queries():
                return False
        else:
            self.logger.info("Queries already verified")
        
        # Step 2: Run algorithms
        self.run_algorithms()
        
        # Step 3: Generate charts
        self.generate_charts()
        
        # Step 4: Generate report
        self.generate_report()
        
        self.logger.section("Pipeline Complete!")
        
        end_time = datetime.now()
        start_time = datetime.fromisoformat(self.state["start_time"])
        elapsed = (end_time - start_time).total_seconds() / 3600
        
        self.logger.info(f"Total time: {elapsed:.2f} hours")
        
        return True
    
    def reset(self):
        """Reset pipeline state."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
        
        results_file = RESULTS_DIR / "experiment_results.json"
        if results_file.exists():
            results_file.unlink()
        
        self.state = self._load_state()
        print("Pipeline state reset.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="VRP-LU Experiment Pipeline")
    parser.add_argument("--status", action="store_true", help="Show pipeline status")
    parser.add_argument("--reset", action="store_true", help="Reset pipeline state")
    parser.add_argument("--charts-only", action="store_true", help="Only generate charts")
    parser.add_argument("--report-only", action="store_true", help="Only generate report")
    
    args = parser.parse_args()
    
    pipeline = ExperimentPipeline()
    
    if args.status:
        pipeline.show_status()
    elif args.reset:
        pipeline.reset()
    elif args.charts_only:
        pipeline.generate_charts()
    elif args.report_only:
        pipeline.generate_report()
    else:
        pipeline.run_full_pipeline()


if __name__ == "__main__":
    main()
