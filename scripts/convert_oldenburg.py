#!/usr/bin/env python3
"""
Convert Oldenburg dataset to OptLoad format with synthetic time-dependent travel times.

Input format:
- edges: edge_id source destination distance
- nodes: node_id latitude longitude

Output format (same as London):
- First line: time series (0 450 480 510 540 570 960 990 1020 1050 1080 1110)
- edges: source destination time_varying_distances direction_flag
- nodes: node_id x y
"""

import os
import random
from pathlib import Path

# Configuration
BASE_DIR = Path("/home/gunturi/VRPLU-OptLoad")
INPUT_DIR = BASE_DIR / "dataset" / "Oldenberg"
OUTPUT_DIR = BASE_DIR / "dataset"

# Time series (same as London)
TIME_SERIES = [0, 450, 480, 510, 540, 570, 960, 990, 1020, 1050, 1080, 1110]

# Time-dependent variation factors (peak hours have higher travel times)
# Indices: 0=midnight, 450=7:30am, 480=8am, 510=8:30am, 540=9am, 570=9:30am
#          960=4pm, 990=4:30pm, 1020=5pm, 1050=5:30pm, 1080=6pm, 1110=6:30pm
VARIATION_FACTORS = [
    1.0,   # 0 - midnight (baseline)
    1.12,  # 450 - 7:30am (morning rush starting)
    1.22,  # 480 - 8am (morning rush)
    1.32,  # 510 - 8:30am (peak morning rush)
    1.25,  # 540 - 9am (morning rush ending)
    1.10,  # 570 - 9:30am (post rush)
    1.10,  # 960 - 4pm (pre-evening rush)
    1.18,  # 990 - 4:30pm (evening rush starting)
    1.28,  # 1020 - 5pm (evening rush)
    1.35,  # 1050 - 5:30pm (peak evening rush)
    1.22,  # 1080 - 6pm (evening rush ending)
    1.08,  # 1110 - 6:30pm (post rush)
]

# Scale factor to convert raw distances to travel time (minutes)
# Oldenburg distances are in coordinate units (~100m each), assume 30km/h average speed
# 100m / 30km/h = 0.003333 hours = 0.2 minutes per unit
# Scale down by 100 to get sub-minute travel times like London
DISTANCE_SCALE = 0.01  # Convert to reasonable travel times


def add_noise(factor, noise_level=0.05):
    """Add small random noise to variation factor."""
    return factor * (1 + random.uniform(-noise_level, noise_level))


def convert_oldenburg():
    """Convert Oldenburg dataset to OptLoad format."""
    print("=" * 60)
    print("CONVERTING OLDENBURG DATASET TO OPTLOAD FORMAT")
    print("=" * 60)
    
    # Read input files
    edges_file = INPUT_DIR / "edges_6105.txt"
    nodes_file = INPUT_DIR / "nodes_6105.txt"
    
    # Find actual max node ID
    max_node_id = 0
    with open(nodes_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                node_id = int(parts[0])
                max_node_id = max(max_node_id, node_id)
    
    node_count = max_node_id + 1  # Node IDs are 0-indexed
    
    print(f"Input nodes file: {nodes_file}")
    print(f"Input edges file: {edges_file}")
    print(f"Max node ID: {max_node_id}")
    print(f"Node count (for solver): {node_count}")
    
    # Output files
    output_edges = OUTPUT_DIR / f"edges_{node_count}.txt"
    output_nodes = OUTPUT_DIR / f"nodes_{node_count}.txt"
    
    # Convert nodes (format: node_id x y)
    print(f"\nConverting nodes to: {output_nodes}")
    with open(nodes_file, 'r') as fin, open(output_nodes, 'w') as fout:
        for line in fin:
            parts = line.strip().split()
            if len(parts) >= 3:
                node_id = parts[0]
                lat = parts[1]  # Using as x coordinate
                lon = parts[2]  # Using as y coordinate
                fout.write(f"{node_id} {lat} {lon}\n")
    
    # Convert edges with time-dependent travel times
    print(f"Converting edges to: {output_edges}")
    
    # First line: time series
    with open(output_edges, 'w') as fout:
        fout.write(" ".join(str(t) for t in TIME_SERIES) + " \n")
        
        edge_count = 0
        with open(edges_file, 'r') as fin:
            for line in fin:
                parts = line.strip().split()
                if len(parts) >= 4:
                    edge_id = parts[0]
                    source = parts[1]
                    dest = parts[2]
                    base_distance = float(parts[3]) * DISTANCE_SCALE
                    
                    # Generate time-varying distances
                    time_distances = []
                    for factor in VARIATION_FACTORS:
                        varied_distance = base_distance * add_noise(factor)
                        time_distances.append(f"{varied_distance:.6f}")
                    
                    # Format: source destination comma_separated_distances direction_flag
                    distances_str = ",".join(time_distances)
                    fout.write(f"{source} {dest} {distances_str} 0\n")
                    
                    # Add reverse edge (bidirectional)
                    time_distances_rev = []
                    for factor in VARIATION_FACTORS:
                        varied_distance = base_distance * add_noise(factor)
                        time_distances_rev.append(f"{varied_distance:.6f}")
                    distances_str_rev = ",".join(time_distances_rev)
                    fout.write(f"{dest} {source} {distances_str_rev} 0\n")
                    
                    edge_count += 1
    
    print(f"Converted {edge_count} edges (x2 for bidirectional)")
    print(f"\nOutput files created:")
    print(f"  - {output_nodes}")
    print(f"  - {output_edges}")
    
    return node_count


if __name__ == "__main__":
    random.seed(42)  # For reproducibility
    convert_oldenburg()
    print("\n✓ Oldenburg dataset conversion complete!")
