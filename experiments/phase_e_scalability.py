"""
Phase E: Network Scalability Experiments
========================================
Tests algorithm performance on different network sizes.

Design:
- Fix N = 60 requests
- Extract 25%, 50%, 100% of the network (subgraphs)
- Run OptLoad and Insertion baseline
- Record metrics
"""

import subprocess
import os
import sys
import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from experiments.config import (
    CONFIG, QUERIES_DIR, RESULTS_DIR, PROJECT_ROOT,
    DATASET_DIR, NODE_FILE, TOTAL_NODES
)
from experiments.utils.logger import get_logger, get_checkpoint_manager
from experiments.phase_d_algorithm_execution import AlgorithmExecutor, JavaRunner


@dataclass
class SubgraphConfig:
    """Configuration for a subgraph experiment."""
    percentage: float
    num_nodes: int
    node_ids: List[int]
    seed: int
    

class SubgraphGenerator:
    """
    Generates subgraphs of the transportation network.
    """
    
    def __init__(self):
        self.logger = get_logger("subgraph_generator")
        self.total_nodes = TOTAL_NODES
        
    def generate_subgraph(self, percentage: float, seed: int = 42) -> SubgraphConfig:
        """
        Generate a random subgraph with the specified percentage of nodes.
        
        Args:
            percentage: Fraction of nodes to include (0.0 to 1.0)
            seed: Random seed for reproducibility
            
        Returns:
            SubgraphConfig with selected node IDs
        """
        
        random.seed(seed)
        
        num_nodes = int(self.total_nodes * percentage)
        
        # Sample nodes randomly
        all_nodes = list(range(self.total_nodes))
        selected_nodes = sorted(random.sample(all_nodes, num_nodes))
        
        self.logger.info(f"Generated subgraph with {num_nodes} nodes ({percentage*100:.0f}%)")
        
        return SubgraphConfig(
            percentage=percentage,
            num_nodes=num_nodes,
            node_ids=selected_nodes,
            seed=seed
        )
    
    def save_subgraph_nodes(self, config: SubgraphConfig, output_dir: Path) -> Path:
        """Save subgraph node list to file."""
        
        output_file = output_dir / f"subgraph_nodes_{int(config.percentage*100)}.txt"
        
        with open(output_file, 'w') as f:
            for node_id in config.node_ids:
                f.write(f"{node_id}\n")
        
        return output_file
    
    def create_subgraph_dataset(self, config: SubgraphConfig, output_dir: Path) -> Tuple[Path, Path]:
        """
        Create a filtered node/edge dataset for the subgraph.
        
        Note: This is a simplified version. Full implementation would need
        to properly filter edges that connect only nodes in the subgraph.
        """
        
        node_set = set(config.node_ids)
        
        # Create mapping from old to new node IDs
        node_mapping = {old_id: new_id for new_id, old_id in enumerate(config.node_ids)}
        
        # Filter and remap nodes
        nodes_file = output_dir / f"nodes_{int(config.percentage*100)}.txt"
        
        with open(NODE_FILE, 'r') as fin, open(nodes_file, 'w') as fout:
            for line_num, line in enumerate(fin):
                if line_num in node_set:
                    fout.write(line)
        
        self.logger.info(f"Created subgraph nodes file: {nodes_file}")
        
        # Note: Edge filtering requires reading the large edge file
        # For now, we'll just note the configuration
        
        return nodes_file, None  # edges_file would be second return value


class ScalabilityExperiment:
    """
    Runs network scalability experiments.
    """
    
    def __init__(self, config=None):
        self.config = config or CONFIG.scalability
        self.logger = get_logger("scalability_experiment")
        self.subgraph_gen = SubgraphGenerator()
        self.executor = AlgorithmExecutor()
        
    def generate_fixed_n_queries(self, n: int, num_queries: int, 
                                  valid_nodes: List[int], seed: int) -> List[Path]:
        """
        Generate queries using only nodes from the subgraph.
        """
        
        from experiments.phase_c_query_generation import QueryGenerator, GeneratedQuery
        
        # Create a modified generator that uses only valid nodes
        generator = QueryGenerator()
        generator.valid_nodes = valid_nodes
        
        queries = []
        query_dir = QUERIES_DIR / f"scalability_N{n}"
        query_dir.mkdir(parents=True, exist_ok=True)
        
        for i in range(1, num_queries + 1):
            query_seed = seed * 1000 + i
            query = generator.generate_query(n, query_id=i, seed=query_seed)
            
            if query:
                query_file = query_dir / f"query_{i}.txt"
                with open(query_file, 'w') as f:
                    f.write(query.to_string())
                queries.append(query_file)
        
        return queries
    
    def run_scalability_experiments(self, checkpoint_manager=None) -> Dict:
        """
        Run the scalability experiments:
        1. Fix N = 60 requests
        2. For each network size (25%, 50%, 100%):
           - Generate subgraph
           - Generate queries within subgraph
           - Run algorithms
           - Record metrics
        """
        
        self.logger.section("Phase E: Network Scalability Experiments")
        
        results = {}
        
        # Create output directory
        scalability_dir = RESULTS_DIR / "scalability"
        scalability_dir.mkdir(exist_ok=True)
        
        n_requests = self.config.FIXED_N
        algorithms = self.config.ALGORITHMS_TO_RUN
        
        for percentage in self.config.SUBGRAPH_PERCENTAGES:
            experiment_key = f"network_{int(percentage*100)}pct"
            
            # Check checkpoint
            if checkpoint_manager and checkpoint_manager.is_item_completed(f"scale_{experiment_key}"):
                self.logger.info(f"Skipping {experiment_key} (already completed)")
                continue
            
            self.logger.subsection(f"Network Size: {percentage*100:.0f}%")
            
            # Generate subgraph
            subgraph = self.subgraph_gen.generate_subgraph(percentage, seed=42)
            self.subgraph_gen.save_subgraph_nodes(subgraph, scalability_dir)
            
            # Generate queries for this network size
            num_queries = 10  # Fewer queries for scalability tests
            queries = self.generate_fixed_n_queries(
                n_requests, 
                num_queries, 
                subgraph.node_ids,
                seed=int(percentage * 1000)
            )
            
            self.logger.info(f"Generated {len(queries)} queries for {percentage*100:.0f}% network")
            
            # Run algorithms
            experiment_results = {
                "percentage": percentage,
                "num_nodes": subgraph.num_nodes,
                "num_queries": len(queries),
                "algorithms": {}
            }
            
            for algorithm in algorithms:
                algo_results = []
                
                for query_path in queries:
                    query_id = query_path.stem
                    result = self.executor.run_single_algorithm(
                        query_path, 
                        algorithm, 
                        f"scale_{int(percentage*100)}_{query_id}"
                    )
                    algo_results.append(result.to_dict())
                
                experiment_results["algorithms"][algorithm] = algo_results
                
                # Calculate summary statistics
                successful = [r for r in algo_results if r.get("success")]
                if successful:
                    avg_runtime = sum(r.get("runtime_ms", 0) for r in successful) / len(successful)
                    avg_distance = sum(r.get("distance", 0) for r in successful) / len(successful)
                    avg_lu = sum(r.get("lu_cost", 0) for r in successful) / len(successful)
                    avg_served = sum(r.get("served_requests", 0) for r in successful) / len(successful)
                    
                    self.logger.info(
                        f"  {algorithm}: avg_runtime={avg_runtime:.0f}ms, "
                        f"avg_dist={avg_distance:.2f}, avg_LU={avg_lu:.1f}, "
                        f"avg_served={avg_served:.1f}"
                    )
            
            results[experiment_key] = experiment_results
            
            # Update checkpoint
            if checkpoint_manager:
                checkpoint_manager.mark_item_completed(f"scale_{experiment_key}")
        
        # Save results
        results_file = scalability_dir / "scalability_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"Scalability experiments complete. Results saved to: {results_file}")
        
        if checkpoint_manager:
            checkpoint_manager.complete_phase("phase_e_scalability")
        
        return results


def main():
    """Run scalability experiments as standalone script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run network scalability experiments")
    parser.add_argument("--percentages", type=float, nargs="+", default=None,
                       help="Network size percentages to test")
    parser.add_argument("--algorithms", type=str, nargs="+", default=None,
                       help="Algorithms to run")
    parser.add_argument("--reset", action="store_true",
                       help="Reset checkpoint and start fresh")
    
    args = parser.parse_args()
    
    # Update config
    if args.percentages:
        CONFIG.scalability.SUBGRAPH_PERCENTAGES = args.percentages
    if args.algorithms:
        CONFIG.scalability.ALGORITHMS_TO_RUN = args.algorithms
    
    # Initialize checkpoint manager
    checkpoint = get_checkpoint_manager("scalability_experiments")
    
    if args.reset:
        checkpoint.reset()
        print("Checkpoint reset. Starting fresh.")
    
    # Run experiments
    experiment = ScalabilityExperiment()
    results = experiment.run_scalability_experiments(checkpoint)
    
    print(f"\nCompleted {len(results)} scalability experiments")


if __name__ == "__main__":
    main()
