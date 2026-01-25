#!/usr/bin/env python3
"""
Tour-Based Query Generator for VRP-LU
======================================

Generates realistic pickup-delivery queries by:
1. Building a feasible time-dependent vehicle tour
2. Sampling pickup-delivery pairs from visited nodes
3. Constructing time windows based on actual arrival times

This ensures all queries are spatially and temporally realistic.
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

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.config import DATASET_DIR, QUERIES_DIR, CHECKPOINTS_DIR
from experiments.utils.logger import get_logger, get_checkpoint_manager


# =============================================================================
# Global Parameters (from the plan)
# =============================================================================

@dataclass
class QueryGenConfig:
    """Configuration for tour-based query generation."""
    # Time parameters (in minutes)
    TIME_HORIZON: int = 600  # 10 hours
    WORKING_TIME_START: int = 540  # 09:00
    WORKING_TIME_END: int = 1140   # 19:00
    RETURN_BUFFER: int = 30
    
    # Capacity and demand
    CAPACITY_MIN: int = 8
    CAPACITY_MAX: int = 12
    DEMAND_MIN: int = 1
    DEMAND_MAX: int = 5
    
    # Time window slack (in minutes)
    PICKUP_SLACK_MIN: int = 15
    PICKUP_SLACK_MAX: int = 45
    DELIVERY_SLACK_MIN: int = 15
    DELIVERY_SLACK_MAX: int = 45
    
    # Minimum separation between pickup and delivery
    MIN_PD_SEPARATION: int = 10  # minutes
    
    # Tour construction
    CANDIDATE_K: int = 50  # Number of nearest neighbors to consider (increased)
    LOCALITY_ALPHA: float = 0.1  # Lower = more exploration (was 0.5)
    MIN_TOUR_LENGTH: int = 150  # Minimum stops in tour
    
    # Experiment setup
    N_VALUES: List[int] = field(default_factory=lambda: [10, 20, 40, 60, 80, 100])
    RUNS_PER_N: int = 100
    SEED_BASE: int = 42


CONFIG = QueryGenConfig()


# =============================================================================
# Graph Data Structures
# =============================================================================

@dataclass
class GraphNode:
    """A node in the road network."""
    node_id: int
    x: float  # latitude/easting
    y: float  # longitude/northing
    
    def euclidean_distance(self, other: 'GraphNode') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


@dataclass
class GraphEdge:
    """An edge with time-dependent travel times."""
    source: int
    destination: int
    distance: float
    travel_times: Dict[int, float]  # departure_time -> travel_time
    
    def get_travel_time(self, departure_time: float) -> float:
        """Get interpolated travel time for a departure time."""
        times = sorted(self.travel_times.keys())
        
        if not times:
            return self.distance / 50 * 60  # Fallback: 50 units/hour
        
        # Find bracketing time points
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
        
        # Linear interpolation
        t1, t2 = lower_t, upper_t
        c1, c2 = self.travel_times[t1], self.travel_times[t2]
        
        if t2 == t1:
            return c1
        
        ratio = (departure_time - t1) / (t2 - t1)
        return c1 + ratio * (c2 - c1)
    
    def get_arrival_time(self, departure_time: float) -> float:
        """Get arrival time given departure time."""
        return departure_time + self.get_travel_time(departure_time)


class RoadNetwork:
    """
    Road network graph with time-dependent edge costs.
    """
    
    def __init__(self):
        self.nodes: Dict[int, GraphNode] = {}
        self.outgoing: Dict[int, Dict[int, GraphEdge]] = defaultdict(dict)
        self.incoming: Dict[int, Dict[int, GraphEdge]] = defaultdict(dict)
        self.time_series: List[int] = []
        self.logger = get_logger("road_network")
        
    def load_from_files(self, nodes_file: Path, edges_file: Path):
        """Load graph from node and edge files."""
        
        self.logger.info(f"Loading nodes from {nodes_file}")
        
        # Load nodes
        with open(nodes_file, 'r') as f:
            for line_num, line in enumerate(f):
                parts = line.strip().split()
                if len(parts) >= 3:
                    node_id = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    self.nodes[node_id] = GraphNode(node_id, x, y)
                
                if (line_num + 1) % 50000 == 0:
                    self.logger.debug(f"Loaded {line_num + 1} nodes...")
        
        self.logger.info(f"Loaded {len(self.nodes)} nodes")
        self.logger.info(f"Loading edges from {edges_file}")
        
        # Load edges
        with open(edges_file, 'r') as f:
            # First line is time series
            first_line = f.readline().strip()
            self.time_series = [int(t) for t in first_line.split()]
            
            edge_count = 0
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    source = int(parts[0])
                    dest = int(parts[1])
                    travel_times_str = parts[2]
                    
                    # Parse travel times
                    travel_times = {}
                    costs = travel_times_str.split(',')
                    for i, cost in enumerate(costs):
                        if i < len(self.time_series):
                            travel_times[self.time_series[i]] = float(cost)
                    
                    # Calculate distance
                    if source in self.nodes and dest in self.nodes:
                        distance = self.nodes[source].euclidean_distance(self.nodes[dest])
                        
                        edge = GraphEdge(source, dest, distance, travel_times)
                        self.outgoing[source][dest] = edge
                        self.incoming[dest][source] = edge
                        edge_count += 1
                
                if edge_count % 100000 == 0 and edge_count > 0:
                    self.logger.debug(f"Loaded {edge_count} edges...")
        
        self.logger.info(f"Loaded {edge_count} edges")
    
    def get_neighbors(self, node_id: int) -> List[int]:
        """Get outgoing neighbor node IDs."""
        return list(self.outgoing.get(node_id, {}).keys())
    
    def get_edge(self, source: int, dest: int) -> Optional[GraphEdge]:
        """Get edge between two nodes."""
        return self.outgoing.get(source, {}).get(dest)
    
    def get_k_nearest(self, node_id: int, k: int = 15) -> List[Tuple[int, float]]:
        """
        Get k nearest neighbor nodes by Euclidean distance.
        Returns list of (neighbor_id, distance) sorted by distance.
        """
        if node_id not in self.nodes:
            return []
        
        source = self.nodes[node_id]
        neighbors = self.get_neighbors(node_id)
        
        if not neighbors:
            return []
        
        # Calculate distances to all neighbors
        distances = []
        for neighbor_id in neighbors:
            if neighbor_id in self.nodes:
                dist = source.euclidean_distance(self.nodes[neighbor_id])
                distances.append((neighbor_id, dist))
        
        # Sort by distance and return top k
        distances.sort(key=lambda x: x[1])
        return distances[:k]


# =============================================================================
# Time-Dependent Dijkstra
# =============================================================================

class TDDijkstra:
    """
    Time-dependent Dijkstra's algorithm for earliest arrival paths.
    """
    
    def __init__(self, network: RoadNetwork):
        self.network = network
    
    def earliest_arrival(self, source: int, target: int, 
                         departure_time: float,
                         max_time: float = float('inf')) -> Tuple[Optional[float], List[int]]:
        """
        Find earliest arrival path from source to target.
        
        Args:
            source: Starting node
            target: Destination node
            departure_time: Departure time from source
            max_time: Maximum allowed arrival time
            
        Returns:
            (arrival_time, path) or (None, []) if no path found
        """
        
        # Use A* with Euclidean heuristic for faster convergence
        source_node = self.network.nodes.get(source)
        target_node = self.network.nodes.get(target)
        
        if not source_node or not target_node:
            return None, []
        
        # Estimate max speed (about 60 km/h = 1 km/min = 1000 m/min)
        max_speed = 1000.0
        
        def heuristic(node_id):
            node = self.network.nodes.get(node_id)
            if node:
                return target_node.euclidean_distance(node) / max_speed
            return 0
        
        # Priority queue: (f_score, arrival_time, node_id)
        h0 = heuristic(source)
        pq = [(departure_time + h0, departure_time, source)]
        
        # Best arrival times
        best = {source: departure_time}
        
        # Parent pointers for path reconstruction
        parent = {source: None}
        
        # Limit iterations to prevent runaway on disconnected graphs
        max_iterations = 100000
        iterations = 0
        
        while pq and iterations < max_iterations:
            iterations += 1
            _, current_time, current = heapq.heappop(pq)
            
            # Skip if we've found a better path
            if current_time > best.get(current, float('inf')):
                continue
            
            # Found target
            if current == target:
                # Reconstruct path
                path = []
                node = target
                while node is not None:
                    path.append(node)
                    node = parent[node]
                path.reverse()
                return current_time, path
            
            # Explore neighbors
            for neighbor in self.network.get_neighbors(current):
                edge = self.network.get_edge(current, neighbor)
                if edge:
                    arrival = edge.get_arrival_time(current_time)
                    
                    if arrival <= max_time and arrival < best.get(neighbor, float('inf')):
                        best[neighbor] = arrival
                        parent[neighbor] = current
                        f_score = arrival + heuristic(neighbor)
                        heapq.heappush(pq, (f_score, arrival, neighbor))
        
        return None, []
    
    def travel_time(self, source: int, target: int, 
                    departure_time: float) -> Optional[float]:
        """Get travel time between two nodes."""
        arrival, _ = self.earliest_arrival(source, target, departure_time)
        if arrival is not None:
            return arrival - departure_time
        return None


# =============================================================================
# Tour Builder
# =============================================================================

@dataclass
class TourStop:
    """A stop on the tour with arrival time."""
    node_id: int
    arrival_time: float


class TourBuilder:
    """
    Builds a feasible time-dependent vehicle tour.
    
    The tour:
    - Starts at a random depot
    - Visits nodes while respecting time constraints
    - Returns to depot before working hours end
    """
    
    def __init__(self, network: RoadNetwork, config: QueryGenConfig = None):
        self.network = network
        self.config = config or CONFIG
        self.dijkstra = TDDijkstra(network)
        self.logger = get_logger("tour_builder")
        self.rng = random.Random()
    
    def set_seed(self, seed: int):
        """Set random seed for reproducibility."""
        self.rng = random.Random(seed)
    
    def select_depot(self) -> int:
        """Select a random depot node."""
        # Choose a node that has outgoing edges
        valid_nodes = [n for n in self.network.nodes.keys() 
                       if len(self.network.get_neighbors(n)) > 0]
        return self.rng.choice(valid_nodes)
    
    def select_next_candidate(self, current: int, 
                              visited: Set[int],
                              tour_length: int = 0) -> Optional[int]:
        """
        Select next node using proximity-weighted sampling.
        
        P(v) ∝ exp(-α * distance(u, v))
        
        If no candidates found from k-nearest, falls back to random unvisited neighbors.
        """
        
        # Try k-nearest first
        candidates = self.network.get_k_nearest(current, self.config.CANDIDATE_K)
        
        # Filter out visited nodes
        candidates = [(n, d) for n, d in candidates if n not in visited]
        
        # If k-nearest exhausted and tour is short, try direct neighbors
        if not candidates and tour_length < self.config.MIN_TOUR_LENGTH:
            neighbors = self.network.get_neighbors(current)
            unvisited_neighbors = [n for n in neighbors if n not in visited]
            if unvisited_neighbors:
                # Pick a random unvisited neighbor
                return self.rng.choice(unvisited_neighbors)
            
            # Last resort: pick any random unvisited node (for connectivity)
            # This helps "jump" to a new area of the graph
            all_nodes = list(self.network.nodes.keys())
            unvisited = [n for n in all_nodes if n not in visited and 
                         len(self.network.get_neighbors(n)) > 0]
            if unvisited:
                # Sample from unvisited nodes, preferring ones with many neighbors
                sample_size = min(100, len(unvisited))
                sample = self.rng.sample(unvisited, sample_size)
                return self.rng.choice(sample)
            return None
        
        if not candidates:
            return None
        
        # Compute weights
        alpha = self.config.LOCALITY_ALPHA
        weights = [math.exp(-alpha * d) for _, d in candidates]
        total = sum(weights)
        
        if total == 0:
            return candidates[0][0]
        
        # Sample
        r = self.rng.random() * total
        cumulative = 0
        for i, (node, _) in enumerate(candidates):
            cumulative += weights[i]
            if r <= cumulative:
                return node
        
        return candidates[-1][0]
    
    def can_return_to_depot(self, current: int, current_time: float, 
                            depot: int) -> Tuple[bool, Optional[float]]:
        """
        Check if we can return to depot in time.
        
        Returns (feasible, return_time)
        """
        arrival, _ = self.dijkstra.earliest_arrival(
            current, depot, current_time,
            max_time=self.config.WORKING_TIME_END
        )
        
        if arrival is None:
            return False, None
        
        if arrival + self.config.RETURN_BUFFER <= self.config.WORKING_TIME_END:
            return True, arrival
        
        return False, None
    
    def build_tour(self, depot: int = None, seed: int = None) -> List[TourStop]:
        """
        Build a feasible time-dependent tour.
        
        Args:
            depot: Starting/ending depot node (random if None)
            seed: Random seed
            
        Returns:
            List of TourStop (node_id, arrival_time)
        """
        
        if seed is not None:
            self.set_seed(seed)
        
        if depot is None:
            depot = self.select_depot()
        
        # Initialize
        tour = [TourStop(depot, self.config.WORKING_TIME_START)]
        current_node = depot
        current_time = float(self.config.WORKING_TIME_START)
        visited = {depot}
        
        # Increase max attempts proportionally to desired tour length
        max_attempts = max(5000, self.config.MIN_TOUR_LENGTH * 20)
        attempts = 0
        consecutive_failures = 0
        max_consecutive_failures = 100
        
        while attempts < max_attempts and consecutive_failures < max_consecutive_failures:
            attempts += 1
            
            # Select next candidate - pass current tour length for fallback logic
            next_node = self.select_next_candidate(
                current_node, visited, tour_length=len(tour)
            )
            
            if next_node is None:
                consecutive_failures += 1
                continue
            
            # Compute arrival at next node
            arrival, path = self.dijkstra.earliest_arrival(
                current_node, next_node, current_time,
                max_time=self.config.WORKING_TIME_END - self.config.RETURN_BUFFER
            )
            
            if arrival is None:
                visited.add(next_node)  # Mark as unreachable
                consecutive_failures += 1
                continue
            
            # Check if we can still return to depot after visiting next_node
            can_return, return_time = self.can_return_to_depot(
                next_node, arrival, depot
            )
            
            if not can_return:
                visited.add(next_node)
                consecutive_failures += 1
                continue
            
            # Reset consecutive failures - we found a valid move
            consecutive_failures = 0
            
            # Accept move - add intermediate nodes from path
            for i, path_node in enumerate(path[1:], 1):
                # Calculate arrival at this intermediate node
                if i < len(path) - 1:
                    # Intermediate node - estimate time proportionally
                    progress = i / (len(path) - 1)
                    node_arrival = current_time + progress * (arrival - current_time)
                else:
                    node_arrival = arrival
                
                tour.append(TourStop(path_node, node_arrival))
                visited.add(path_node)
            
            current_node = next_node
            current_time = arrival
        
        # Return to depot
        if current_node != depot:
            arrival, path = self.dijkstra.earliest_arrival(
                current_node, depot, current_time
            )
            if arrival is not None and len(path) > 1:
                for path_node in path[1:]:
                    tour.append(TourStop(path_node, arrival))
        
        return tour


# =============================================================================
# Request Generator
# =============================================================================

@dataclass
class ServiceRequest:
    """A pickup-delivery service request."""
    pickup_node: int
    delivery_node: int
    pickup_start: int
    pickup_end: int
    delivery_start: int
    delivery_end: int
    demand: int
    
    # Metadata
    pickup_tour_index: int = -1
    delivery_tour_index: int = -1
    
    def to_string(self) -> str:
        return (f"S {self.pickup_node},{self.delivery_node} "
                f"{self.pickup_start},{self.pickup_end} "
                f"{self.delivery_start},{self.delivery_end} "
                f"{self.demand}")


@dataclass
class GeneratedQuery:
    """A complete VRP-LU query."""
    query_id: int
    depot_node: int
    capacity: int
    services: List[ServiceRequest]
    seed: int
    n_requests: int
    tour_length: int
    
    def to_string(self) -> str:
        lines = [f"D {self.depot_node}", f"C {self.capacity}"]
        for service in self.services:
            lines.append(service.to_string())
        return "\n".join(lines)
    
    def to_meta_dict(self) -> dict:
        return {
            "query_id": self.query_id,
            "depot_node": self.depot_node,
            "capacity": self.capacity,
            "seed": self.seed,
            "n_requests": self.n_requests,
            "tour_length": self.tour_length,
            "services": [
                {
                    "pickup_node": s.pickup_node,
                    "delivery_node": s.delivery_node,
                    "pickup_window": [s.pickup_start, s.pickup_end],
                    "delivery_window": [s.delivery_start, s.delivery_end],
                    "demand": s.demand,
                    "pickup_tour_index": s.pickup_tour_index,
                    "delivery_tour_index": s.delivery_tour_index,
                }
                for s in self.services
            ]
        }


class RequestGenerator:
    """
    Generates pickup-delivery requests from a tour.
    
    Ensures:
    - Pickup index < delivery index on tour
    - Reasonable time windows centered on arrival times
    - Valid demands
    """
    
    def __init__(self, config: QueryGenConfig = None):
        self.config = config or CONFIG
        self.rng = random.Random()
        self.logger = get_logger("request_generator")
    
    def set_seed(self, seed: int):
        self.rng = random.Random(seed)
    
    def generate_requests(self, tour: List[TourStop], 
                          n_requests: int) -> List[ServiceRequest]:
        """
        Generate n pickup-delivery requests from the tour.
        
        Args:
            tour: List of TourStop from tour builder
            n_requests: Number of requests to generate
            
        Returns:
            List of ServiceRequest
        """
        
        if len(tour) < 4:  # Need at least depot + 2 stops + depot
            self.logger.warning(f"Tour too short ({len(tour)}), cannot generate requests")
            return []
        
        # Exclude first and last stops (depot)
        valid_indices = list(range(1, len(tour) - 1))
        
        if len(valid_indices) < 2:
            self.logger.warning("Not enough tour stops for requests")
            return []
        
        requests = []
        used_pairs = set()
        max_attempts = n_requests * 10
        attempts = 0
        
        while len(requests) < n_requests and attempts < max_attempts:
            attempts += 1
            
            # Sample pickup index
            if len(valid_indices) < 2:
                break
            
            i = self.rng.choice(valid_indices[:-1])  # Not the last valid index
            
            # Sample delivery index > pickup index
            valid_j = [j for j in valid_indices if j > i]
            if not valid_j:
                continue
            
            j = self.rng.choice(valid_j)
            
            # Check separation
            pickup_time = tour[i].arrival_time
            delivery_time = tour[j].arrival_time
            
            if delivery_time - pickup_time < self.config.MIN_PD_SEPARATION:
                continue
            
            # Avoid duplicate pairs
            pair_key = (tour[i].node_id, tour[j].node_id)
            if pair_key in used_pairs:
                continue
            used_pairs.add(pair_key)
            
            # Create request
            request = self._create_request(tour[i], tour[j], i, j)
            if request:
                requests.append(request)
        
        return requests
    
    def _create_request(self, pickup_stop: TourStop, delivery_stop: TourStop,
                        pickup_idx: int, delivery_idx: int) -> Optional[ServiceRequest]:
        """Create a service request with time windows."""
        
        # Sample slacks
        p_slack = self.rng.randint(self.config.PICKUP_SLACK_MIN, 
                                   self.config.PICKUP_SLACK_MAX)
        d_slack = self.rng.randint(self.config.DELIVERY_SLACK_MIN, 
                                   self.config.DELIVERY_SLACK_MAX)
        
        # Pickup time window centered on arrival
        p_start = max(self.config.WORKING_TIME_START, 
                     int(pickup_stop.arrival_time - p_slack / 2))
        p_end = min(self.config.WORKING_TIME_END,
                   int(pickup_stop.arrival_time + p_slack / 2))
        
        # Delivery time window centered on arrival, but after pickup
        d_center = delivery_stop.arrival_time
        d_start = max(p_end + 1, int(d_center - d_slack / 2))
        d_end = min(self.config.WORKING_TIME_END,
                   int(d_center + d_slack / 2))
        
        # Validate
        if p_start >= p_end or d_start >= d_end or d_start <= p_start:
            return None
        
        # Sample demand
        demand = self.rng.randint(self.config.DEMAND_MIN, self.config.DEMAND_MAX)
        
        return ServiceRequest(
            pickup_node=pickup_stop.node_id,
            delivery_node=delivery_stop.node_id,
            pickup_start=p_start,
            pickup_end=p_end,
            delivery_start=d_start,
            delivery_end=d_end,
            demand=demand,
            pickup_tour_index=pickup_idx,
            delivery_tour_index=delivery_idx
        )


# =============================================================================
# Main Query Generator
# =============================================================================

class TourBasedQueryGenerator:
    """
    Main class for generating VRP-LU queries using tour-based approach.
    """
    
    def __init__(self, config: QueryGenConfig = None):
        self.config = config or CONFIG
        self.logger = get_logger("tour_query_generator")
        self.network = None
        self.tour_builder = None
        self.request_gen = None
    
    def load_network(self, nodes_file: Path = None, edges_file: Path = None):
        """Load the road network."""
        
        if nodes_file is None:
            nodes_file = DATASET_DIR / "nodes_285050.txt"
        if edges_file is None:
            edges_file = DATASET_DIR / "edges_285050.txt"
        
        self.logger.info("Loading road network...")
        self.network = RoadNetwork()
        self.network.load_from_files(nodes_file, edges_file)
        
        self.tour_builder = TourBuilder(self.network, self.config)
        self.request_gen = RequestGenerator(self.config)
        
        self.logger.info(f"Network loaded: {len(self.network.nodes)} nodes")
    
    def generate_query(self, n_requests: int, query_id: int, 
                       seed: int) -> Optional[GeneratedQuery]:
        """
        Generate a single query with n pickup-delivery requests.
        
        Args:
            n_requests: Number of service requests (N)
            query_id: Query identifier
            seed: Random seed for reproducibility
            
        Returns:
            GeneratedQuery or None if generation fails
        """
        
        if self.network is None:
            self.logger.error("Network not loaded. Call load_network() first.")
            return None
        
        # Set seeds
        self.tour_builder.set_seed(seed)
        self.request_gen.set_seed(seed + 1000)
        rng = random.Random(seed + 2000)
        
        # Build tour
        tour = self.tour_builder.build_tour(seed=seed)
        
        if len(tour) < n_requests + 2:
            self.logger.warning(
                f"Query {query_id}: Tour too short ({len(tour)}) for {n_requests} requests"
            )
            # Try to build a longer tour with different depot
            for attempt in range(5):
                tour = self.tour_builder.build_tour(seed=seed + attempt * 100)
                if len(tour) >= n_requests + 2:
                    break
        
        if len(tour) < 4:
            self.logger.error(f"Query {query_id}: Could not build valid tour")
            return None
        
        # Generate requests
        services = self.request_gen.generate_requests(tour, n_requests)
        
        if len(services) < n_requests:
            self.logger.warning(
                f"Query {query_id}: Only generated {len(services)}/{n_requests} requests"
            )
        
        if not services:
            self.logger.error(f"Query {query_id}: No services generated")
            return None
        
        # Assign capacity
        capacity = rng.randint(self.config.CAPACITY_MIN, self.config.CAPACITY_MAX)
        
        return GeneratedQuery(
            query_id=query_id,
            depot_node=tour[0].node_id,
            capacity=capacity,
            services=services,
            seed=seed,
            n_requests=len(services),
            tour_length=len(tour)
        )
    
    def generate_all_queries(self, checkpoint_manager=None) -> Dict:
        """
        Generate all queries according to experiment design.
        
        For each N in N_VALUES:
            For run = 1..RUNS_PER_N:
                Generate query with deterministic seed
        """
        
        self.logger.section("Tour-Based Query Generation")
        
        if self.network is None:
            self.load_network()
        
        generated = {}
        total = len(self.config.N_VALUES) * self.config.RUNS_PER_N
        completed = 0
        
        for N in self.config.N_VALUES:
            self.logger.subsection(f"Generating queries for N = {N}")
            
            # Create directory
            n_dir = QUERIES_DIR / f"N_{N}"
            n_dir.mkdir(parents=True, exist_ok=True)
            
            for run in range(1, self.config.RUNS_PER_N + 1):
                query_key = f"N{N}_R{run}"
                
                # Check checkpoint
                if checkpoint_manager and checkpoint_manager.is_item_completed(f"query_{query_key}"):
                    self.logger.debug(f"Skipping {query_key} (already done)")
                    completed += 1
                    continue
                
                # Deterministic seed
                seed = self.config.SEED_BASE * 10000 + N * 100 + run
                
                # Generate query
                query = self.generate_query(N, query_id=run, seed=seed)
                
                if query is None:
                    self.logger.error(f"Failed to generate {query_key}")
                    if checkpoint_manager:
                        checkpoint_manager.mark_item_failed(f"query_{query_key}", "Generation failed")
                    continue
                
                # Save query file
                query_file = n_dir / f"query_{run}.txt"
                with open(query_file, 'w') as f:
                    f.write(query.to_string())
                
                # Save metadata
                meta_file = n_dir / f"query_{run}_meta.json"
                with open(meta_file, 'w') as f:
                    json.dump(query.to_meta_dict(), f, indent=2)
                
                generated[query_key] = str(query_file)
                
                if checkpoint_manager:
                    checkpoint_manager.mark_item_completed(f"query_{query_key}")
                
                completed += 1
                
                if completed % 50 == 0 or completed == total:
                    self.logger.info(f"Progress: {completed}/{total} queries")
        
        # Save index
        index_file = QUERIES_DIR / "query_index.json"
        with open(index_file, 'w') as f:
            json.dump(generated, f, indent=2)
        
        self.logger.info(f"Generation complete. Total: {len(generated)} queries")
        
        if checkpoint_manager:
            checkpoint_manager.complete_phase("phase_c_tour_query_generation")
        
        return generated


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Tour-based VRP-LU query generator"
    )
    parser.add_argument("--n-values", type=int, nargs="+", default=None,
                       help="N values (number of requests)")
    parser.add_argument("--runs", type=int, default=None,
                       help="Runs per N value")
    parser.add_argument("--seed", type=int, default=42,
                       help="Base random seed")
    parser.add_argument("--reset", action="store_true",
                       help="Reset checkpoint")
    parser.add_argument("--test", action="store_true",
                       help="Test mode: generate 1 query with N=10")
    
    args = parser.parse_args()
    
    # Update config
    if args.n_values:
        CONFIG.N_VALUES = args.n_values
    if args.runs:
        CONFIG.RUNS_PER_N = args.runs
    CONFIG.SEED_BASE = args.seed
    
    # Checkpoint
    checkpoint = get_checkpoint_manager("tour_query_generation")
    
    if args.reset:
        checkpoint.reset()
        print("Checkpoint reset.")
    
    # Test mode
    if args.test:
        print("Test mode: generating 1 query with N=10")
        CONFIG.N_VALUES = [10]
        CONFIG.RUNS_PER_N = 1
    
    # Generate
    generator = TourBasedQueryGenerator(CONFIG)
    queries = generator.generate_all_queries(checkpoint)
    
    print(f"\nGenerated {len(queries)} queries")
    print(f"Saved to: {QUERIES_DIR}")
    
    # Show sample
    if queries:
        sample_key = list(queries.keys())[0]
        sample_path = queries[sample_key]
        print(f"\nSample query ({sample_key}):")
        with open(sample_path, 'r') as f:
            print(f.read()[:500])


if __name__ == "__main__":
    main()
