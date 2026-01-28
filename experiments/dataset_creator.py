#!/usr/bin/env python3
"""
Dataset Creation Logic for VRP-LU Optimization Problems
========================================================

This module provides comprehensive utilities for:
1. Creating synthetic road networks (nodes and edges)
2. Generating realistic service request queries
3. Validating dataset integrity
4. Transforming existing datasets (subgraph extraction, format conversion)
"""

import random
import math
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import csv


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logger(name: str) -> logging.Logger:
    """Configure logger for dataset creation."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Node:
    """Represents a location in the road network."""
    node_id: int
    x: float
    y: float
    
    def euclidean_distance(self, other: 'Node') -> float:
        """Calculate Euclidean distance to another node."""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def to_csv_row(self) -> str:
        """Convert to CSV format for nodes file."""
        return f"{self.node_id} {self.x} {self.y}"


@dataclass
class Edge:
    """Represents a directed edge in the road network."""
    source: int
    destination: int
    costs: List[float]  # Time-dependent costs for different periods
    
    def to_csv_row(self) -> str:
        """Convert to CSV format for edges file."""
        cost_str = ",".join(f"{c:.6f}" for c in self.costs)
        return f"{self.source} {self.destination} {cost_str}"


@dataclass
class Service:
    """Represents a pickup-delivery service request."""
    service_id: int
    pickup_node: int
    delivery_node: int
    demand: int
    pickup_start: int
    pickup_end: int
    delivery_start: int
    delivery_end: int
    
    def to_query_row(self) -> str:
        """Convert to query file format."""
        return (f"S {self.pickup_node},{self.delivery_node} "
                f"[{self.pickup_start},{self.pickup_end}] "
                f"[{self.delivery_start},{self.delivery_end}] {self.demand}")


@dataclass
class Query:
    """Represents a complete routing query/problem instance."""
    query_id: int
    depot_node: int
    capacity: int
    services: List[Service]
    metadata: Dict = field(default_factory=dict)
    
    def to_query_file_content(self) -> str:
        """Generate complete query file content."""
        lines = [f"D {self.depot_node}", f"C {self.capacity}"]
        lines.extend(s.to_query_row() for s in self.services)
        return "\n".join(lines) + "\n"
    
    def to_metadata(self) -> Dict:
        """Generate metadata dictionary."""
        return {
            'query_id': self.query_id,
            'depot_node': self.depot_node,
            'capacity': self.capacity,
            'n_requests': len(self.services),
            'demand_range': [min(s.demand for s in self.services),
                            max(s.demand for s in self.services)],
            'time_window_stats': {
                'pickup_range': [min(s.pickup_start for s in self.services),
                                max(s.pickup_end for s in self.services)],
                'delivery_range': [min(s.delivery_start for s in self.services),
                                  max(s.delivery_end for s in self.services)]
            },
            **self.metadata
        }


@dataclass
class DatasetConfig:
    """Configuration for dataset generation."""
    # Nodes generation
    num_nodes: int = 100
    x_bounds: Tuple[float, float] = (0.0, 100.0)
    y_bounds: Tuple[float, float] = (0.0, 100.0)
    node_seed: int = 42
    
    # Edges generation
    edge_density: float = 0.1  # Fraction of possible edges
    time_periods: int = 4
    min_speed: float = 40.0  # mph
    max_speed: float = 55.0  # mph
    edge_seed: int = 42
    
    # Query generation
    n_requests: int = 20
    num_queries: int = 10
    capacity_min: int = 8
    capacity_max: int = 12
    demand_min: int = 1
    demand_max: int = 5
    
    # Time windows
    working_time_start: int = 540   # 09:00 (minutes)
    working_time_end: int = 1140    # 19:00 (minutes)
    pickup_slack_min: int = 15
    pickup_slack_max: int = 45
    delivery_slack_min: int = 15
    delivery_slack_max: int = 45
    min_pd_separation: int = 10
    
    # Query generation
    query_seed: int = 42


# =============================================================================
# NETWORK GENERATION
# =============================================================================

class NodeGenerator:
    """Generates synthetic node coordinates."""
    
    def __init__(self, config: DatasetConfig, logger: logging.Logger = None):
        self.config = config
        self.logger = logger or setup_logger(__name__)
        self.nodes: Dict[int, Node] = {}
    
    def generate_uniform_random(self) -> Dict[int, Node]:
        """Generate nodes uniformly at random in 2D space."""
        random.seed(self.config.node_seed)
        self.logger.info(f"Generating {self.config.num_nodes} nodes (uniform random)...")
        
        x_min, x_max = self.config.x_bounds
        y_min, y_max = self.config.y_bounds
        
        for node_id in range(self.config.num_nodes):
            x = random.uniform(x_min, x_max)
            y = random.uniform(y_min, y_max)
            self.nodes[node_id] = Node(node_id, x, y)
        
        self.logger.info(f"✓ Generated {len(self.nodes)} nodes")
        return self.nodes
    
    def generate_clustered(self, num_clusters: int = 5) -> Dict[int, Node]:
        """Generate nodes in clusters (more realistic)."""
        random.seed(self.config.node_seed)
        self.logger.info(f"Generating {self.config.num_nodes} nodes ({num_clusters} clusters)...")
        
        x_min, x_max = self.config.x_bounds
        y_min, y_max = self.config.y_bounds
        
        # Generate cluster centers
        cluster_centers = []
        for _ in range(num_clusters):
            cx = random.uniform(x_min, x_max)
            cy = random.uniform(y_min, y_max)
            cluster_centers.append((cx, cy))
        
        # Assign nodes to clusters
        nodes_per_cluster = self.config.num_nodes // num_clusters
        node_id = 0
        
        for cluster_idx, (cx, cy) in enumerate(cluster_centers):
            cluster_size = nodes_per_cluster
            if cluster_idx == num_clusters - 1:
                cluster_size = self.config.num_nodes - node_id  # Last cluster gets remainder
            
            # Generate nodes around cluster center
            cluster_radius = min(x_max - x_min, y_max - y_min) / (2 * num_clusters)
            
            for _ in range(cluster_size):
                angle = random.uniform(0, 2 * math.pi)
                radius = random.uniform(0, cluster_radius)
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                
                # Clamp to bounds
                x = max(x_min, min(x_max, x))
                y = max(y_min, min(y_max, y))
                
                self.nodes[node_id] = Node(node_id, x, y)
                node_id += 1
        
        self.logger.info(f"✓ Generated {len(self.nodes)} nodes in {num_clusters} clusters")
        return self.nodes
    
    def load_from_file(self, nodes_file: Path) -> Dict[int, Node]:
        """Load nodes from existing file."""
        self.logger.info(f"Loading nodes from {nodes_file}")
        
        with open(nodes_file, 'r') as f:
            for line_num, line in enumerate(f):
                parts = line.strip().split()
                if len(parts) >= 3:
                    node_id = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    self.nodes[node_id] = Node(node_id, x, y)
                
                if (line_num + 1) % 50000 == 0:
                    self.logger.debug(f"Loaded {line_num + 1} nodes...")
        
        self.logger.info(f"✓ Loaded {len(self.nodes)} nodes")
        return self.nodes
    
    def save_to_file(self, output_path: Path) -> None:
        """Save nodes to file."""
        self.logger.info(f"Saving {len(self.nodes)} nodes to {output_path}")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            for node_id in sorted(self.nodes.keys()):
                f.write(self.nodes[node_id].to_csv_row() + "\n")
        
        self.logger.info(f"✓ Saved nodes to {output_path}")


class EdgeGenerator:
    """Generates edges for road network."""
    
    def __init__(self, nodes: Dict[int, Node], config: DatasetConfig,
                 logger: logging.Logger = None):
        self.nodes = nodes
        self.config = config
        self.logger = logger or setup_logger(__name__)
        self.edges: Dict[Tuple[int, int], Edge] = {}
    
    def generate_k_nearest_neighbors(self, k: int = 10) -> Dict[Tuple[int, int], Edge]:
        """Generate edges using k-nearest neighbors."""
        random.seed(self.config.edge_seed)
        self.logger.info(f"Generating edges using k-nearest neighbors (k={k})...")
        
        edge_count = 0
        
        for source_id, source_node in self.nodes.items():
            # Find k nearest neighbors
            distances = []
            for dest_id, dest_node in self.nodes.items():
                if dest_id != source_id:
                    dist = source_node.euclidean_distance(dest_node)
                    distances.append((dist, dest_id))
            
            distances.sort()
            k_nearest = distances[:min(k, len(distances))]
            
            # Add edges to k nearest neighbors
            for _, dest_id in k_nearest:
                edge = self._create_edge(source_id, dest_id)
                self.edges[(source_id, dest_id)] = edge
                edge_count += 1
            
            if (source_id + 1) % 100 == 0:
                self.logger.debug(f"Processed {source_id + 1} source nodes...")
        
        self.logger.info(f"✓ Generated {edge_count} edges")
        return self.edges
    
    def generate_random_edges(self) -> Dict[Tuple[int, int], Edge]:
        """Generate random edges with specified density."""
        random.seed(self.config.edge_seed)
        self.logger.info(f"Generating edges with density {self.config.edge_density}...")
        
        node_list = list(self.nodes.keys())
        edge_count = 0
        
        for source_id in node_list:
            for dest_id in node_list:
                if source_id != dest_id and random.random() < self.config.edge_density:
                    edge = self._create_edge(source_id, dest_id)
                    self.edges[(source_id, dest_id)] = edge
                    edge_count += 1
        
        self.logger.info(f"✓ Generated {edge_count} edges")
        return self.edges
    
    def _create_edge(self, source_id: int, dest_id: int) -> Edge:
        """Create edge with time-dependent costs."""
        source = self.nodes[source_id]
        dest = self.nodes[dest_id]
        
        distance = source.euclidean_distance(dest)
        
        # Generate time-dependent costs (same distance, varying speeds)
        costs = []
        for _ in range(self.config.time_periods):
            speed = random.uniform(self.config.min_speed, self.config.max_speed)
            cost = distance / speed  # Time cost
            costs.append(cost)
        
        return Edge(source_id, dest_id, costs)
    
    def load_from_file(self, edges_file: Path) -> Dict[Tuple[int, int], Edge]:
        """Load edges from existing file."""
        self.logger.info(f"Loading edges from {edges_file}")
        
        with open(edges_file, 'r') as f:
            # First line is time series
            first_line = f.readline().strip()
            self.config.time_periods = len(first_line.split())
            
            # Load edges
            edge_count = 0
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    source = int(parts[0])
                    dest = int(parts[1])
                    
                    # Parse time-dependent costs
                    cost_str = parts[2]
                    costs = [float(c) for c in cost_str.split(',')]
                    
                    self.edges[(source, dest)] = Edge(source, dest, costs)
                    edge_count += 1
                
                if (edge_count + 1) % 100000 == 0:
                    self.logger.debug(f"Loaded {edge_count} edges...")
        
        self.logger.info(f"✓ Loaded {edge_count} edges")
        return self.edges
    
    def save_to_file(self, output_path: Path) -> None:
        """Save edges to file."""
        self.logger.info(f"Saving {len(self.edges)} edges to {output_path}")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            # Write time series header
            time_series = " ".join(str(p * 30) for p in range(self.config.time_periods))
            f.write(time_series + "\n")
            
            # Write edges
            for (source, dest) in sorted(self.edges.keys()):
                f.write(self.edges[(source, dest)].to_csv_row() + "\n")
        
        self.logger.info(f"✓ Saved edges to {output_path}")


# =============================================================================
# QUERY GENERATION
# =============================================================================

class QueryGenerator:
    """Generates realistic service request queries."""
    
    def __init__(self, nodes: Dict[int, Node], config: DatasetConfig,
                 logger: logging.Logger = None):
        self.nodes = nodes
        self.config = config
        self.logger = logger or setup_logger(__name__)
        self.rng = random.Random(config.query_seed)
    
    def generate_query(self, query_id: int) -> Query:
        """Generate a single query."""
        # Select depot
        depot = self.rng.choice(list(self.nodes.keys()))
        
        # Generate capacity
        capacity = self.rng.randint(
            self.config.capacity_min,
            self.config.capacity_max
        )
        
        # Generate services
        services = self._generate_services()
        
        query = Query(
            query_id=query_id,
            depot_node=depot,
            capacity=capacity,
            services=services,
            metadata={
                'generation_method': 'random_realistic',
                'seed': self.config.query_seed + query_id
            }
        )
        
        return query
    
    def _generate_services(self) -> List[Service]:
        """Generate service requests for a query."""
        services = []
        node_list = list(self.nodes.keys())
        
        for service_id in range(self.config.n_requests):
            # Ensure pickup and delivery nodes are different
            pickup = self.rng.choice(node_list)
            delivery = self.rng.choice([n for n in node_list if n != pickup])
            
            demand = self.rng.randint(self.config.demand_min, self.config.demand_max)
            
            # Generate time windows
            pickup_start = self.rng.randint(
                self.config.working_time_start,
                self.config.working_time_end - 100
            )
            pickup_slack = self.rng.randint(
                self.config.pickup_slack_min,
                self.config.pickup_slack_max
            )
            pickup_end = min(pickup_start + pickup_slack, self.config.working_time_end)
            
            # Delivery window after pickup window
            delivery_start = pickup_end + self.config.min_pd_separation
            delivery_slack = self.rng.randint(
                self.config.delivery_slack_min,
                self.config.delivery_slack_max
            )
            delivery_end = min(delivery_start + delivery_slack, self.config.working_time_end)
            
            service = Service(
                service_id=service_id,
                pickup_node=pickup,
                delivery_node=delivery,
                demand=demand,
                pickup_start=pickup_start,
                pickup_end=pickup_end,
                delivery_start=delivery_start,
                delivery_end=delivery_end
            )
            services.append(service)
        
        return services
    
    def generate_queries(self, num_queries: int = None) -> List[Query]:
        """Generate multiple queries."""
        num_queries = num_queries or self.config.num_queries
        self.logger.info(f"Generating {num_queries} queries...")
        
        queries = []
        for query_id in range(num_queries):
            query = self.generate_query(query_id + 1)
            queries.append(query)
            
            if (query_id + 1) % max(1, num_queries // 10) == 0:
                self.logger.debug(f"Generated {query_id + 1}/{num_queries} queries")
        
        self.logger.info(f"✓ Generated {len(queries)} queries")
        return queries
    
    def save_queries(self, queries: List[Query], output_dir: Path) -> None:
        """Save queries to files."""
        self.logger.info(f"Saving {len(queries)} queries to {output_dir}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for query in queries:
            # Save query file
            query_file = output_dir / f"query_{query.query_id}.txt"
            with open(query_file, 'w') as f:
                f.write(query.to_query_file_content())
            
            # Save metadata file
            meta_file = output_dir / f"query_{query.query_id}_meta.json"
            with open(meta_file, 'w') as f:
                json.dump(query.to_metadata(), f, indent=2)
        
        self.logger.info(f"✓ Saved {len(queries)} queries")


# =============================================================================
# DATASET VALIDATION
# =============================================================================

class DatasetValidator:
    """Validates dataset integrity and consistency."""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or setup_logger(__name__)
        self.errors = []
        self.warnings = []
    
    def validate_nodes(self, nodes: Dict[int, Node]) -> bool:
        """Validate node consistency."""
        self.logger.info(f"Validating {len(nodes)} nodes...")
        
        # Check for duplicate node IDs
        if len(nodes) != len(set(nodes.keys())):
            self.errors.append("Duplicate node IDs found")
            return False
        
        # Check for reasonable coordinates
        for node_id, node in nodes.items():
            if math.isnan(node.x) or math.isnan(node.y):
                self.errors.append(f"Node {node_id} has NaN coordinates")
                return False
            
            if math.isinf(node.x) or math.isinf(node.y):
                self.errors.append(f"Node {node_id} has infinite coordinates")
                return False
        
        self.logger.info("✓ Nodes validation passed")
        return True
    
    def validate_edges(self, edges: Dict[Tuple[int, int], Edge],
                      nodes: Dict[int, Node]) -> bool:
        """Validate edge consistency."""
        self.logger.info(f"Validating {len(edges)} edges...")
        
        valid_node_ids = set(nodes.keys())
        
        for (source, dest), edge in edges.items():
            # Check nodes exist
            if source not in valid_node_ids:
                self.errors.append(f"Edge source node {source} not in nodes")
                return False
            if dest not in valid_node_ids:
                self.errors.append(f"Edge dest node {dest} not in nodes")
                return False
            
            # Check costs are positive
            for cost in edge.costs:
                if cost <= 0:
                    self.errors.append(f"Edge {source}->{dest} has non-positive cost {cost}")
                    return False
        
        self.logger.info("✓ Edges validation passed")
        return True
    
    def validate_query(self, query: Query, nodes: Dict[int, Node]) -> bool:
        """Validate query consistency."""
        valid_node_ids = set(nodes.keys())
        
        # Check depot exists
        if query.depot_node not in valid_node_ids:
            self.errors.append(f"Query {query.query_id}: depot node not found")
            return False
        
        # Check services
        for service in query.services:
            if service.pickup_node not in valid_node_ids:
                self.errors.append(f"Query {query.query_id}: pickup node not found")
                return False
            
            if service.delivery_node not in valid_node_ids:
                self.errors.append(f"Query {query.query_id}: delivery node not found")
                return False
            
            # Check time windows
            if service.pickup_start >= service.pickup_end:
                self.errors.append(
                    f"Query {query.query_id}: invalid pickup time window"
                )
                return False
            
            if service.delivery_start >= service.delivery_end:
                self.errors.append(
                    f"Query {query.query_id}: invalid delivery time window"
                )
                return False
            
            if service.pickup_end > service.delivery_start:
                self.errors.append(
                    f"Query {query.query_id}: delivery must start after pickup ends"
                )
                return False
            
            # Check demand
            if service.demand <= 0 or service.demand > query.capacity:
                self.errors.append(
                    f"Query {query.query_id}: invalid demand {service.demand}"
                )
                return False
        
        return True
    
    def report(self) -> None:
        """Print validation report."""
        if self.errors:
            self.logger.error(f"Validation FAILED with {len(self.errors)} errors:")
            for error in self.errors:
                self.logger.error(f"  - {error}")
        
        if self.warnings:
            for warning in self.warnings:
                self.logger.warning(f"  - {warning}")
        
        if not self.errors:
            self.logger.info("✓ All validations passed")


# =============================================================================
# DATASET CREATION ORCHESTRATOR
# =============================================================================

class DatasetCreator:
    """Main interface for creating complete datasets."""
    
    def __init__(self, config: DatasetConfig, output_dir: Path,
                 logger: logging.Logger = None):
        self.config = config
        self.output_dir = output_dir
        self.logger = logger or setup_logger(__name__)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_synthetic_dataset(self) -> Tuple[Dict[int, Node], Dict[Tuple[int, int], Edge]]:
        """Create complete synthetic dataset."""
        self.logger.info("=" * 70)
        self.logger.info("CREATING SYNTHETIC DATASET")
        self.logger.info("=" * 70)
        
        # Generate nodes
        node_gen = NodeGenerator(self.config, self.logger)
        nodes = node_gen.generate_clustered(num_clusters=5)
        node_gen.save_to_file(self.output_dir / "nodes.txt")
        
        # Generate edges
        edge_gen = EdgeGenerator(nodes, self.config, self.logger)
        edges = edge_gen.generate_k_nearest_neighbors(k=10)
        edge_gen.save_to_file(self.output_dir / "edges.txt")
        
        # Validate
        validator = DatasetValidator(self.logger)
        validator.validate_nodes(nodes)
        validator.validate_edges(edges, nodes)
        validator.report()
        
        return nodes, edges
    
    def create_queries(self, nodes: Dict[int, Node], num_queries: int = None) -> List[Query]:
        """Create queries for dataset."""
        self.logger.info("=" * 70)
        self.logger.info("CREATING QUERIES")
        self.logger.info("=" * 70)
        
        query_gen = QueryGenerator(nodes, self.config, self.logger)
        queries = query_gen.generate_queries(num_queries or self.config.num_queries)
        
        # Validate queries
        validator = DatasetValidator(self.logger)
        for query in queries:
            validator.validate_query(query, nodes)
        validator.report()
        
        # Save queries
        queries_dir = self.output_dir / "queries"
        query_gen.save_queries(queries, queries_dir)
        
        return queries
    
    def create_complete_dataset(self) -> None:
        """Create complete dataset (nodes, edges, queries)."""
        nodes, edges = self.create_synthetic_dataset()
        self.create_queries(nodes)
        
        self.logger.info("=" * 70)
        self.logger.info("DATASET CREATION COMPLETE")
        self.logger.info("=" * 70)
        self.logger.info(f"Output directory: {self.output_dir}")
        self.logger.info(f"  - Nodes: {len(nodes)}")
        self.logger.info(f"  - Edges: {len(edges)}")
        self.logger.info(f"  - Queries: {self.config.num_queries}")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_standard_dataset(size: str = 'small',
                           output_dir: Optional[Path] = None) -> Path:
    """Create standard dataset configuration."""
    configs = {
        'small': DatasetConfig(
            num_nodes=100,
            num_queries=5,
            n_requests=10
        ),
        'medium': DatasetConfig(
            num_nodes=500,
            num_queries=10,
            n_requests=20
        ),
        'large': DatasetConfig(
            num_nodes=1000,
            num_queries=20,
            n_requests=30
        )
    }
    
    config = configs.get(size)
    if not config:
        raise ValueError(f"Unknown dataset size: {size}")
    
    if output_dir is None:
        output_dir = Path(f"dataset_{size}")
    
    creator = DatasetCreator(config, output_dir)
    creator.create_complete_dataset()
    
    return output_dir


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        size = sys.argv[1]
    else:
        size = 'small'
    
    create_standard_dataset(size)
