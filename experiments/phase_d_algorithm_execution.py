"""
Phase D: Algorithm Execution
============================
Runs multiple VRP-LU algorithms on generated queries and logs results.

Algorithms:
- Exact: Exact branch-and-bound solver
- ExactLIFO: LIFO stack-based solver
- Insertion: Greedy insertion heuristic
- OptLoad: Default clustering-based heuristic
- FoodMatch: FoodMatch-inspired solver
- Bazelmans: Bazelmans baseline

Metrics logged:
- LU cost, distance, served requests, runtime, Pareto size
"""

import subprocess
import os
import sys
import time
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import threading

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from experiments.config import (
    CONFIG, QUERIES_DIR, RESULTS_DIR, PROJECT_ROOT,
    CHECKPOINTS_DIR
)
from experiments.utils.logger import get_logger, get_checkpoint_manager


@dataclass
class AlgorithmResult:
    """Result from running an algorithm on a query."""
    query_id: str
    algorithm: str
    success: bool
    lu_cost: Optional[int] = None
    distance: Optional[float] = None
    served_requests: Optional[int] = None
    total_requests: Optional[int] = None
    runtime_ms: Optional[int] = None
    pareto_size: Optional[int] = None
    capacity: Optional[int] = None
    error_message: Optional[str] = None
    raw_output: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


class JavaRunner:
    """Handles Java compilation and execution."""
    
    def __init__(self, project_root: Path = PROJECT_ROOT):
        self.project_root = project_root
        self.src_dir = project_root / "src"
        self.target_dir = project_root / "target" / "classes"
        self.logger = get_logger("java_runner")
        self._compile_lock = threading.Lock()
        self._compiled = False
        
    def compile(self) -> bool:
        """Compile Java source files using javac directly."""
        
        # Only compile once per session
        if self._compiled:
            return True
            
        self.logger.info("Compiling Java sources...")
        
        with self._compile_lock:
            try:
                # Always use javac for the flat src/ directory structure
                java_files = list(self.src_dir.glob("*.java"))
                if not java_files:
                    self.logger.error("No Java files found in src directory")
                    return False
                
                self.target_dir.mkdir(parents=True, exist_ok=True)
                
                cmd = [
                    "javac", "-d", str(self.target_dir),
                    "-sourcepath", str(self.src_dir)
                ] + [str(f) for f in java_files]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    self.logger.info("Compilation successful")
                    self._compiled = True
                    return True
                else:
                    self.logger.error(f"Compilation failed: {result.stderr}")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Compilation error: {e}")
                return False
    
    def run_solver(self, query_file: Path, solver_flag: str, 
                   timeout_seconds: int = 600) -> Tuple[bool, str, int]:
        """
        Run a VRP-LU solver on a query file.
        
        Returns:
            Tuple[bool, str, int]: (success, output, runtime_ms)
        """
        
        import shutil
        
        start_time = time.time()
        
        try:
            # The Java program expects Query_<vertex_count>.txt in the working directory
            # Copy the query file to the expected location
            vertex_count = 285050  # Hardcoded for this dataset
            expected_query_path = self.project_root / f"Query_{vertex_count}.txt"
            
            # Backup existing query file if present
            backup_path = None
            if expected_query_path.exists():
                backup_path = self.project_root / f"Query_{vertex_count}.txt.bak"
                shutil.copy(expected_query_path, backup_path)
            
            # Copy our query file to expected location
            shutil.copy(query_file, expected_query_path)
            
            # Determine classpath
            classpath = str(self.target_dir)
            
            # Check if compiled classes exist
            main_class = self.target_dir / "VRPLoadingUnloadingMain.class"
            if not main_class.exists():
                if not self.compile():
                    return False, "Compilation failed", 0
            
            # Run the Java program
            cmd = [
                "java",
                "-Xmx8g", "-Xms2g",
                "-cp", classpath,
                "VRPLoadingUnloadingMain",
                str(self.project_root),  # Working directory with dataset
                solver_flag
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=self.project_root
            )
            
            end_time = time.time()
            runtime_ms = int((end_time - start_time) * 1000)
            
            # Restore backup if it existed
            if backup_path and backup_path.exists():
                shutil.move(backup_path, expected_query_path)
            else:
                # Remove temporary query file
                if expected_query_path.exists():
                    expected_query_path.unlink()
            
            output = result.stdout + result.stderr
            
            # Read the output file to get results
            output_prefix = self._get_output_prefix(solver_flag)
            output_file = self.project_root / f"{output_prefix}{vertex_count}.txt"
            if output_file.exists():
                with open(output_file, 'r') as f:
                    output += f"\n--- OUTPUT FILE ---\n" + f.read()
            
            success = result.returncode == 0
            
            return success, output, runtime_ms
            
        except subprocess.TimeoutExpired:
            end_time = time.time()
            runtime_ms = int((end_time - start_time) * 1000)
            return False, f"Timeout after {timeout_seconds}s", runtime_ms
            
        except Exception as e:
            end_time = time.time()
            runtime_ms = int((end_time - start_time) * 1000)
            return False, str(e), runtime_ms
    
    def _get_output_prefix(self, solver_flag: str) -> str:
        """Get output file prefix for a solver."""
        # Maps from Java SolverType enum
        prefixes = {
            "--exact": "OutputExact_",
            "--lifostack": "OutputLifo_",
            "--insertion": "OutputInsertion_",
            "--cluster": "Output_",
            "--foodmatch": "OutputFoodMatch_",
            "--bazelmans": "OutputBazelmans_",
        }
        return prefixes.get(solver_flag.lower(), "Output_")


class OutputParser:
    """Parses VRP-LU solver output to extract metrics."""
    
    @staticmethod
    def parse_output(output: str, algorithm: str, query_id: str) -> AlgorithmResult:
        """Parse solver output and extract metrics."""
        
        result = AlgorithmResult(
            query_id=query_id,
            algorithm=algorithm,
            success=False,
            raw_output=output[:5000]  # Truncate for storage
        )
        
        try:
            # The Java solver output format in the output file is:
            # [Route...]\tNumber of Successful Requests:X\tL-U Cost:Y\tDistance:Z
            # <runtime_seconds>
            
            # Pattern from actual Java output file
            # Example: "[Depot:111750,...]	Number of Successful Requests:5	L-U Cost:10	Distance:12345.6"
            output_file_match = re.search(
                r"Number of Successful Requests:(\d+)\s*L-U Cost:(\d+)\s*Distance:([\d.]+)",
                output
            )
            if output_file_match:
                result.served_requests = int(output_file_match.group(1))
                result.lu_cost = int(output_file_match.group(2))
                result.distance = float(output_file_match.group(3))
                result.success = True
            
            # Extract runtime from Java console output
            # Format: "Finished processing query 1 in 10046 ms"
            time_match = re.search(r"in\s*(\d+)\s*ms", output)
            if time_match:
                result.runtime_ms = int(time_match.group(1))
            
            # Also check for runtime in seconds at end of output file
            # Format: "10.046" (seconds on its own line after Distance)
            runtime_sec_match = re.search(r"Distance:[\d.]+\n([\d.]+)\s*$", output, re.MULTILINE)
            if runtime_sec_match and not result.runtime_ms:
                result.runtime_ms = int(float(runtime_sec_match.group(1)) * 1000)
            
            # Extract capacity from log output
            # Format: "Set capacity for query 1 to 10"
            cap_match = re.search(r"capacity.*to\s*(\d+)", output, re.IGNORECASE)
            if cap_match:
                result.capacity = int(cap_match.group(1))
            
            # Count services added
            # Format: "Added service X to query Y"
            services_added = len(re.findall(r"Added service \d+", output))
            if services_added:
                result.total_requests = services_added
            
            # Check for errors
            if "Exception" in output or "Error" in output:
                error_match = re.search(r"(Exception|Error)[^\n]*", output)
                if error_match:
                    result.error_message = error_match.group(0)[:200]
                    result.success = False
            
            # If no solution found
            if "No feasible solution" in output:
                result.success = True  # Algorithm ran successfully, just no solution
                result.served_requests = 0
                result.lu_cost = 0
                result.distance = 0.0
                
        except Exception as e:
            result.error_message = f"Parse error: {str(e)}"
        
        return result


class AlgorithmExecutor:
    """
    Executes VRP-LU algorithms on queries with progress tracking.
    """
    
    def __init__(self, config=None):
        self.config = config or CONFIG.algorithm
        self.logger = get_logger("algorithm_executor")
        self.java_runner = JavaRunner()
        self.output_parser = OutputParser()
        
    def prepare_query_file(self, query_path: Path, n_requests: int) -> Path:
        """
        Prepare query file in the format expected by the Java solver.
        The solver expects Query_<vertex_count>.txt in the working directory.
        """
        
        # Read the query content
        with open(query_path, 'r') as f:
            content = f.read()
        
        # Write to expected location
        expected_file = PROJECT_ROOT / f"Query_{285050}.txt"
        with open(expected_file, 'w') as f:
            f.write(content)
        
        return expected_file
    
    def run_single_algorithm(self, query_path: Path, algorithm: str,
                             query_id: str) -> AlgorithmResult:
        """Run a single algorithm on a query."""
        
        solver_flag = self.config.SOLVERS.get(algorithm)
        if not solver_flag:
            return AlgorithmResult(
                query_id=query_id,
                algorithm=algorithm,
                success=False,
                error_message=f"Unknown algorithm: {algorithm}"
            )
        
        # Prepare the query file
        self.prepare_query_file(query_path, 0)  # n_requests not needed here
        
        # Run the solver
        success, output, runtime_ms = self.java_runner.run_solver(
            query_path, 
            solver_flag,
            timeout_seconds=self.config.TIMEOUT_SECONDS
        )
        
        # Parse the output
        result = self.output_parser.parse_output(output, algorithm, query_id)
        result.runtime_ms = runtime_ms
        
        return result
    
    def run_all_algorithms(self, query_path: Path, query_id: str,
                          algorithms: List[str] = None) -> Dict[str, AlgorithmResult]:
        """Run all specified algorithms on a query."""
        
        if algorithms is None:
            algorithms = list(self.config.SOLVERS.keys())
        
        results = {}
        for algorithm in algorithms:
            self.logger.debug(f"Running {algorithm} on {query_id}")
            result = self.run_single_algorithm(query_path, algorithm, query_id)
            results[algorithm] = result
            
            if result.success:
                self.logger.debug(
                    f"  {algorithm}: {result.served_requests} served, "
                    f"LU={result.lu_cost}, dist={result.distance:.2f}, "
                    f"time={result.runtime_ms}ms"
                )
            else:
                self.logger.warning(f"  {algorithm} failed: {result.error_message}")
        
        return results
    
    def execute_all_experiments(self, checkpoint_manager=None) -> Dict:
        """
        Execute all algorithm experiments according to design.
        
        For each query:
            For each algorithm:
                Run and log results
        """
        
        self.logger.section("Phase D: Algorithm Execution")
        
        # Ensure Java is compiled
        if not self.java_runner.compile():
            self.logger.error("Failed to compile Java sources")
            return {}
        
        # Load query index
        query_index_file = QUERIES_DIR / "query_index.json"
        if not query_index_file.exists():
            self.logger.error("Query index not found. Run Phase C first.")
            return {}
        
        with open(query_index_file, 'r') as f:
            query_index = json.load(f)
        
        all_results = {}
        total_experiments = len(query_index) * len(self.config.SOLVERS)
        completed = 0
        
        algorithms = list(self.config.SOLVERS.keys())
        
        for query_key, query_path in query_index.items():
            query_path = Path(query_path)
            
            if not query_path.exists():
                self.logger.warning(f"Query file not found: {query_path}")
                continue
            
            for algorithm in algorithms:
                experiment_key = f"{query_key}_{algorithm}"
                
                # Check checkpoint
                if checkpoint_manager and checkpoint_manager.is_item_completed(f"algo_{experiment_key}"):
                    self.logger.debug(f"Skipping {experiment_key} (already completed)")
                    completed += 1
                    continue
                
                # Run the algorithm
                self.logger.debug(f"Running {experiment_key}")
                result = self.run_single_algorithm(query_path, algorithm, query_key)
                
                all_results[experiment_key] = result.to_dict()
                
                # Update checkpoint
                if checkpoint_manager:
                    checkpoint_manager.mark_item_completed(f"algo_{experiment_key}")
                
                completed += 1
                
                if completed % 20 == 0:
                    self.logger.info(f"Progress: {completed}/{total_experiments} experiments")
                    
                    # Save intermediate results
                    self._save_results(all_results)
        
        # Save final results
        self._save_results(all_results)
        
        self.logger.info(f"Algorithm execution complete. Total experiments: {len(all_results)}")
        
        if checkpoint_manager:
            checkpoint_manager.complete_phase("phase_d_algorithm_execution")
        
        return all_results
    
    def _save_results(self, results: Dict):
        """Save results to file."""
        results_file = RESULTS_DIR / "algorithm_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)


def main():
    """Run algorithm execution as standalone script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Execute VRP-LU algorithms on queries")
    parser.add_argument("--algorithms", type=str, nargs="+", default=None,
                       help="Specific algorithms to run")
    parser.add_argument("--query", type=str, default=None,
                       help="Run on specific query (e.g., N10_R1)")
    parser.add_argument("--reset", action="store_true",
                       help="Reset checkpoint and start fresh")
    parser.add_argument("--timeout", type=int, default=600,
                       help="Timeout per query in seconds")
    
    args = parser.parse_args()
    
    # Update config
    if args.timeout:
        CONFIG.algorithm.TIMEOUT_SECONDS = args.timeout
    
    # Initialize checkpoint manager
    checkpoint = get_checkpoint_manager("algorithm_execution")
    
    if args.reset:
        checkpoint.reset()
        print("Checkpoint reset. Starting fresh.")
    
    # Check if already completed
    if checkpoint.is_phase_completed("phase_d_algorithm_execution"):
        print("Algorithm execution already completed. Use --reset to rerun.")
        return
    
    # Run execution
    executor = AlgorithmExecutor()
    
    if args.query:
        # Run on specific query
        query_path = QUERIES_DIR / args.query.replace("_R", "/query_").replace("N", "N_") + ".txt"
        if not query_path.exists():
            print(f"Query not found: {query_path}")
            return
        
        results = executor.run_all_algorithms(
            query_path, 
            args.query,
            args.algorithms
        )
        
        for algo, result in results.items():
            print(f"\n{algo}:")
            print(f"  Success: {result.success}")
            print(f"  Served: {result.served_requests}/{result.total_requests}")
            print(f"  LU Cost: {result.lu_cost}")
            print(f"  Distance: {result.distance}")
            print(f"  Runtime: {result.runtime_ms}ms")
    else:
        # Run all experiments
        results = executor.execute_all_experiments(checkpoint)
        print(f"\nCompleted {len(results)} experiments")
        print(f"Results saved to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
