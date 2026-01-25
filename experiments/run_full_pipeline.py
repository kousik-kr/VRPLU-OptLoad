#!/usr/bin/env python3
"""
Full Experiment Pipeline Runner
===============================

Orchestrates the complete VRP-LU experiment workflow:
1. Phase C: Query Generation (tour-based) - if not already done
2. Phase D: Algorithm Execution
3. Phase E: Network Scalability Analysis
4. Phase F: Plot Generation
5. Phase G: Validation

Usage:
    python run_full_pipeline.py [--skip-generation] [--algorithms ALG1 ALG2 ...]
"""

import argparse
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add experiments directory to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from config import CONFIG, QUERIES_DIR, RESULTS_DIR, PLOTS_DIR, CHECKPOINTS_DIR
from utils.logger import get_logger, get_checkpoint_manager


def check_query_generation_complete():
    """Check if all queries have been generated."""
    expected_total = len(CONFIG.query_gen.N_VALUES) * CONFIG.query_gen.RUNS_PER_N
    
    actual_total = 0
    for n_val in CONFIG.query_gen.N_VALUES:
        n_dir = QUERIES_DIR / f"N_{n_val}"
        if n_dir.exists():
            actual_total += len(list(n_dir.glob("query_*.txt")))
    
    return actual_total >= expected_total, actual_total, expected_total


def run_phase_c(logger, checkpoint):
    """Phase C: Query Generation."""
    logger.section("Phase C: Query Generation")
    
    from tour_query_generator import TourBasedQueryGenerator, CONFIG as QUERY_CONFIG
    
    # Check if already complete
    complete, actual, expected = check_query_generation_complete()
    if complete:
        logger.info(f"Query generation already complete: {actual}/{expected}")
        checkpoint.complete_phase("phase_c")
        return True
    
    logger.info(f"Generating queries: {actual}/{expected} complete")
    
    generator = TourBasedQueryGenerator(QUERY_CONFIG)
    queries = generator.generate_all_queries(checkpoint)
    
    if len(queries) >= expected:
        logger.info(f"Query generation complete: {len(queries)} queries")
        checkpoint.complete_phase("phase_c")
        return True
    else:
        logger.warning(f"Query generation incomplete: {len(queries)}/{expected}")
        return False


def run_phase_d(logger, checkpoint, algorithms=None):
    """Phase D: Algorithm Execution."""
    logger.section("Phase D: Algorithm Execution")
    
    from phase_d_algorithm_execution import AlgorithmExecutor
    
    executor = AlgorithmExecutor()
    
    if algorithms:
        # Override default algorithms
        executor.algorithms = {k: v for k, v in executor.algorithms.items() 
                               if k.lower() in [a.lower() for a in algorithms]}
    
    results = executor.run_all_algorithms(checkpoint)
    
    if results:
        logger.info(f"Algorithm execution complete: {len(results)} results")
        checkpoint.complete_phase("phase_d")
        return True
    else:
        logger.error("Algorithm execution failed")
        return False


def run_phase_e(logger, checkpoint):
    """Phase E: Network Scalability Analysis."""
    logger.section("Phase E: Network Scalability Analysis")
    
    try:
        from phase_e_scalability import ScalabilityAnalyzer
        analyzer = ScalabilityAnalyzer()
        results = analyzer.run_scalability_tests(checkpoint)
        
        if results:
            logger.info(f"Scalability analysis complete")
            checkpoint.complete_phase("phase_e")
            return True
        else:
            logger.warning("Scalability analysis returned no results")
            return False
    except Exception as e:
        logger.error(f"Scalability analysis error: {e}")
        return False


def run_phase_f(logger, checkpoint):
    """Phase F: Plot Generation."""
    logger.section("Phase F: Plot Generation")
    
    try:
        from phase_f_plot_generation import PlotGenerator
        generator = PlotGenerator()
        plots = generator.generate_all_plots()
        
        if plots:
            logger.info(f"Generated {len(plots)} plots")
            checkpoint.complete_phase("phase_f")
            return True
        else:
            logger.warning("No plots generated")
            return False
    except Exception as e:
        logger.error(f"Plot generation error: {e}")
        return False


def run_phase_g(logger, checkpoint):
    """Phase G: Validation."""
    logger.section("Phase G: Validation")
    
    try:
        from phase_g_validation import SolutionValidator
        validator = SolutionValidator()
        report = validator.validate_all_results()
        
        if report:
            logger.info("Validation complete")
            checkpoint.complete_phase("phase_g")
            return True
        else:
            logger.warning("Validation returned no report")
            return False
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run full VRP-LU experiment pipeline"
    )
    parser.add_argument("--skip-generation", action="store_true",
                       help="Skip Phase C (query generation)")
    parser.add_argument("--skip-execution", action="store_true",
                       help="Skip Phase D (algorithm execution)")
    parser.add_argument("--skip-scalability", action="store_true",
                       help="Skip Phase E (scalability analysis)")
    parser.add_argument("--skip-plots", action="store_true",
                       help="Skip Phase F (plot generation)")
    parser.add_argument("--skip-validation", action="store_true",
                       help="Skip Phase G (validation)")
    parser.add_argument("--algorithms", nargs="+", default=None,
                       help="Specific algorithms to run (default: all)")
    parser.add_argument("--reset", action="store_true",
                       help="Reset all checkpoints")
    parser.add_argument("--phase", type=str, choices=['c', 'd', 'e', 'f', 'g'],
                       help="Run only specific phase")
    
    args = parser.parse_args()
    
    # Initialize
    logger = get_logger("pipeline")
    checkpoint = get_checkpoint_manager("full_pipeline")
    
    if args.reset:
        checkpoint.reset()
        logger.info("Checkpoints reset")
    
    logger.section("VRP-LU Experiment Pipeline")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    results = {}
    
    # Determine which phases to run
    if args.phase:
        phases = [args.phase]
    else:
        phases = ['c', 'd', 'e', 'f', 'g']
        if args.skip_generation:
            phases.remove('c')
        if args.skip_execution:
            phases.remove('d')
        if args.skip_scalability:
            phases.remove('e')
        if args.skip_plots:
            phases.remove('f')
        if args.skip_validation:
            phases.remove('g')
    
    # Run phases
    for phase in phases:
        phase_start = time.time()
        
        if phase == 'c':
            success = run_phase_c(logger, checkpoint)
        elif phase == 'd':
            success = run_phase_d(logger, checkpoint, args.algorithms)
        elif phase == 'e':
            success = run_phase_e(logger, checkpoint)
        elif phase == 'f':
            success = run_phase_f(logger, checkpoint)
        elif phase == 'g':
            success = run_phase_g(logger, checkpoint)
        else:
            continue
        
        phase_time = time.time() - phase_start
        results[f"phase_{phase}"] = {
            "success": success,
            "runtime_seconds": int(phase_time)
        }
        
        if not success:
            logger.warning(f"Phase {phase.upper()} did not complete successfully")
    
    # Summary
    total_time = time.time() - start_time
    
    logger.section("Pipeline Summary")
    for phase, result in results.items():
        status = "✓" if result["success"] else "✗"
        logger.info(f"  {phase}: {status} ({result['runtime_seconds']}s)")
    
    logger.info(f"Total runtime: {int(total_time)}s ({total_time/60:.1f} min)")
    
    # Save summary
    summary_file = RESULTS_DIR / "pipeline_summary.json"
    summary = {
        "timestamp": datetime.now().isoformat(),
        "phases": results,
        "total_runtime_seconds": int(total_time)
    }
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Summary saved to: {summary_file}")
    
    # Exit with appropriate code
    all_success = all(r["success"] for r in results.values())
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
