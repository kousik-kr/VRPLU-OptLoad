"""
Phase C: Query Generation
=========================
Generates queries for VRP-LU experiments with configurable parameters.

Query Format:
    D <depot_node_id>
    C <capacity>
    S <pickup_node>,<delivery_node> <pickup_start>,<pickup_end> <delivery_start>,<delivery_end> <demand>
"""

import random
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from experiments.config import (
    CONFIG, QUERIES_DIR, NODE_FILE, TOTAL_NODES,
    CHECKPOINTS_DIR
)
from experiments.utils.logger import get_logger, get_checkpoint_manager


@dataclass
class ServiceRequest:
    """Represents a single pickup-delivery service request."""
    pickup_node: int
    delivery_node: int
    pickup_start: int
    pickup_end: int
    delivery_start: int
    delivery_end: int
    demand: int
    
    def to_string(self) -> str:
        return (f"S {self.pickup_node},{self.delivery_node} "
                f"{self.pickup_start},{self.pickup_end} "
                f"{self.delivery_start},{self.delivery_end} "
                f"{self.demand}")


@dataclass
class GeneratedQuery:
    """Represents a complete query."""
    query_id: int
    depot_node: int
    capacity: int
    services: List[ServiceRequest]
    seed: int
    n_requests: int
    
    def to_string(self) -> str:
        lines = [f"D {self.depot_node}", f"C {self.capacity}"]
        for service in self.services:
            lines.append(service.to_string())
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        return {
            "query_id": self.query_id,
            "depot_node": self.depot_node,
            "capacity": self.capacity,
            "seed": self.seed,
            "n_requests": self.n_requests,
            "services": [
                {
                    "pickup_node": s.pickup_node,
                    "delivery_node": s.delivery_node,
                    "pickup_window": [s.pickup_start, s.pickup_end],
                    "delivery_window": [s.delivery_start, s.delivery_end],
                    "demand": s.demand
                }
                for s in self.services
            ]
        }


class QueryGenerator:
    """
    Generates VRP-LU queries with proper time window constraints.
    
    Ensures:
    - Delivery time windows start after pickup time windows
    - Time windows respect working hours
    - Demands are within reasonable bounds
    """
    
    def __init__(self, config=None):
        self.config = config or CONFIG.query
        self.logger = get_logger("query_generator")
        self.valid_nodes = self._load_valid_nodes()
        
    def _load_valid_nodes(self) -> List[int]:
        """Load valid node IDs from the dataset."""
        if NODE_FILE.exists():
            with open(NODE_FILE, 'r') as f:
                # Count lines (each line is a node)
                count = sum(1 for _ in f)
            self.logger.info(f"Loaded {count} valid nodes from dataset")
            return list(range(count))
        else:
            self.logger.warning(f"Node file not found at {NODE_FILE}, using range 0-{TOTAL_NODES-1}")
            return list(range(TOTAL_NODES))
    
    def _generate_time_window(self, min_start: int, max_end: int, 
                               min_duration: int = None) -> Tuple[int, int]:
        """Generate a valid time window."""
        min_duration = min_duration or self.config.DURATION_MIN
        max_duration = self.config.DURATION_MAX
        
        # Ensure we have room for the minimum duration
        if max_end - min_start < min_duration:
            return None
        
        # Generate duration
        max_possible_duration = min(max_duration, max_end - min_start)
        duration = random.randint(min_duration, max_possible_duration)
        
        # Generate start time
        latest_start = max_end - duration
        start = random.randint(min_start, latest_start)
        end = start + duration
        
        return (start, end)
    
    def _generate_service_request(self, existing_pickups: List[Tuple[int, int]],
                                   existing_deliveries: List[Tuple[int, int]]) -> Optional[ServiceRequest]:
        """Generate a single service request with valid time windows."""
        
        max_attempts = 2000  # Increased attempts for larger N
        
        for _ in range(max_attempts):
            # Generate pickup time window - use shorter durations for more flexibility
            duration_min = max(15, self.config.DURATION_MIN // 2)  # Allow shorter windows
            pickup_tw = self._generate_time_window(
                self.config.WORK_START,
                self.config.WORK_END - duration_min - 5,
                min_duration=duration_min
            )
            if pickup_tw is None:
                continue
                
            pickup_start, pickup_end = pickup_tw
            
            # Relaxed overlap constraints for larger N (allow more overlaps)
            max_overlaps = max(3, len(existing_pickups) // 10 + 2)
            overlaps = sum(
                1 for (s, e) in existing_pickups
                if not (pickup_end <= s or pickup_start >= e)
            )
            if overlaps > max_overlaps:
                continue
            
            # Generate delivery time window (must start after pickup ends)
            delivery_tw = self._generate_time_window(
                pickup_end + 1,
                self.config.WORK_END,
                min_duration=duration_min
            )
            if delivery_tw is None:
                continue
                
            delivery_start, delivery_end = delivery_tw
            
            # Check overlap constraints for delivery windows (relaxed)
            max_delivery_overlaps = max(5, len(existing_deliveries) // 8 + 3)
            overlaps = sum(
                1 for (s, e) in existing_deliveries
                if not (delivery_end <= s or delivery_start >= e)
            )
            if overlaps > max_delivery_overlaps:
                continue
            
            # Generate nodes and demand
            pickup_node = random.choice(self.valid_nodes)
            delivery_node = random.choice(self.valid_nodes)
            demand = random.randint(self.config.DEMAND_MIN, self.config.DEMAND_MAX)
            
            return ServiceRequest(
                pickup_node=pickup_node,
                delivery_node=delivery_node,
                pickup_start=pickup_start,
                pickup_end=pickup_end,
                delivery_start=delivery_start,
                delivery_end=delivery_end,
                demand=demand
            )
        
        return None
    
    def generate_query(self, n_requests: int, query_id: int, seed: int) -> Optional[GeneratedQuery]:
        """Generate a single query with n service requests."""
        
        random.seed(seed)
        
        depot_node = random.choice(self.valid_nodes)
        capacity = random.randint(self.config.CAPACITY_MIN, self.config.CAPACITY_MAX)
        
        services = []
        pickup_windows = []
        delivery_windows = []
        
        for _ in range(n_requests):
            service = self._generate_service_request(pickup_windows, delivery_windows)
            if service is None:
                self.logger.warning(f"Failed to generate service request for query {query_id}")
                return None
            
            services.append(service)
            pickup_windows.append((service.pickup_start, service.pickup_end))
            delivery_windows.append((service.delivery_start, service.delivery_end))
        
        return GeneratedQuery(
            query_id=query_id,
            depot_node=depot_node,
            capacity=capacity,
            services=services,
            seed=seed,
            n_requests=n_requests
        )
    
    def generate_all_queries(self, checkpoint_manager=None) -> dict:
        """
        Generate all queries according to experimental design.
        
        For each N in N_VALUES:
            For run = 1..RUNS_PER_N:
                Generate query with seed
        
        Returns:
            dict: Mapping of (N, run) -> query file path
        """
        
        self.logger.section("Phase C: Query Generation")
        
        generated_queries = {}
        total_queries = len(self.config.N_VALUES) * self.config.RUNS_PER_N
        completed = 0
        
        for N in self.config.N_VALUES:
            self.logger.subsection(f"Generating queries for N = {N}")
            
            # Create directory for this N
            n_dir = QUERIES_DIR / f"N_{N}"
            n_dir.mkdir(exist_ok=True)
            
            for run in range(1, self.config.RUNS_PER_N + 1):
                query_key = f"N{N}_R{run}"
                
                # Check if already completed
                if checkpoint_manager and checkpoint_manager.is_item_completed(f"query_{query_key}"):
                    self.logger.debug(f"Skipping {query_key} (already completed)")
                    completed += 1
                    continue
                
                # Generate deterministic seed
                seed = self.config.SEED_BASE * 1000 + N * 100 + run
                
                # Generate the query
                query = self.generate_query(N, query_id=run, seed=seed)
                
                if query is None:
                    self.logger.error(f"Failed to generate query {query_key}")
                    if checkpoint_manager:
                        checkpoint_manager.mark_item_failed(f"query_{query_key}", "Generation failed")
                    continue
                
                # Save query file (VRP-LU format)
                query_file = n_dir / f"query_{run}.txt"
                with open(query_file, 'w') as f:
                    f.write(query.to_string())
                
                # Save query metadata (JSON)
                meta_file = n_dir / f"query_{run}_meta.json"
                with open(meta_file, 'w') as f:
                    json.dump(query.to_dict(), f, indent=2)
                
                generated_queries[(N, run)] = str(query_file)
                
                if checkpoint_manager:
                    checkpoint_manager.mark_item_completed(f"query_{query_key}")
                
                completed += 1
                
                if completed % 50 == 0 or completed == total_queries:
                    self.logger.info(f"Progress: {completed}/{total_queries} queries generated")
        
        # Save index of all queries
        index_file = QUERIES_DIR / "query_index.json"
        index_data = {
            f"N{k[0]}_R{k[1]}": v for k, v in generated_queries.items()
        }
        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)
        
        self.logger.info(f"Query generation complete. Total queries: {len(generated_queries)}")
        
        if checkpoint_manager:
            checkpoint_manager.complete_phase("phase_c_query_generation")
        
        return generated_queries


def main():
    """Run query generation as standalone script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate VRP-LU queries for experiments")
    parser.add_argument("--n-values", type=int, nargs="+", default=None,
                       help="List of N values (number of requests)")
    parser.add_argument("--runs", type=int, default=None,
                       help="Number of runs per N value")
    parser.add_argument("--reset", action="store_true",
                       help="Reset checkpoint and start fresh")
    parser.add_argument("--seed", type=int, default=42,
                       help="Base random seed")
    
    args = parser.parse_args()
    
    # Update config if args provided
    if args.n_values:
        CONFIG.query.N_VALUES = args.n_values
    if args.runs:
        CONFIG.query.RUNS_PER_N = args.runs
    if args.seed:
        CONFIG.query.SEED_BASE = args.seed
    
    # Initialize checkpoint manager
    checkpoint = get_checkpoint_manager("query_generation")
    
    if args.reset:
        checkpoint.reset()
        print("Checkpoint reset. Starting fresh.")
    
    # Check if already completed
    if checkpoint.is_phase_completed("phase_c_query_generation"):
        print("Query generation already completed. Use --reset to regenerate.")
        return
    
    # Run generation
    generator = QueryGenerator()
    queries = generator.generate_all_queries(checkpoint)
    
    print(f"\nGenerated {len(queries)} queries")
    print(f"Queries saved to: {QUERIES_DIR}")


if __name__ == "__main__":
    main()
