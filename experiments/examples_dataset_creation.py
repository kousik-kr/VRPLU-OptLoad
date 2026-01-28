#!/usr/bin/env python3
"""
Practical Examples for Dataset Creation
========================================

This script demonstrates various dataset creation scenarios.
Run with: python examples_dataset_creation.py [example_name]
"""

from pathlib import Path
from experiments.dataset_creator import (
    DatasetConfig, DatasetCreator, NodeGenerator, EdgeGenerator,
    QueryGenerator, DatasetValidator
)
import logging


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


# =============================================================================
# EXAMPLE 1: Create Minimal Dataset (Quick Start)
# =============================================================================

def example_minimal_dataset():
    """Create a minimal dataset for testing (50 nodes, 5 queries)."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Minimal Dataset for Testing")
    print("="*70)
    
    config = DatasetConfig(
        num_nodes=50,
        num_queries=5,
        n_requests=10,
        node_seed=42,
        edge_seed=42,
        query_seed=42
    )
    
    output_dir = Path('examples/example1_minimal')
    creator = DatasetCreator(config, output_dir)
    creator.create_complete_dataset()
    
    print(f"\n✓ Dataset created at: {output_dir}")
    print(f"  Files: nodes.txt, edges.txt, queries/query_*.txt")


# =============================================================================
# EXAMPLE 2: Create Medium Dataset (Realistic Urban Network)
# =============================================================================

def example_medium_dataset():
    """Create medium dataset simulating urban network (500 nodes)."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Medium Dataset (Urban Network)")
    print("="*70)
    
    config = DatasetConfig(
        num_nodes=500,
        x_bounds=(0.0, 50.0),
        y_bounds=(0.0, 50.0),
        num_queries=15,
        n_requests=20,
        capacity_min=10,
        capacity_max=15,
        node_seed=123,
        edge_seed=123,
        query_seed=123
    )
    
    output_dir = Path('examples/example2_medium')
    creator = DatasetCreator(config, output_dir)
    creator.create_complete_dataset()
    
    print(f"\n✓ Dataset created at: {output_dir}")


# =============================================================================
# EXAMPLE 3: Generate Queries for Existing Network
# =============================================================================

def example_add_queries_to_existing():
    """Generate additional queries for existing network."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Add Queries to Existing Network")
    print("="*70)
    
    # Assume we have an existing network
    # (in practice, would be from DATASET.md files)
    
    config = DatasetConfig(
        num_nodes=500,
        num_queries=25,  # Different from original
        n_requests=30    # Larger queries
    )
    
    # Create nodes first (would normally load from file)
    node_gen = NodeGenerator(config)
    nodes = node_gen.generate_clustered(num_clusters=5)
    
    # Generate queries for the network
    query_gen = QueryGenerator(nodes, config)
    queries = query_gen.generate_queries(num_queries=25)
    
    output_dir = Path('examples/example3_queries')
    output_dir.mkdir(parents=True, exist_ok=True)
    query_gen.save_queries(queries, output_dir / 'queries')
    
    print(f"\n✓ Queries created at: {output_dir}/queries")
    print(f"  Created {len(queries)} queries with 30 requests each")


# =============================================================================
# EXAMPLE 4: Custom Time Windows and Demand
# =============================================================================

def example_custom_time_windows():
    """Create dataset with custom time window constraints."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Custom Time Windows and Demand")
    print("="*70)
    
    # Early morning delivery scenario (6:00 AM - 12:00 PM)
    config = DatasetConfig(
        num_nodes=300,
        num_queries=10,
        n_requests=15,
        working_time_start=360,      # 6:00 AM
        working_time_end=720,        # 12:00 PM
        pickup_slack_min=20,
        pickup_slack_max=40,
        min_pd_separation=5,
        demand_min=2,
        demand_max=8,
        capacity_min=15,
        capacity_max=20,
        node_seed=99,
        edge_seed=99,
        query_seed=99
    )
    
    output_dir = Path('examples/example4_early_morning')
    creator = DatasetCreator(config, output_dir)
    creator.create_complete_dataset()
    
    print(f"\n✓ Early morning delivery dataset at: {output_dir}")
    print(f"  Time windows: 6:00 AM - 12:00 PM (tight schedule)")
    print(f"  Higher demand (2-8 units), larger capacity (15-20 units)")


# =============================================================================
# EXAMPLE 5: Large Network with Scalability Study
# =============================================================================

def example_scalability_study():
    """Create datasets of different sizes for scalability analysis."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Scalability Study - Multiple Network Sizes")
    print("="*70)
    
    sizes = [
        ('small', 100, 10),
        ('medium', 500, 10),
        ('large', 1000, 10)
    ]
    
    base_dir = Path('examples/example5_scalability')
    
    for name, num_nodes, num_queries in sizes:
        print(f"\n  Creating {name} network ({num_nodes} nodes)...")
        
        config = DatasetConfig(
            num_nodes=num_nodes,
            num_queries=num_queries,
            n_requests=20,
            node_seed=42,
            edge_seed=42,
            query_seed=42
        )
        
        output_dir = base_dir / name
        creator = DatasetCreator(config, output_dir)
        nodes, edges = creator.create_synthetic_dataset()
        creator.create_queries(nodes)
        
        print(f"    ✓ Created: {num_nodes} nodes, {len(edges)} edges, {num_queries} queries")
    
    print(f"\n✓ Scalability study datasets at: {base_dir}")


# =============================================================================
# EXAMPLE 6: Validation of Generated Dataset
# =============================================================================

def example_validate_dataset():
    """Create dataset and validate all constraints."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Dataset Validation")
    print("="*70)
    
    config = DatasetConfig(
        num_nodes=200,
        num_queries=8,
        n_requests=15,
        node_seed=42,
        edge_seed=42,
        query_seed=42
    )
    
    output_dir = Path('examples/example6_validation')
    creator = DatasetCreator(config, output_dir)
    
    # Create dataset
    nodes, edges = creator.create_synthetic_dataset()
    queries = creator.create_queries(nodes)
    
    # Validate thoroughly
    print("\n" + "-"*70)
    print("Running comprehensive validation...")
    print("-"*70)
    
    validator = DatasetValidator()
    
    # Validate nodes
    print("\nValidating nodes...")
    if validator.validate_nodes(nodes):
        print(f"✓ All {len(nodes)} nodes valid")
    
    # Validate edges
    print("Validating edges...")
    if validator.validate_edges(edges, nodes):
        print(f"✓ All {len(edges)} edges valid")
    
    # Validate queries
    print("Validating queries...")
    all_valid = True
    for query in queries:
        if not validator.validate_query(query, nodes):
            all_valid = False
            break
    
    if all_valid:
        print(f"✓ All {len(queries)} queries valid")
    
    validator.report()
    print(f"\n✓ Complete validation at: {output_dir}")


# =============================================================================
# EXAMPLE 7: Comparing Different Edge Generation Methods
# =============================================================================

def example_edge_generation_comparison():
    """Compare k-nearest neighbors vs random edge generation."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Edge Generation Method Comparison")
    print("="*70)
    
    config = DatasetConfig(num_nodes=200)
    
    # Generate nodes (shared)
    node_gen = NodeGenerator(config)
    nodes = node_gen.generate_clustered(num_clusters=3)
    
    output_dir = Path('examples/example7_edge_comparison')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Method 1: K-nearest neighbors
    print("\nMethod 1: K-Nearest Neighbors (k=10)")
    edge_gen = EdgeGenerator(nodes, config)
    edges_knn = edge_gen.generate_k_nearest_neighbors(k=10)
    print(f"  Generated {len(edges_knn)} edges")
    
    # Method 2: Random edges
    print("\nMethod 2: Random Edges (density=5%)")
    config.edge_density = 0.05
    edge_gen = EdgeGenerator(nodes, config)
    edges_random = edge_gen.generate_random_edges()
    print(f"  Generated {len(edges_random)} edges")
    
    print(f"\nComparison:")
    print(f"  K-NN edges:    {len(edges_knn)} (dense, directed)")
    print(f"  Random edges:  {len(edges_random)} (sparse, random)")
    print(f"\n✓ Comparison data at: {output_dir}")


# =============================================================================
# EXAMPLE 8: Integration with Solver
# =============================================================================

def example_solver_integration():
    """Create dataset and prepare for solver execution."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Solver Integration Setup")
    print("="*70)
    
    config = DatasetConfig(
        num_nodes=100,
        num_queries=3,
        n_requests=10,
        node_seed=42,
        edge_seed=42,
        query_seed=42
    )
    
    output_dir = Path('examples/example8_solver')
    creator = DatasetCreator(config, output_dir)
    creator.create_complete_dataset()
    
    print("\nSolver Integration Guide:")
    print("-" * 70)
    print("\nTo run OptLoad solver on this dataset:")
    print("")
    print("  export DATASET_DIR='examples/example8_solver'")
    print("  cd /path/to/VRPLU-OptLoad")
    print("")
    print("  # For a single query:")
    print("  java -cp target/classes VRPLoadingUnloadingMain \\")
    print("    --cluster \\")
    print("    --nodes $DATASET_DIR/nodes.txt \\")
    print("    --edges $DATASET_DIR/edges.txt \\")
    print("    --query $DATASET_DIR/queries/query_1.txt")
    print("")
    print("  # For all queries:")
    print("  for q in examples/example8_solver/queries/query_*.txt; do")
    print("    java -cp target/classes VRPLoadingUnloadingMain \\")
    print("      --cluster \\")
    print("      --nodes $DATASET_DIR/nodes.txt \\")
    print("      --edges $DATASET_DIR/edges.txt \\")
    print("      --query $q")
    print("  done")
    print("")
    print(f"\n✓ Dataset prepared at: {output_dir}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all examples or specific example."""
    import sys
    
    setup_logging()
    
    examples = {
        '1': example_minimal_dataset,
        '2': example_medium_dataset,
        '3': example_add_queries_to_existing,
        '4': example_custom_time_windows,
        '5': example_scalability_study,
        '6': example_validate_dataset,
        '7': example_edge_generation_comparison,
        '8': example_solver_integration,
    }
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        if example_num in examples:
            examples[example_num]()
        else:
            print(f"Unknown example: {example_num}")
            print(f"Available examples: {', '.join(examples.keys())}")
    else:
        # Run all examples
        for example_num in sorted(examples.keys()):
            try:
                examples[example_num]()
            except Exception as e:
                print(f"Error in example {example_num}: {e}")
                import traceback
                traceback.print_exc()


if __name__ == '__main__':
    main()
