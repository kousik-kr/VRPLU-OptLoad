#!/usr/bin/env python3
"""
Convert California dataset to OptLoad format with synthetic time-dependent travel times.

Input format:
- edges: edge_id source destination distance (distance needs x1000)
- nodes: node_id longitude latitude

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
INPUT_DIR = BASE_DIR / "dataset" / "California"
OUTPUT_DIR = BASE_DIR / "dataset"

# Time series (same as London)
TIME_SERIES = [0, 450, 480, 510, 540, 570, 960, 990, 1020, 1050, 1080, 1110]

# Time-dependent variation factors
VARIATION_FACTORS = [
    1.0,   # 0 - midnight (baseline)
    1.12,  # 450 - 7:30am
    1.22,  # 480 - 8am
    1.32,  # 510 - 8:30am
    1.25,  # 540 - 9am
    1.10,  # 570 - 9:30am
    1.10,  # 960 - 4pm
    1.18,  # 990 - 4:30pm
    1.28,  # 1020 - 5pm
    1.35,  # 1050 - 5:30pm
    1.22,  # 1080 - 6pm
    1.08,  # 1110 - 6:30pm
]

# Distance multiplier for California
# Original distances are very small (0.001-0.01 coordinate units = lat/lon degrees)
# Multiply to get reasonable travel times in minutes
# 1 degree ~ 111km, so 0.001 degrees ~ 111m
# At 30km/h, 111m takes 0.22 minutes
# Original multiplier of 1000 was too high (giving 2-8 min per edge)
# Use 500 to get ~1-4 minute edges
DISTANCE_MULTIPLIER = 500


def add_noise(factor, noise_level=0.05):
    """Add small random noise to variation factor."""
    return factor * (1 + random.uniform(-noise_level, noise_level))


def convert_california():
    """Convert California dataset to OptLoad format."""
    print("=" * 60)
    print("CONVERTING CALIFORNIA DATASET TO OPTLOAD FORMAT")
    print("=" * 60)
    
    # Read input files
    edges_file = INPUT_DIR / "edge distance.txt"
    nodes_file = INPUT_DIR / "node coordinates.txt"
    
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
    print(f"Distance multiplier: {DISTANCE_MULTIPLIER}")
    
    # Output files
    output_edges = OUTPUT_DIR / f"edges_{node_count}.txt"
    output_nodes = OUTPUT_DIR / f"nodes_{node_count}.txt"
    
    # Convert nodes
    # Input: node_id longitude latitude
    # Output: node_id x y (use projected coordinates)
    print(f"\nConverting nodes to: {output_nodes}")
    
    # First pass: find bounds for simple projection
    min_lon, max_lon = float('inf'), float('-inf')
    min_lat, max_lat = float('inf'), float('-inf')
    
    with open(nodes_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3:
                lon = float(parts[1])
                lat = float(parts[2])
                min_lon = min(min_lon, lon)
                max_lon = max(max_lon, lon)
                min_lat = min(min_lat, lat)
                max_lat = max(max_lat, lat)
    
    print(f"  Longitude range: [{min_lon:.4f}, {max_lon:.4f}]")
    print(f"  Latitude range: [{min_lat:.4f}, {max_lat:.4f}]")
    
    # Convert to pseudo-metric coordinates (scaled to reasonable range)
    # Use simple equirectangular projection
    import math
    lat_center = (min_lat + max_lat) / 2
    lon_scale = math.cos(math.radians(lat_center)) * 111320  # meters per degree longitude
    lat_scale = 111320  # meters per degree latitude
    
    with open(nodes_file, 'r') as fin, open(output_nodes, 'w') as fout:
        for line in fin:
            parts = line.strip().split()
            if len(parts) >= 3:
                node_id = parts[0]
                lon = float(parts[1])
                lat = float(parts[2])
                
                # Project to pseudo-metric (meters from origin)
                x = (lon - min_lon) * lon_scale
                y = (lat - min_lat) * lat_scale
                
                fout.write(f"{node_id} {x:.6f} {y:.6f}\n")
    
    # Convert edges with time-dependent travel times
    print(f"Converting edges to: {output_edges}")
    
    with open(output_edges, 'w') as fout:
        # First line: time series
        fout.write(" ".join(str(t) for t in TIME_SERIES) + " \n")
        
        edge_count = 0
        with open(edges_file, 'r') as fin:
            for line in fin:
                parts = line.strip().split()
                if len(parts) >= 4:
                    edge_id = parts[0]
                    source = parts[1]
                    dest = parts[2]
                    base_distance = float(parts[3]) * DISTANCE_MULTIPLIER  # Apply multiplier
                    
                    # Generate time-varying distances
                    time_distances = []
                    for factor in VARIATION_FACTORS:
                        varied_distance = base_distance * add_noise(factor)
                        time_distances.append(f"{varied_distance:.6f}")
                    
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
    convert_california()
    print("\n✓ California dataset conversion complete!")
