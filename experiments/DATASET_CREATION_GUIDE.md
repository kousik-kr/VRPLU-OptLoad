# Dataset Creation Logic - Usage Guide

## Overview

The `dataset_creator.py` module provides a complete framework for:
1. **Generating synthetic road networks** with realistic node coordinates and edge weights
2. **Creating service request queries** with time window and demand constraints
3. **Validating dataset integrity** before use
4. **Loading existing datasets** for processing

## Core Components

### 1. Data Structures

#### `Node`
Represents a location in the road network.
```python
@dataclass
class Node:
    node_id: int      # Unique identifier
    x: float          # X coordinate
    y: float          # Y coordinate
```

#### `Edge`
Represents a directed road connection with time-dependent costs.
```python
@dataclass
class Edge:
    source: int                    # Source node ID
    destination: int               # Destination node ID
    costs: List[float]            # Time-dependent costs for 4 time periods
```

#### `Service`
Represents a single pickup-delivery service request.
```python
@dataclass
class Service:
    service_id: int           # Unique ID within query
    pickup_node: int          # Where to pick up
    delivery_node: int        # Where to deliver
    demand: int               # Units to carry (1-5)
    pickup_start: int         # Earliest pickup time (minutes from midnight)
    pickup_end: int           # Latest pickup time
    delivery_start: int       # Earliest delivery time
    delivery_end: int         # Latest delivery time
```

#### `Query`
Represents a complete routing problem instance.
```python
@dataclass
class Query:
    query_id: int             # Unique query identifier
    depot_node: int           # Starting location
    capacity: int             # Vehicle capacity (8-12 units)
    services: List[Service]   # Services to satisfy
```

#### `DatasetConfig`
Configuration for dataset generation.
```python
@dataclass
class DatasetConfig:
    # Network generation
    num_nodes: int = 100
    x_bounds: Tuple[float, float] = (0.0, 100.0)
    y_bounds: Tuple[float, float] = (0.0, 100.0)
    
    # Edges
    edge_density: float = 0.1  # 10% of possible edges
    time_periods: int = 4      # Morning, midday, afternoon, evening
    
    # Queries
    n_requests: int = 20       # Services per query
    num_queries: int = 10      # Number of problem instances
    capacity_min: int = 8
    capacity_max: int = 12
    demand_min: int = 1
    demand_max: int = 5
```

---

## Usage Examples

### Quick Start: Create Standard Dataset

```python
from experiments.dataset_creator import create_standard_dataset

# Create small dataset (100 nodes, 5 queries, 10 requests each)
output_dir = create_standard_dataset('small')

# Create medium dataset (500 nodes, 10 queries, 20 requests each)
output_dir = create_standard_dataset('medium')

# Create large dataset (1000 nodes, 20 queries, 30 requests each)
output_dir = create_standard_dataset('large')
```

### Custom Configuration

```python
from experiments.dataset_creator import DatasetConfig, DatasetCreator
from pathlib import Path

# Create custom configuration
config = DatasetConfig(
    num_nodes=250,
    n_requests=15,
    num_queries=20,
    capacity_min=6,
    capacity_max=10
)

# Create dataset with custom config
creator = DatasetCreator(config, Path('my_dataset'))
nodes, edges = creator.create_synthetic_dataset()
queries = creator.create_queries(nodes)
```

### Advanced: Load and Process Existing Dataset

```python
from experiments.dataset_creator import (
    NodeGenerator, EdgeGenerator, QueryGenerator, DatasetConfig
)
from pathlib import Path

# Load existing network
config = DatasetConfig(num_nodes=285050)
node_gen = NodeGenerator(config)
nodes = node_gen.load_from_file(Path('dataset/nodes_285050.txt'))

edge_gen = EdgeGenerator(nodes, config)
edges = edge_gen.load_from_file(Path('dataset/edges_285050.txt'))

# Generate new queries for existing network
query_gen = QueryGenerator(nodes, config)
queries = query_gen.generate_queries(num_queries=50)
query_gen.save_queries(queries, Path('queries/'))
```

### Generate Only Queries

```python
# For existing network, generate additional queries
query_gen = QueryGenerator(nodes, config)

# Generate single query
query = query_gen.generate_query(query_id=1)

# Generate multiple queries
queries = query_gen.generate_queries(num_queries=100)

# Save to files
query_gen.save_queries(queries, Path('output_queries/'))
```

---

## Node Generation Methods

### 1. Uniform Random Distribution

Generates nodes uniformly throughout the 2D space.

```python
node_gen = NodeGenerator(config)
nodes = node_gen.generate_uniform_random()
```

**When to use:**
- Testing algorithm robustness on unstructured networks
- Worst-case complexity analysis
- General-purpose benchmarking

**Characteristics:**
- Sparse connectivity
- Long average distances
- No regional clustering

### 2. Clustered Distribution (Recommended)

Generates nodes in regional clusters (realistic for urban networks).

```python
node_gen = NodeGenerator(config)
nodes = node_gen.generate_clustered(num_clusters=5)
```

**When to use:**
- Simulating realistic urban/regional road networks
- Standard dataset creation
- Most practical applications

**Characteristics:**
- Dense local connectivity
- Variable inter-cluster distances
- Realistic spatial structure

---

## Edge Generation Methods

### 1. K-Nearest Neighbors

Creates edges to k nearest neighbors (directed graph).

```python
edge_gen = EdgeGenerator(nodes, config)
edges = edge_gen.generate_k_nearest_neighbors(k=10)
```

**Advantages:**
- Consistent degree per node
- Locally-connected network
- Efficient for large networks
- Realistic road network topology

**Parameters:**
- `k`: Number of nearest neighbors (typically 10-20)

### 2. Random Edge Density

Creates edges randomly with specified density probability.

```python
config.edge_density = 0.1  # 10% of possible edges
edge_gen = EdgeGenerator(nodes, config)
edges = edge_gen.generate_random_edges()
```

**Advantages:**
- Full control over edge count
- Simple to implement
- Variable degree per node

---

## Query Generation Features

### Time Window Generation

Services have realistic time windows within working hours (9:00 AM - 7:00 PM).

**Configuration:**
```python
config.working_time_start = 540  # 9:00 AM (minutes from midnight)
config.working_time_end = 1140   # 7:00 PM
config.pickup_slack_min = 15     # Minimum pickup window
config.pickup_slack_max = 45     # Maximum pickup window
config.min_pd_separation = 10    # Minimum minutes between pickup and delivery
```

**Generated Time Windows:**
- Pickup window: [pickup_start, pickup_end]
- Delivery window: [delivery_start, delivery_end] where delivery_start > pickup_end

### Spatial Distribution

Pickup and delivery nodes are selected randomly from network nodes.

```python
# Ensures pickup and delivery nodes are different
# Maintains realistic distance constraints
```

### Demand Variation

Each service has varying demand (units to transport).

```python
config.demand_min = 1     # Minimum units
config.demand_max = 5     # Maximum units
config.capacity_min = 8   # Vehicle capacity minimum
config.capacity_max = 12  # Vehicle capacity maximum
```

---

## File Formats

### Nodes File Format
```
node_id x_coordinate y_coordinate
0 -121.904167 41.974556
1 -121.902153 41.974766
...
```

### Edges File Format
```
time_period_boundaries (space-separated)
source_node destination_node cost1,cost2,cost3,cost4
0 6 0.005952,0.005952,0.005952,0.005952
1 2 0.014350,0.014350,0.014350,0.014350
...
```

### Query File Format
```
D depot_node_id
C vehicle_capacity
S pickup_node,delivery_node [pickup_start,pickup_end] [delivery_start,delivery_end] demand
S pickup_node,delivery_node [pickup_start,pickup_end] [delivery_start,delivery_end] demand
...
```

**Example Query:**
```
D 15
C 10
S 42,87 [540,600] [650,750] 3
S 15,200 [600,700] [750,900] 2
...
```

### Metadata File Format (JSON)
```json
{
  "query_id": 1,
  "depot_node": 15,
  "capacity": 10,
  "n_requests": 20,
  "demand_range": [1, 5],
  "time_window_stats": {
    "pickup_range": [540, 1100],
    "delivery_range": [600, 1140]
  },
  "generation_method": "random_realistic",
  "seed": 43
}
```

---

## Validation

The `DatasetValidator` class ensures dataset integrity.

```python
from experiments.dataset_creator import DatasetValidator

validator = DatasetValidator()

# Validate nodes
validator.validate_nodes(nodes)

# Validate edges
validator.validate_edges(edges, nodes)

# Validate queries
for query in queries:
    validator.validate_query(query, nodes)

# Print report
validator.report()
```

**Checks Performed:**
1. **Nodes:**
   - No duplicate node IDs
   - All coordinates are finite (not NaN or Inf)

2. **Edges:**
   - Source and destination nodes exist
   - All costs are positive

3. **Queries:**
   - Depot node exists
   - All pickup/delivery nodes exist
   - Time windows are valid (start < end)
   - Pickup window precedes delivery window
   - All demands fit in vehicle capacity

---

## Performance Considerations

### Memory Usage
- 100 nodes: ~1 KB (trivial)
- 1,000 nodes: ~10 KB
- 10,000 nodes: ~100 KB
- 100,000 nodes: ~1 MB
- 285,050 nodes: ~3 MB

### Generation Time
- 100 nodes, 10 edges each: <1 second
- 1,000 nodes, 10 edges each: ~1 second
- 10,000 nodes, 10 edges each: ~5 seconds
- 100,000 nodes, 10 edges each: ~50 seconds

### Query Generation
- 20 queries, 20 requests each: <1 second
- 100 queries, 30 requests each: ~1 second
- 1,000 queries, 50 requests each: ~5 seconds

---

## Advanced Scenarios

### Subgraph Extraction

Extract subset of nodes to create smaller dataset variant:

```python
from experiments.dataset_creator import NodeGenerator, EdgeGenerator

# Load full dataset
node_gen = NodeGenerator(config)
nodes = node_gen.load_from_file('nodes_285050.txt')

# Extract 20% of nodes
subset_node_ids = sorted(random.sample(nodes.keys(), int(0.2 * len(nodes))))
subset_nodes = {nid: nodes[nid] for nid in subset_node_ids}

# Save subset
node_gen.nodes = subset_nodes
node_gen.save_to_file('nodes_57010.txt')
```

### Format Conversion

Convert between dataset formats:

```python
# Load from one format
nodes = node_gen.load_from_file('osm_nodes.txt')
edges = edge_gen.load_from_file('osm_edges.txt')

# Save in standard format
node_gen.save_to_file('nodes_converted.txt')
edge_gen.save_to_file('edges_converted.txt')
```

### Reproducibility

Control randomness with seeds:

```python
config = DatasetConfig(
    node_seed=42,      # Reproducible node placement
    edge_seed=42,      # Reproducible edge generation
    query_seed=42      # Reproducible queries
)

# Multiple runs with same config produce identical results
```

---

## Integration with OptLoad Solver

### Standard Workflow

```python
from experiments.dataset_creator import DatasetCreator, DatasetConfig
from pathlib import Path
import subprocess

# 1. Create dataset
config = DatasetConfig(num_nodes=500, num_queries=20)
creator = DatasetCreator(config, Path('experiment_dataset'))
nodes, edges = creator.create_synthetic_dataset()
queries = creator.create_queries(nodes)

# 2. Prepare solver input
nodes_file = Path('experiment_dataset/nodes.txt')
edges_file = Path('experiment_dataset/edges.txt')
queries_dir = Path('experiment_dataset/queries')

# 3. Run solver for each query
for query_file in sorted(queries_dir.glob('query_*.txt')):
    cmd = [
        'java', '-cp', 'target/classes',
        'VRPLoadingUnloadingMain',
        '--cluster',  # OptLoad algorithm
        '--nodes', str(nodes_file),
        '--edges', str(edges_file),
        '--query', str(query_file)
    ]
    subprocess.run(cmd)
```

---

## Troubleshooting

### Issue: "Node file not found"
**Solution:** Ensure nodes are generated before edges.

```python
nodes = node_gen.generate_clustered()
node_gen.save_to_file(output_path)  # Must save before creating edges
```

### Issue: "Invalid time window"
**Solution:** Verify `working_time_start < working_time_end` and allow sufficient slack.

```python
config.working_time_start = 540  # 9:00 AM
config.working_time_end = 1140   # 7:00 PM
config.pickup_slack_min = 30     # Increase if window too tight
```

### Issue: "Demand exceeds capacity"
**Solution:** Adjust capacity and demand ranges.

```python
config.capacity_min = 15  # Increase vehicle capacity
config.demand_max = 8    # Or decrease max demand
```

### Issue: Slow query generation
**Solution:** Reduce number of nodes or edges, or use K-NN instead of random edges.

```python
# Slower: Random edges with high density
config.edge_density = 0.2  # High density = slow
edge_gen.generate_random_edges()

# Faster: K-nearest neighbors
edge_gen.generate_k_nearest_neighbors(k=10)  # Fixed degree
```

---

## References

- Full implementation: [dataset_creator.py](./dataset_creator.py)
- Configuration: See `DatasetConfig` dataclass
- File formats: [DATASET.md](../DATASET.md)
- Existing datasets: [Google Drive](https://drive.google.com/drive/folders/1amiGMc5Uz92xeuGebwHm2Sj23w_mgN3m)
