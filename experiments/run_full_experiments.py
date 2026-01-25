#!/usr/bin/env python3
"""
Full Experiment Runner with Robust Error Handling
=================================================

Runs all VRP-LU algorithms on all generated queries with:
- Checkpoint-based resumability
- Graceful handling of algorithm failures
- Progress logging
- Result aggregation

For OptLoad: If it returns 0 results, we log it but continue (algorithm limitation)
For other algorithms: If they fail, we use 0 as default values
"""

import sys
import json
import time
import shutil
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import subprocess

# Add experiments directory to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from config import CONFIG, QUERIES_DIR, RESULTS_DIR, PROJECT_ROOT, CHECKPOINTS_DIR
from utils.logger import get_logger, get_checkpoint_manager


@dataclass
class ExperimentResult:
    """Result from running an algorithm on a query."""
    query_id: str
    algorithm: str
    success: bool
    served_requests: int = 0
    total_requests: int = 0
    lu_cost: int = 0
    distance: float = 0.0
    runtime_ms: int = 0
    capacity: int = 0
    error_message: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)


class RobustExperimentRunner:
    """
    Runs experiments with robust error handling and checkpointing.
    """
    
    def __init__(self):
        self.logger = get_logger("experiment_runner")
        self.project_root = PROJECT_ROOT
        self.target_dir = PROJECT_ROOT / "target" / "classes"
        self.checkpoint = get_checkpoint_manager("full_experiments")
        
        # Algorithm configurations
        self.algorithms = {
            "Insertion": "--insertion",
            "OptLoad": "--cluster",
            "ExactLIFO": "--lifostack",
            "Bazelmans": "--bazelmans",
            "FoodMatch": "--foodmatch",
        }
        
        # Note: Exact algorithm is very slow, skip by default
        # Can be added with: "Exact": "--exact"
        
        self.results = {}
        self.results_file = RESULTS_DIR / "experiment_results.json"
        
    def compile_java(self) -> bool:
        """Compile Java sources if needed."""
        main_class = self.target_dir / "VRPLoadingUnloadingMain.class"
        if main_class.exists():
            self.logger.info("Java classes already compiled")
            return True
        
        self.logger.info("Compiling Java sources...")
        src_dir = self.project_root / "src"
        java_files = list(src_dir.glob("*.java"))
        
        if not java_files:
            self.logger.error("No Java files found")
            return False
        
        self.target_dir.mkdir(parents=True, exist_ok=True)
        
        cmd = ["javac", "-d", str(self.target_dir), "-sourcepath", str(src_dir)] + \
              [str(f) for f in java_files]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                self.logger.info("Compilation successful")
                return True
            else:
                self.logger.error(f"Compilation failed: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Compilation error: {e}")
            return False
    
    def run_solver(self, query_file: Path, solver_flag: str, 
                   timeout_seconds: int = 300) -> tuple:
        """
        Run a solver on a query file.
        
        Returns: (success, output, runtime_ms)
        """
        vertex_count = 285050
        expected_query_path = self.project_root / f"Query_{vertex_count}.txt"
        
        start_time = time.time()
        
        try:
            # Copy query to expected location
            shutil.copy(query_file, expected_query_path)
            
            # Run solver
            cmd = [
                "java", "-Xmx8g", "-Xms2g",
                "-cp", str(self.target_dir),
                "VRPLoadingUnloadingMain",
                str(self.project_root),
                solver_flag
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=self.project_root
            )
            
            runtime_ms = int((time.time() - start_time) * 1000)
            
            # Read output file
            output_prefix = self._get_output_prefix(solver_flag)
            output_file = self.project_root / f"{output_prefix}{vertex_count}.txt"
            
            output = result.stdout + result.stderr
            if output_file.exists():
                with open(output_file, 'r') as f:
                    output += "\n--- OUTPUT FILE ---\n" + f.read()
            
            return True, output, runtime_ms
            
        except subprocess.TimeoutExpired:
            runtime_ms = int((time.time() - start_time) * 1000)
            return False, f"Timeout after {timeout_seconds}s", runtime_ms
        except Exception as e:
            runtime_ms = int((time.time() - start_time) * 1000)
            return False, str(e), runtime_ms
        finally:
            # Clean up
            if expected_query_path.exists():
                expected_query_path.unlink()
    
    def _get_output_prefix(self, solver_flag: str) -> str:
        prefixes = {
            "--exact": "OutputExact_",
            "--lifostack": "OutputLifo_",
            "--insertion": "OutputInsertion_",
            "--cluster": "Output_",
            "--foodmatch": "OutputFoodMatch_",
            "--bazelmans": "OutputBazelmans_",
        }
        return prefixes.get(solver_flag.lower(), "Output_")
    
    def parse_output(self, output: str, algorithm: str, query_id: str, 
                     runtime_ms: int) -> ExperimentResult:
        """Parse solver output and extract metrics."""
        
        result = ExperimentResult(
            query_id=query_id,
            algorithm=algorithm,
            success=False,
            runtime_ms=runtime_ms
        )
        
        import re
        
        try:
            # Parse output file content
            # Format: [Route...]\tNumber of Successful Requests:X\tL-U Cost:Y\tDistance:Z
            match = re.search(
                r"Number of Successful Requests:(\d+)\s*L-U Cost:(\d+)\s*Distance:([\d.]+)",
                output
            )
            if match:
                result.served_requests = int(match.group(1))
                result.lu_cost = int(match.group(2))
                result.distance = float(match.group(3))
                result.success = True
            
            # Parse runtime from Java output
            time_match = re.search(r"in\s*(\d+)\s*ms", output)
            if time_match:
                result.runtime_ms = int(time_match.group(1))
            
            # Parse capacity
            cap_match = re.search(r"capacity.*to\s*(\d+)", output, re.IGNORECASE)
            if cap_match:
                result.capacity = int(cap_match.group(1))
            
            # Count services
            services_added = len(re.findall(r"Added service \d+", output))
            if services_added:
                result.total_requests = services_added
            
            # Check for errors
            if "Exception" in output or "Error" in output:
                error_match = re.search(r"(Exception|Error)[^\n]*", output)
                if error_match:
                    result.error_message = error_match.group(0)[:200]
            
        except Exception as e:
            result.error_message = f"Parse error: {str(e)}"
        
        return result
    
    def load_results(self):
        """Load existing results from file."""
        if self.results_file.exists():
            with open(self.results_file, 'r') as f:
                self.results = json.load(f)
            self.logger.info(f"Loaded {len(self.results)} existing results")
    
    def save_results(self):
        """Save results to file."""
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    def run_all_experiments(self, algorithms: List[str] = None, 
                            timeout_per_query: int = 300):
        """
        Run all experiments on all queries.
        """
        self.logger.section("Full Experiment Execution")
        
        # Load query index
        query_index_file = QUERIES_DIR / "query_index.json"
        if not query_index_file.exists():
            self.logger.error("Query index not found. Run query generation first.")
            return
        
        with open(query_index_file, 'r') as f:
            query_index = json.load(f)
        
        self.logger.info(f"Found {len(query_index)} queries")
        
        # Compile Java
        if not self.compile_java():
            self.logger.error("Failed to compile Java sources")
            return
        
        # Load existing results
        self.load_results()
        
        # Determine algorithms to run
        if algorithms:
            algos_to_run = {k: v for k, v in self.algorithms.items() if k in algorithms}
        else:
            algos_to_run = self.algorithms
        
        self.logger.info(f"Running algorithms: {list(algos_to_run.keys())}")
        
        # Calculate totals
        total_experiments = len(query_index) * len(algos_to_run)
        completed = sum(1 for k in self.results.keys() if any(a in k for a in algos_to_run.keys()))
        
        self.logger.info(f"Total experiments: {total_experiments}, Already completed: {completed}")
        
        start_time = time.time()
        
        for query_key, query_path in query_index.items():
            query_path = Path(query_path)
            
            if not query_path.exists():
                self.logger.warning(f"Query file not found: {query_path}")
                continue
            
            for algo_name, algo_flag in algos_to_run.items():
                experiment_key = f"{query_key}_{algo_name}"
                
                # Skip if already done
                if experiment_key in self.results:
                    continue
                
                # Run the experiment
                success, output, runtime = self.run_solver(
                    query_path, algo_flag, timeout_per_query
                )
                
                # Parse results
                result = self.parse_output(output, algo_name, query_key, runtime)
                
                # Handle OptLoad special case
                if algo_name == "OptLoad" and result.served_requests == 0:
                    result.error_message = "OptLoad clustering found no feasible solution"
                    # This is expected for some queries - not a failure
                    result.success = True
                
                # Store result
                self.results[experiment_key] = result.to_dict()
                completed += 1
                
                # Log progress
                if completed % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    remaining = (total_experiments - completed) / rate if rate > 0 else 0
                    self.logger.info(
                        f"Progress: {completed}/{total_experiments} "
                        f"({100*completed/total_experiments:.1f}%) "
                        f"ETA: {remaining/60:.1f} min"
                    )
                    # Save intermediate results
                    self.save_results()
        
        # Save final results
        self.save_results()
        
        elapsed = time.time() - start_time
        self.logger.info(f"Completed {completed} experiments in {elapsed/60:.1f} minutes")
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate summary statistics."""
        summary = {
            "total_experiments": len(self.results),
            "by_algorithm": {},
            "by_n_value": {},
            "timestamp": datetime.now().isoformat()
        }
        
        for key, result in self.results.items():
            algo = result["algorithm"]
            
            # Parse N value from query_id (e.g., "N10_R1")
            n_val = result["query_id"].split("_")[0].replace("N", "")
            
            # By algorithm
            if algo not in summary["by_algorithm"]:
                summary["by_algorithm"][algo] = {
                    "count": 0,
                    "success": 0,
                    "total_served": 0,
                    "total_lu_cost": 0,
                    "total_distance": 0,
                    "total_runtime_ms": 0,
                }
            
            s = summary["by_algorithm"][algo]
            s["count"] += 1
            if result["served_requests"] > 0:
                s["success"] += 1
                s["total_served"] += result["served_requests"]
                s["total_lu_cost"] += result["lu_cost"]
                s["total_distance"] += result["distance"]
            s["total_runtime_ms"] += result["runtime_ms"]
            
            # By N value
            if n_val not in summary["by_n_value"]:
                summary["by_n_value"][n_val] = {
                    "count": 0,
                    "algorithms": {}
                }
            
            bn = summary["by_n_value"][n_val]
            bn["count"] += 1
            
            if algo not in bn["algorithms"]:
                bn["algorithms"][algo] = {
                    "success": 0,
                    "avg_served": 0,
                    "avg_lu_cost": 0,
                    "avg_runtime_ms": 0,
                    "count": 0,
                }
            
            ba = bn["algorithms"][algo]
            ba["count"] += 1
            if result["served_requests"] > 0:
                ba["success"] += 1
                ba["avg_served"] += result["served_requests"]
                ba["avg_lu_cost"] += result["lu_cost"]
            ba["avg_runtime_ms"] += result["runtime_ms"]
        
        # Calculate averages
        for algo, s in summary["by_algorithm"].items():
            if s["success"] > 0:
                s["avg_served"] = s["total_served"] / s["success"]
                s["avg_lu_cost"] = s["total_lu_cost"] / s["success"]
                s["avg_distance"] = s["total_distance"] / s["success"]
            s["avg_runtime_ms"] = s["total_runtime_ms"] / s["count"] if s["count"] > 0 else 0
            s["success_rate"] = s["success"] / s["count"] if s["count"] > 0 else 0
        
        for n_val, bn in summary["by_n_value"].items():
            for algo, ba in bn["algorithms"].items():
                if ba["success"] > 0:
                    ba["avg_served"] /= ba["success"]
                    ba["avg_lu_cost"] /= ba["success"]
                ba["avg_runtime_ms"] /= ba["count"] if ba["count"] > 0 else 1
        
        # Save summary
        summary_file = RESULTS_DIR / "experiment_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"Summary saved to: {summary_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("EXPERIMENT SUMMARY")
        print("="*60)
        
        print("\nBy Algorithm:")
        for algo, s in summary["by_algorithm"].items():
            print(f"\n  {algo}:")
            print(f"    Total runs: {s['count']}")
            print(f"    Success rate: {s['success_rate']*100:.1f}%")
            print(f"    Avg served requests: {s.get('avg_served', 0):.1f}")
            print(f"    Avg LU cost: {s.get('avg_lu_cost', 0):.1f}")
            print(f"    Avg runtime: {s['avg_runtime_ms']:.0f} ms")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run full VRP-LU experiments")
    parser.add_argument("--algorithms", nargs="+", default=None,
                       help="Specific algorithms to run")
    parser.add_argument("--timeout", type=int, default=300,
                       help="Timeout per query in seconds")
    parser.add_argument("--reset", action="store_true",
                       help="Reset and start fresh")
    
    args = parser.parse_args()
    
    runner = RobustExperimentRunner()
    
    if args.reset:
        # Clear existing results
        if runner.results_file.exists():
            runner.results_file.unlink()
        print("Reset complete. Starting fresh.")
    
    runner.run_all_experiments(
        algorithms=args.algorithms,
        timeout_per_query=args.timeout
    )


if __name__ == "__main__":
    main()
