#!/usr/bin/env python3
"""
VRPLU-OptLoad Experiment Runner
===============================

Main orchestration script that runs all experiment phases:
  - Phase C: Query Generation
  - Phase D: Algorithm Execution
  - Phase E: Network Scalability
  - Phase F: Plot Generation
  - Phase G: Sanity Validation

Features:
  - Checkpoint/resume support for each phase
  - Comprehensive logging
  - Progress tracking
  - Error recovery

Usage:
    python run_experiments.py                    # Run all phases
    python run_experiments.py --phase C D       # Run specific phases
    python run_experiments.py --reset           # Start fresh
    python run_experiments.py --status          # Check progress
"""

import argparse
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.config import (
    CONFIG, RESULTS_DIR, LOGS_DIR, CHECKPOINTS_DIR, PLOTS_DIR, QUERIES_DIR
)
from experiments.utils.logger import get_logger, get_checkpoint_manager

# Phase imports
from experiments.phase_c_query_generation import QueryGenerator
from experiments.phase_d_algorithm_execution import AlgorithmExecutor
from experiments.phase_e_scalability import ScalabilityExperiment
from experiments.phase_f_plot_generation import PlotGenerator
from experiments.phase_g_validation import SolutionValidator


class ExperimentRunner:
    """
    Main experiment orchestrator with checkpointing and logging.
    """
    
    PHASES = {
        'C': ('Query Generation', 'phase_c_query_generation'),
        'D': ('Algorithm Execution', 'phase_d_algorithm_execution'),
        'E': ('Network Scalability', 'phase_e_scalability'),
        'F': ('Plot Generation', 'phase_f_plot_generation'),
        'G': ('Sanity Validation', 'phase_g_validation'),
    }
    
    def __init__(self, experiment_name: str = "vrplu_experiment"):
        self.experiment_name = experiment_name
        self.logger = get_logger(experiment_name)
        self.checkpoint = get_checkpoint_manager(experiment_name)
        self.start_time = None
        
    def print_banner(self):
        """Print experiment banner."""
        banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║            VRPLU-OptLoad Experiment Framework                    ║
║            ===================================                   ║
║                                                                  ║
║   Phase C: Query Generation                                      ║
║   Phase D: Algorithm Execution                                   ║
║   Phase E: Network Scalability                                   ║
║   Phase F: Plot Generation                                       ║
║   Phase G: Sanity Validation                                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
        print(banner)
        self.logger.info("=" * 60)
        self.logger.info(f"Starting experiment: {self.experiment_name}")
        self.logger.info(f"Timestamp: {datetime.now().isoformat()}")
        self.logger.info("=" * 60)
    
    def show_status(self):
        """Display current experiment status."""
        summary = self.checkpoint.get_summary()
        
        print("\n" + "=" * 50)
        print("  EXPERIMENT STATUS")
        print("=" * 50)
        print(f"\nExperiment: {summary['experiment']}")
        print(f"Started: {summary['started']}")
        print(f"Last Updated: {summary['last_updated']}")
        print(f"Current Phase: {summary['current_phase']}")
        print(f"\nCompleted Phases: {', '.join(summary['completed_phases']) or 'None'}")
        print(f"Items Completed: {summary['items_completed']}")
        print(f"Items Failed: {summary['items_failed']}")
        
        # Check phase status
        print("\nPhase Status:")
        for phase_key, (phase_name, checkpoint_key) in self.PHASES.items():
            completed = self.checkpoint.is_phase_completed(checkpoint_key)
            status = "✓ Complete" if completed else "○ Pending"
            print(f"  Phase {phase_key} ({phase_name}): {status}")
        
        print("=" * 50 + "\n")
    
    def run_phase_c(self) -> bool:
        """Run Phase C: Query Generation."""
        phase_key = 'phase_c_query_generation'
        
        if self.checkpoint.is_phase_completed(phase_key):
            self.logger.info("Phase C already completed. Skipping.")
            return True
        
        self.checkpoint.set_phase(phase_key)
        
        try:
            generator = QueryGenerator()
            queries = generator.generate_all_queries(self.checkpoint)
            
            if queries:
                self.checkpoint.complete_phase(phase_key)
                self.logger.info(f"Phase C complete. Generated {len(queries)} queries.")
                return True
            else:
                self.logger.error("Phase C failed: No queries generated.")
                return False
                
        except Exception as e:
            self.logger.error(f"Phase C error: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def run_phase_d(self) -> bool:
        """Run Phase D: Algorithm Execution."""
        phase_key = 'phase_d_algorithm_execution'
        
        if self.checkpoint.is_phase_completed(phase_key):
            self.logger.info("Phase D already completed. Skipping.")
            return True
        
        # Check prerequisite
        if not self.checkpoint.is_phase_completed('phase_c_query_generation'):
            self.logger.error("Phase D requires Phase C to be completed first.")
            return False
        
        self.checkpoint.set_phase(phase_key)
        
        try:
            executor = AlgorithmExecutor()
            results = executor.execute_all_experiments(self.checkpoint)
            
            if results:
                self.checkpoint.complete_phase(phase_key)
                self.logger.info(f"Phase D complete. Ran {len(results)} experiments.")
                return True
            else:
                self.logger.warning("Phase D completed with no results.")
                return True  # Not necessarily a failure
                
        except Exception as e:
            self.logger.error(f"Phase D error: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def run_phase_e(self) -> bool:
        """Run Phase E: Network Scalability."""
        phase_key = 'phase_e_scalability'
        
        if self.checkpoint.is_phase_completed(phase_key):
            self.logger.info("Phase E already completed. Skipping.")
            return True
        
        self.checkpoint.set_phase(phase_key)
        
        try:
            experiment = ScalabilityExperiment()
            results = experiment.run_scalability_experiments(self.checkpoint)
            
            self.checkpoint.complete_phase(phase_key)
            self.logger.info(f"Phase E complete. Ran {len(results)} scalability experiments.")
            return True
            
        except Exception as e:
            self.logger.error(f"Phase E error: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def run_phase_f(self) -> bool:
        """Run Phase F: Plot Generation."""
        phase_key = 'phase_f_plot_generation'
        
        # Phase F can be rerun without reset
        self.checkpoint.set_phase(phase_key)
        
        try:
            generator = PlotGenerator()
            generator.generate_all_plots()
            
            self.checkpoint.complete_phase(phase_key)
            self.logger.info("Phase F complete. Plots generated.")
            return True
            
        except Exception as e:
            self.logger.error(f"Phase F error: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def run_phase_g(self) -> bool:
        """Run Phase G: Sanity Validation."""
        phase_key = 'phase_g_validation'
        
        # Check prerequisite
        if not self.checkpoint.is_phase_completed('phase_d_algorithm_execution'):
            self.logger.warning("Phase G: No results to validate. Running anyway for partial validation.")
        
        self.checkpoint.set_phase(phase_key)
        
        try:
            validator = SolutionValidator()
            validations = validator.validate_all_results()
            
            # Count valid/invalid
            valid_count = sum(1 for v in validations.values() if v.get('is_valid'))
            total_count = len(validations)
            
            self.checkpoint.complete_phase(phase_key)
            self.logger.info(f"Phase G complete. Validated {valid_count}/{total_count} solutions.")
            return True
            
        except Exception as e:
            self.logger.error(f"Phase G error: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def run_phases(self, phases: List[str] = None):
        """
        Run specified phases (or all phases if none specified).
        
        Args:
            phases: List of phase letters (e.g., ['C', 'D', 'F'])
        """
        self.print_banner()
        self.start_time = time.time()
        
        # Default to all phases
        if phases is None:
            phases = list(self.PHASES.keys())
        
        phase_runners = {
            'C': self.run_phase_c,
            'D': self.run_phase_d,
            'E': self.run_phase_e,
            'F': self.run_phase_f,
            'G': self.run_phase_g,
        }
        
        success = True
        
        for phase in phases:
            phase = phase.upper()
            if phase not in phase_runners:
                self.logger.warning(f"Unknown phase: {phase}")
                continue
            
            phase_name, _ = self.PHASES[phase]
            self.logger.section(f"Phase {phase}: {phase_name}")
            
            phase_start = time.time()
            result = phase_runners[phase]()
            phase_elapsed = time.time() - phase_start
            
            if result:
                self.logger.info(f"Phase {phase} completed in {phase_elapsed:.1f}s")
            else:
                self.logger.error(f"Phase {phase} failed after {phase_elapsed:.1f}s")
                success = False
                # Don't stop on failure - continue with remaining phases
        
        # Final summary
        total_elapsed = time.time() - self.start_time
        self.logger.section("EXPERIMENT COMPLETE")
        self.logger.info(f"Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")
        
        self.show_status()
        
        return success
    
    def reset(self, phases: List[str] = None):
        """
        Reset checkpoint for specified phases (or all if none specified).
        
        Args:
            phases: List of phase letters to reset
        """
        if phases is None:
            self.checkpoint.reset()
            self.logger.info("All checkpoints reset.")
        else:
            for phase in phases:
                phase = phase.upper()
                if phase in self.PHASES:
                    _, phase_key = self.PHASES[phase]
                    if phase_key in self.checkpoint.state.get("completed_phases", []):
                        self.checkpoint.state["completed_phases"].remove(phase_key)
                    self.logger.info(f"Reset Phase {phase}")
            self.checkpoint.save()


def main():
    parser = argparse.ArgumentParser(
        description="VRPLU-OptLoad Experiment Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_experiments.py                    # Run all phases
  python run_experiments.py --phase C D       # Run Phase C and D only
  python run_experiments.py --phase F         # Regenerate plots only
  python run_experiments.py --status          # Check progress
  python run_experiments.py --reset           # Start fresh
  python run_experiments.py --reset --phase D # Reset only Phase D
        """
    )
    
    parser.add_argument(
        '--phase', '-p',
        nargs='+',
        choices=['C', 'D', 'E', 'F', 'G', 'c', 'd', 'e', 'f', 'g'],
        help='Specific phases to run (default: all)'
    )
    
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Show experiment status and exit'
    )
    
    parser.add_argument(
        '--reset', '-r',
        action='store_true',
        help='Reset checkpoints before running'
    )
    
    parser.add_argument(
        '--name', '-n',
        type=str,
        default='vrplu_experiment',
        help='Experiment name for checkpoints (default: vrplu_experiment)'
    )
    
    parser.add_argument(
        '--n-values',
        type=int,
        nargs='+',
        help='Override N values for query generation (e.g., --n-values 10 20 40)'
    )
    
    parser.add_argument(
        '--runs',
        type=int,
        help='Override number of runs per N value'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        help='Override algorithm timeout in seconds'
    )
    
    args = parser.parse_args()
    
    # Update config from args
    if args.n_values:
        CONFIG.query.N_VALUES = args.n_values
    if args.runs:
        CONFIG.query.RUNS_PER_N = args.runs
    if args.timeout:
        CONFIG.algorithm.TIMEOUT_SECONDS = args.timeout
    
    # Create runner
    runner = ExperimentRunner(experiment_name=args.name)
    
    # Handle status request
    if args.status:
        runner.show_status()
        return
    
    # Handle reset
    if args.reset:
        phases_to_reset = [p.upper() for p in args.phase] if args.phase else None
        runner.reset(phases_to_reset)
        if not args.phase:
            print("All checkpoints reset. Ready to start fresh.")
            return
    
    # Run experiments
    phases = [p.upper() for p in args.phase] if args.phase else None
    success = runner.run_phases(phases)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
