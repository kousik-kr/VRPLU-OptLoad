#!/usr/bin/env python3
"""
Tour-Based Query Generator for Oldenburg and California Datasets
================================================================

Uses the same logic as the London query generator to create spatially
and temporally realistic N=20 queries for network scalability experiments.
"""

import random
import heapq
import math
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict

# Configuration
BASE_DIR = Path("/home/gunturi/VRPLU-OptLoad")
DATASET_DIR = BASE_DIR / "dataset"
RESULTS_DIR = BASE_DIR / "experiments" / "results" / "network_scalability"

# Dataset configurations
DATASETS = {
    'oldenburg': {
        'node_count': 6105,
        'nodes_file': DATASET_DIR / 'nodes_6105.txt',
        'edges_file': DATASET_DIR / 'edges_6105.txt',
        'name': 'Oldenburg'
    },
    'california': {
        'node_count': 21048,
        'nodes_file': DATASET_DIR / 'nodes_21048.txt',
        'edges_file': DATASET_DIR / 'edges_21048.txt',
        'name': 'California'
    }
}

# =============================================================================
# Query Generation Parameters (same as London)
# =============================================================================

@dataclass
class QueryGenConfig:
    """Configuration for tour-based query generation."""
    TIME_HORIZON: int = 600
    WORKING_TIME_START: int = 540  # 09:00
    WORKING_TIME_END: int = 1140   # 19:00
    RETURN_BUFFER: int = 30
    
    CAPACITY_MIN: int = 8
    CAPACITY_MAX: int = 12
    DEMAND_MIN: int = 1
    DEMAND_MAX: int = 5
    
    PICKUP_SLACK_MIN: int = 15
    PICKUP_SLACK_MAX: int = 45
    DELIVERY_SLACK_MIN: int = 15
    DELIVERY_SLACK_MAX: int = 45
    
    MIN_PD_SEPARATION: int = 10
    
    CANDIDATE_K: int = 50
    LOCALITY_ALPHA: float = 0.1
    # MIN_TOUR_LENGTH will be set per dataset
    
    N_REQUESTS: int = 20
    NUM_QUERIES: int = 20
    SEED_BASE: int = 42
    
    # Per-dataset parameters (smaller networks need smaller tours)
    MIN_TOUR_LENGTHS: Dict = field(default_factory=lambda: {
        'oldenburg': 15,   # 6105 nodes - smaller, sparser
        'california': 30,  # 21048 nodes - medium sized
        'london': 50       # 285050 nodes - large, dense
    })


CONFIG = QueryGenConfig()


# =============================================================================
# Graph Data Structures
# =============================================================================

@dataclass
class GraphNode:
    node_id: int
    x: float
    y: float
    
    def euclidean_distance(self, other: 'GraphNode') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


@dataclass
class GraphEdge:
    source: int
    destination: int
    distance: float
    travel_times: Dict[int, float]
    
    def get_travel_time(self, departure_time: float) -> float:
        times = sorted(self.travel_times.keys())
        if not times:
            return self.distance / 50 * 60
        
        lower_t = times[0]
        upper_t = times[-1]
        
        for t in times:
            if t <= departure_time:
                lower_t = t
            if t >= departure_time:
                upper_t = t
                break
        
        if lower_t == upper_t:
            return self.travel_times[lower_t]
        
        t1, t2 = lower_t, upper_t
        c1, c2 = self.travel_times[t1], self.travel_times[t2]
        
        if t2 == t1:
            return c1
        
        ratio = (departure_time - t1) / (t2 - t1)
        return c1 + ratio * (c2 - c1)
    
    def get_arrival_time(self, departure_time: float) -> float:
        return departure_time + self.get_travel_time(departure_time)


class RoadNetwork:
    def __init__(self):
        self.nodes: Dict[int, GraphNode] = {}
        self.outgoing: Dict[int, Dict[int, GraphEdge]] = defaultdict(dict)
        self.incoming: Dict[int, Dict[int, GraphEdge]] = defaultdict(dict)
        self.time_series: List[int] = []
        
    def load_from_files(self, nodes_file: Path, edges_file: Path):
        print(f"Loading nodes from {nodes_file}")
        
        with open(nodes_file, 'r') as f:
            for line_num, line in enumerate(f):
                parts = line.strip().split()
                if len(parts) >= 3:
                    node_id = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    self.nodes[node_id] = GraphNode(node_id, x, y)
        
        print(f"Loaded {len(self.nodes)} nodes")
        print(f"Loading edges from {edges_file}")
        
        with open(edges_file, 'r') as f:
            first_line = f.readline().strip()
            self.time_series = [int(t) for t in first_line.split()]
            
            edge_count = 0
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    source = int(parts[0])
                    dest = int(parts[1])
                    travel_times_str = parts[2]
                    
                    travel_times = {}
                    costs = travel_times_str.split(',')
                    for i, cost in enumerate(costs):
                        if i < len(self.time_series):
                            travel_times[self.time_series[i]] = float(cost)
                    
                    if source in self.nodes and dest in self.nodes:
                        distance = self.nodes[source].euclidean_distance(self.nodes[dest])
                        
                        edge = GraphEdge(source, dest, distance, travel_times)
                        self.outgoing[source][dest] = edge
                        self.incoming[dest][source] = edge
                        edge_count += 1
        
        print(f"Loaded {edge_count} edges")
    
    def get_neighbors(self, node_id: int) -> List[int]:
        return list(self.outgoing.get(node_id, {}).keys())
    
    def get_edge(self, source: int, dest: int) -> Optional[GraphEdge]:
        return self.outgoing.get(source, {}).get(dest)
    
    def get_k_nearest(self, node_id: int, k: int = 15) -> List[Tuple[int, float]]:
        if node_id not in self.nodes:
            return []
        
        source = self.nodes[node_id]
        neighbors = self.get_neighbors(node_id)
        
        if not neighbors:
            return []
        
        distances = []
        for neighbor_id in neighbors:
            if neighbor_id in self.nodes:
                dist = source.euclidean_distance(self.nodes[neighbor_id])
                distances.append((neighbor_id, dist))
        
        distances.sort(key=lambda x: x[1])
        return distances[:k]


# =============================================================================
# Tour Builder
# =============================================================================

@dataclass
class TourStop:
    node_id: int
    arrival_time: float


class TourBuilder:
    def __init__(self, network: RoadNetwork, config: QueryGenConfig = None, min_tour_length: int = None, allow_revisit: bool = False):
        self.network = network
        self.config = config or CONFIG
        self.rng = random.Random()
        self.min_tour_length = min_tour_length or 50
        self.allow_revisit = allow_revisit
    
    def set_seed(self, seed: int):
        self.rng = random.Random(seed)
    
    def select_depot(self) -> int:
        valid_nodes = [n for n in self.network.nodes.keys() 
                       if len(self.network.get_neighbors(n)) > 0]
        return self.rng.choice(valid_nodes)
    
    def select_next_candidate(self, current: int, visited: Set[int], tour_length: int = 0) -> Optional[int]:
        candidates = self.network.get_k_nearest(current, self.config.CANDIDATE_K)
        candidates = [(n, d) for n, d in candidates if n not in visited]
        
        if not candidates and tour_length < self.min_tour_length:
            neighbors = self.network.get_neighbors(current)
            unvisited_neighbors = [n for n in neighbors if n not in visited]
            if unvisited_neighbors:
                return self.rng.choice(unvisited_neighbors)
        
        if not candidates:
            return None
        
        # Proximity-weighted sampling
        weights = []
        for _, dist in candidates:
            weight = math.exp(-self.config.LOCALITY_ALPHA * dist / 1000)
            weights.append(max(weight, 0.001))
        
        total = sum(weights)
        weights = [w / total for w in weights]
        
        r = self.rng.random()
        cumulative = 0
        for (node_id, _), weight in zip(candidates, weights):
            cumulative += weight
            if r <= cumulative:
                return node_id
        
        return candidates[-1][0]
    
    def select_next_candidate_allow_revisit(self, current: int, recent_nodes: Set[int]) -> Optional[int]:
        """For sparse graphs - allows revisiting nodes but avoids immediate backtracking."""
        neighbors = self.network.get_neighbors(current)
        
        # Filter out recently visited to avoid short cycles
        fresh_neighbors = [n for n in neighbors if n not in recent_nodes]
        
        if fresh_neighbors:
            return self.rng.choice(fresh_neighbors)
        
        # If all neighbors are recent, pick any neighbor
        if neighbors:
            return self.rng.choice(neighbors)
        
        return None
    
    def build_tour(self, seed: int) -> Tuple[int, List[TourStop]]:
        self.set_seed(seed)
        
        depot = self.select_depot()
        tour = [TourStop(depot, self.config.WORKING_TIME_START)]
        visited = {depot}
        recent_nodes = {depot}  # For allow_revisit mode - track last N nodes
        recent_window = 5  # Don't revisit last 5 nodes
        
        current_time = self.config.WORKING_TIME_START
        current_node = depot
        
        max_time = self.config.WORKING_TIME_END - self.config.RETURN_BUFFER
        max_iterations = 500
        iterations = 0
        
        while current_time < max_time and iterations < max_iterations:
            iterations += 1
            
            if self.allow_revisit:
                next_node = self.select_next_candidate_allow_revisit(current_node, recent_nodes)
            else:
                next_node = self.select_next_candidate(current_node, visited, len(tour))
                
            if next_node is None:
                break
            
            edge = self.network.get_edge(current_node, next_node)
            if edge:
                arrival = edge.get_arrival_time(current_time)
                
                if arrival > max_time:
                    break
                
                tour.append(TourStop(next_node, arrival))
                visited.add(next_node)
                
                # Update recent nodes window
                recent_nodes.add(next_node)
                if len(recent_nodes) > recent_window:
                    # Keep only the last recent_window nodes from tour
                    recent_nodes = {tour[max(0, len(tour)-recent_window) + i].node_id 
                                   for i in range(min(recent_window, len(tour)))}
                
                current_time = arrival
                current_node = next_node
        
        return depot, tour


# =============================================================================
# Query Generator
# =============================================================================

class QueryGenerator:
    def __init__(self, network: RoadNetwork, config: QueryGenConfig = None, dataset_key: str = 'london'):
        self.network = network
        self.config = config or CONFIG
        self.dataset_key = dataset_key
        # Get dataset-specific min tour length
        self.min_tour_length = self.config.MIN_TOUR_LENGTHS.get(dataset_key, 50)
        # For sparse networks (Oldenburg), allow revisiting nodes
        allow_revisit = dataset_key == 'oldenburg'
        self.tour_builder = TourBuilder(network, self.config, self.min_tour_length, allow_revisit)
        self.rng = random.Random()
    
    def generate_query(self, seed: int) -> Optional[Dict]:
        self.rng = random.Random(seed)
        
        # Build tour
        depot, tour = self.tour_builder.build_tour(seed)
        
        # For smaller networks, allow shorter tours (but at least N_REQUESTS + 2 for depot + endpoints)
        min_required = max(self.min_tour_length, self.config.N_REQUESTS + 2)
        
        if len(tour) < min_required:
            print(f"  Warning: Tour too short ({len(tour)} stops, need {min_required})")
            return None
        
        capacity = self.rng.randint(self.config.CAPACITY_MIN, self.config.CAPACITY_MAX)
        
        # Sample pickup-delivery pairs
        services = []
        indices_used = set()
        
        attempts = 0
        max_attempts = 1000
        
        while len(services) < self.config.N_REQUESTS and attempts < max_attempts:
            attempts += 1
            
            # Select pickup index
            pickup_idx = self.rng.randint(1, len(tour) - 2)
            if pickup_idx in indices_used:
                continue
            
            # Select delivery index (must be after pickup)
            min_delivery_idx = pickup_idx + 1
            max_delivery_idx = len(tour) - 1
            
            if min_delivery_idx >= max_delivery_idx:
                continue
            
            delivery_idx = self.rng.randint(min_delivery_idx, max_delivery_idx)
            if delivery_idx in indices_used:
                continue
            
            pickup_stop = tour[pickup_idx]
            delivery_stop = tour[delivery_idx]
            
            # Check time separation
            time_diff = delivery_stop.arrival_time - pickup_stop.arrival_time
            if time_diff < self.config.MIN_PD_SEPARATION:
                continue
            
            # Generate time windows
            pickup_slack = self.rng.randint(self.config.PICKUP_SLACK_MIN, self.config.PICKUP_SLACK_MAX)
            delivery_slack = self.rng.randint(self.config.DELIVERY_SLACK_MIN, self.config.DELIVERY_SLACK_MAX)
            
            pickup_start = max(self.config.WORKING_TIME_START, 
                              int(pickup_stop.arrival_time) - pickup_slack // 2)
            pickup_end = min(self.config.WORKING_TIME_END,
                            int(pickup_stop.arrival_time) + pickup_slack // 2)
            
            delivery_start = max(pickup_end + 1,
                                int(delivery_stop.arrival_time) - delivery_slack // 2)
            delivery_end = min(self.config.WORKING_TIME_END,
                              int(delivery_stop.arrival_time) + delivery_slack // 2)
            
            if delivery_start >= delivery_end:
                continue
            
            demand = self.rng.randint(self.config.DEMAND_MIN, self.config.DEMAND_MAX)
            
            services.append({
                'pickup_node': pickup_stop.node_id,
                'delivery_node': delivery_stop.node_id,
                'pickup_window': [pickup_start, pickup_end],
                'delivery_window': [delivery_start, delivery_end],
                'demand': demand,
                'pickup_tour_index': pickup_idx,
                'delivery_tour_index': delivery_idx
            })
            
            indices_used.add(pickup_idx)
            indices_used.add(delivery_idx)
        
        if len(services) < self.config.N_REQUESTS:
            print(f"  Warning: Only generated {len(services)} services")
            return None
        
        return {
            'depot_node': depot,
            'capacity': capacity,
            'tour_length': len(tour),
            'services': services,
            'seed': seed
        }


def write_query_file(query: Dict, query_id: int, output_path: Path):
    """Write query in OptLoad format."""
    lines = []
    lines.append(f"D {query['depot_node']}")
    lines.append(f"C {query['capacity']}")
    
    for svc in query['services']:
        lines.append(f"S {svc['pickup_node']},{svc['delivery_node']} "
                    f"{svc['pickup_window'][0]},{svc['pickup_window'][1]} "
                    f"{svc['delivery_window'][0]},{svc['delivery_window'][1]} "
                    f"{svc['demand']}")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')


def generate_queries_for_dataset(dataset_key: str):
    """Generate N=20 queries for a dataset."""
    dataset = DATASETS[dataset_key]
    
    print(f"\n{'='*60}")
    print(f"GENERATING QUERIES FOR {dataset['name'].upper()}")
    print(f"{'='*60}")
    
    if not dataset['nodes_file'].exists():
        print(f"ERROR: Nodes file not found: {dataset['nodes_file']}")
        return
    if not dataset['edges_file'].exists():
        print(f"ERROR: Edges file not found: {dataset['edges_file']}")
        return
    
    # Load network
    network = RoadNetwork()
    network.load_from_files(dataset['nodes_file'], dataset['edges_file'])
    
    # Create output directory
    queries_dir = RESULTS_DIR / dataset_key / "queries"
    queries_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate queries
    generator = QueryGenerator(network, CONFIG, dataset_key)
    successful = 0
    
    for i in range(CONFIG.NUM_QUERIES):
        seed = CONFIG.SEED_BASE * 1000 + i + 1
        print(f"\n[{i+1}/{CONFIG.NUM_QUERIES}] Generating query with seed {seed}...")
        
        query = generator.generate_query(seed)
        
        if query:
            query_id = i + 1
            query['query_id'] = query_id
            query['n_requests'] = CONFIG.N_REQUESTS
            
            # Write query file
            query_file = queries_dir / f"query_{query_id}.txt"
            write_query_file(query, query_id, query_file)
            
            # Write meta file
            meta_file = queries_dir / f"query_{query_id}_meta.json"
            with open(meta_file, 'w') as f:
                json.dump(query, f, indent=2)
            
            print(f"  ✓ Query {query_id}: depot={query['depot_node']}, "
                  f"tour_length={query['tour_length']}, services={len(query['services'])}")
            successful += 1
        else:
            print(f"  ✗ Failed to generate query")
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: Generated {successful}/{CONFIG.NUM_QUERIES} queries")
    print(f"Queries saved to: {queries_dir}")
    print(f"{'='*60}")
    
    return successful


def main():
    print("="*70)
    print("TOUR-BASED QUERY GENERATOR FOR NETWORK SCALABILITY")
    print("="*70)
    
    for dataset_key in DATASETS.keys():
        generate_queries_for_dataset(dataset_key)


if __name__ == "__main__":
    main()
