# Dataset Creation - Quick Reference

## Installation

```bash
# No additional dependencies required
# Uses Python stdlib: random, math, json, pathlib, dataclasses, typing
```

## Basic Usage

### Create Dataset in 3 Lines

```python
from experiments.dataset_creator import create_standard_dataset
output_dir = create_standard_dataset('small')  # 100 nodes, 5 queries, 10 requests
```

### Custom Dataset

```python
from experiments.dataset_creator import DatasetConfig, DatasetCreator
from pathlib import Path

config = DatasetConfig(num_nodes=500, num_queries=20, n_requests=30)
creator = DatasetCreator(config, Path('my_dataset'))
creator.create_complete_dataset()
```

## Common Tasks

### Generate Queries Only

```python
from experiments.dataset_creator import QueryGenerator, NodeGenerator, DatasetConfig
from pathlib import Path

# Load existing network
config = DatasetConfig(num_nodes=285050)
node_gen = NodeGenerator(config)
nodes = node_gen.load_from_file(Path('dataset/nodes_285050.txt'))

# Generate queries
query_gen = QueryGenerator(nodes, config)
queries = query_gen.generate_queries(num_queries=100)
query_gen.save_queries(queries, Path('queries/'))
```

### Load Existing Network

```python
node_gen.load_from_file(Path('nodes.txt'))
edge_gen.load_from_file(Path('edges.txt'))
```

### Generate Nodes Only

```python
# Uniform random
nodes = node_gen.generate_uniform_random()

# Clustered (recommended)
nodes = node_gen.generate_clustered(num_clusters=5)

# Save
node_gen.save_to_file(Path('nodes.txt'))
```

### Generate Edges

```python
# K-nearest neighbors (recommended)
edges = edge_gen.generate_k_nearest_neighbors(k=10)

# Random edges
config.edge_density = 0.1  # 10% of possible edges
edges = edge_gen.generate_random_edges()

# Save
edge_gen.save_to_file(Path('edges.txt'))
```

### Validate Dataset

```python
from experiments.dataset_creator import DatasetValidator

validator = DatasetValidator()
validator.validate_nodes(nodes)
validator.validate_edges(edges, nodes)
for query in queries:
    validator.validate_query(query, nodes)
validator.report()
```

## Configuration Presets

| Size | Nodes | Queries | Requests | Use Case |
|------|-------|---------|----------|----------|
| **small** | 100 | 5 | 10 | Testing |
| **medium** | 500 | 10 | 20 | Development |
| **large** | 1000 | 20 | 30 | Benchmarking |

## Key Parameters

| Parameter | Range | Default | Notes |
|-----------|-------|---------|-------|
| `num_nodes` | 10-1M | 100 | Network size |
| `num_queries` | 1-1000 | 10 | Problem instances |
| `n_requests` | 1-100 | 20 | Services per query |
| `capacity_min` | 1-20 | 8 | Vehicle capacity |
| `demand_min` | 1-10 | 1 | Service demand |
| `edge_density` | 0.01-1.0 | 0.1 | For random edges |
| `time_periods` | 1-4 | 4 | Time-dependent costs |

## File Formats

### Nodes File
```
node_id x_coordinate y_coordinate
0 -121.904167 41.974556
1 -121.902153 41.974766
```

### Edges File
```
time_period_boundaries
source_node dest_node cost1,cost2,cost3,cost4
0 6 0.005952,0.005952,0.005952,0.005952
1 2 0.014350,0.014350,0.014350,0.014350
```

### Query File
```
D depot_node_id
C vehicle_capacity
S pickup,delivery [pickup_start,pickup_end] [delivery_start,delivery_end] demand
```

## Run Examples

```bash
# All examples
python experiments/examples_dataset_creation.py

# Specific example
python experiments/examples_dataset_creation.py 1  # Minimal dataset
python experiments/examples_dataset_creation.py 2  # Medium dataset
python experiments/examples_dataset_creation.py 5  # Scalability study
```

## Run Tests

```bash
python -m pytest experiments/tests_dataset_creation.py -v
```

## Solver Integration

```bash
# After creating dataset
java -cp target/classes VRPLoadingUnloadingMain \
  --cluster \
  --nodes dataset/nodes.txt \
  --edges dataset/edges.txt \
  --query dataset/queries/query_1.txt
```

## Performance

| Operation | Dataset Size | Time |
|-----------|--------------|------|
| Generate 100 nodes | - | <0.1s |
| Generate 500 nodes | - | 0.5s |
| Generate 1000 nodes | - | 2s |
| Generate 10k edges (k=10) | 100 nodes | <0.1s |
| Generate 100 queries | 500 nodes | 1s |
| Validate 1000 queries | 100 nodes | 0.1s |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Node not found" | Ensure nodes generated before edges |
| "Time window invalid" | Increase working_time_end, pickup_slack_max |
| "Demand exceeds capacity" | Increase capacity_max or decrease demand_max |
| "Slow generation" | Use k-NN instead of random edges, reduce node count |

## Documentation

- Full guide: [DATASET_CREATION_GUIDE.md](DATASET_CREATION_GUIDE.md)
- Examples: [examples_dataset_creation.py](examples_dataset_creation.py)
- Tests: [tests_dataset_creation.py](tests_dataset_creation.py)
- Implementation: [dataset_creator.py](dataset_creator.py)
