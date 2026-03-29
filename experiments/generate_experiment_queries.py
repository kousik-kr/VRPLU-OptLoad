#!/usr/bin/env python3
"""
Generate all queries needed for the complete experimental plan.

Experiments:
  Step 1: Core comparison (Oldenburg, N=2,5,10)
  Step 2: Scalability with requests (London, N=10,20,40,60,80) — reuse existing
  Step 3: Network scalability (Oldenburg, California, London, N=20)
    Step 4: Ablation study (London, N=2,5)
  Step 5: Search space reduction (London, N=10,18,26,34,42,50,58,66,74)
  Step 6: Parallel performance (London, N=60) — reuse existing
  Step 7A: Capacity sensitivity (London, N=20, C=6,8,10,12)
  Step 7B: Time window sensitivity (London, N=20, TW=30,60,90,120)
"""

import os
import sys
import random
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DATASET_DIR = PROJECT_ROOT / "dataset"
QUERIES_DIR = PROJECT_ROOT / "experiments" / "queries"

# Network configurations
NETWORKS = {
    "oldenburg": {"nodes_file": "nodes_6105.txt", "node_count": 6105},
    "california": {"nodes_file": "nodes_21048.txt", "node_count": 21048},
    "london": {"nodes_file": "nodes_285050.txt", "node_count": 285050},
}

# Working hours (minutes from midnight)
WORK_START = 540   # 9:00 AM
WORK_END = 1140    # 7:00 PM

# Defaults
DEFAULT_CAPACITY_MIN = 8
DEFAULT_CAPACITY_MAX = 12
DEFAULT_DEMAND_MIN = 1
DEFAULT_DEMAND_MAX = 5
DEFAULT_TW_MIN = 30
DEFAULT_TW_MAX = 120
SEED_BASE = 42
RUNS = 10


@dataclass
class ServiceRequest:
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


def load_valid_nodes(network: str) -> List[int]:
    """Load valid node IDs from the dataset."""
    node_file = DATASET_DIR / NETWORKS[network]["nodes_file"]
    if node_file.exists():
        with open(node_file, 'r') as f:
            count = sum(1 for _ in f)
        return list(range(count))
    else:
        return list(range(NETWORKS[network]["node_count"]))


def generate_time_window(min_start: int, max_end: int,
                         duration_min: int = 15, duration_max: int = 120) -> Optional[Tuple[int, int]]:
    """Generate a valid time window."""
    if max_end - min_start < duration_min:
        return None
    max_possible_duration = min(duration_max, max_end - min_start)
    if max_possible_duration < duration_min:
        return None
    duration = random.randint(duration_min, max_possible_duration)
    latest_start = max_end - duration
    start = random.randint(min_start, latest_start)
    end = start + duration
    return (start, end)


def generate_service_request(valid_nodes: List[int],
                             existing_pickups: List[Tuple[int, int]],
                             existing_deliveries: List[Tuple[int, int]],
                             tw_duration_min: int = 15,
                             tw_duration_max: int = 120,
                             demand_min: int = 1,
                             demand_max: int = 5,
                             relax_overlaps: bool = False) -> Optional[ServiceRequest]:
    """Generate a single service request."""
    max_attempts = 5000

    for _ in range(max_attempts):
        # Generate pickup time window
        pickup_tw = generate_time_window(
            WORK_START, WORK_END - tw_duration_min - 5,
            duration_min=tw_duration_min, duration_max=tw_duration_max
        )
        if pickup_tw is None:
            continue
        pickup_start, pickup_end = pickup_tw

        # Overlap constraints (relaxed or normal)
        if not relax_overlaps:
            max_overlaps = max(3, len(existing_pickups) // 10 + 2)
            overlaps = sum(
                1 for (s, e) in existing_pickups
                if not (pickup_end <= s or pickup_start >= e)
            )
            if overlaps > max_overlaps:
                continue

        # Delivery time window must start after pickup ends
        delivery_tw = generate_time_window(
            pickup_end + 1, WORK_END,
            duration_min=max(10, min(tw_duration_min, WORK_END - pickup_end - 2)),
            duration_max=max(10, min(tw_duration_max, WORK_END - pickup_end - 1))
        )
        if delivery_tw is None:
            continue
        delivery_start, delivery_end = delivery_tw

        # Check delivery overlap constraints
        if not relax_overlaps:
            max_delivery_overlaps = max(5, len(existing_deliveries) // 8 + 3)
            overlaps = sum(
                1 for (s, e) in existing_deliveries
                if not (delivery_end <= s or delivery_start >= e)
            )
            if overlaps > max_delivery_overlaps:
                continue

        pickup_node = random.choice(valid_nodes)
        delivery_node = random.choice(valid_nodes)
        while delivery_node == pickup_node:
            delivery_node = random.choice(valid_nodes)
        demand = random.randint(demand_min, demand_max)

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


def generate_query(valid_nodes: List[int], n_requests: int, seed: int,
                   capacity: int = None,
                   tw_duration_min: int = 15,
                   tw_duration_max: int = 120,
                   demand_min: int = 1,
                   demand_max: int = 5,
                   relax_overlaps: bool = False) -> Optional[str]:
    """Generate a single query string."""
    random.seed(seed)

    depot_node = random.choice(valid_nodes)
    if capacity is None:
        capacity = random.randint(DEFAULT_CAPACITY_MIN, DEFAULT_CAPACITY_MAX)

    services = []
    pickup_windows = []
    delivery_windows = []

    for _ in range(n_requests):
        service = generate_service_request(
            valid_nodes, pickup_windows, delivery_windows,
            tw_duration_min=tw_duration_min,
            tw_duration_max=tw_duration_max,
            demand_min=demand_min,
            demand_max=demand_max,
            relax_overlaps=relax_overlaps
        )
        if service is None:
            print(f"  Warning: Failed to generate request {len(services)+1}/{n_requests} (seed={seed})")
            return None

        services.append(service)
        pickup_windows.append((service.pickup_start, service.pickup_end))
        delivery_windows.append((service.delivery_start, service.delivery_end))

    lines = [f"D {depot_node}", f"C {capacity}"]
    for s in services:
        lines.append(s.to_string())
    return "\n".join(lines)


def generate_queries_for_config(network: str, n_requests: int, runs: int,
                                output_dir: Path, prefix: str = "query",
                                capacity: int = None,
                                tw_duration_min: int = 15,
                                tw_duration_max: int = 120,
                                seed_offset: int = 0,
                                relax_overlaps: bool = False):
    """Generate multiple queries for a given configuration."""
    output_dir.mkdir(parents=True, exist_ok=True)
    valid_nodes = load_valid_nodes(network)
    generated = 0

    for run in range(1, runs + 1):
        seed = SEED_BASE * 10000 + NETWORKS[network]["node_count"] * 100 + n_requests * 10 + run + seed_offset
        query_str = generate_query(
            valid_nodes, n_requests, seed,
            capacity=capacity,
            tw_duration_min=tw_duration_min,
            tw_duration_max=tw_duration_max,
            relax_overlaps=relax_overlaps
        )
        if query_str is None:
            print(f"  FAILED: {network} N={n_requests} run={run}")
            continue

        query_file = output_dir / f"{prefix}_{run}.txt"
        with open(query_file, 'w') as f:
            f.write(query_str)
        generated += 1

    print(f"  Generated {generated}/{runs} queries -> {output_dir}")
    return generated


def check_existing_london_queries():
    """Check if existing London queries can be reused."""
    existing = {}
    for n_dir in QUERIES_DIR.glob("N_*"):
        n = int(n_dir.name.split("_")[1])
        count = len(list(n_dir.glob("query_*.txt")))
        if count > 0:
            existing[n] = count
    return existing


def main():
    print("=" * 60)
    print("EXPERIMENT QUERY GENERATION")
    print("=" * 60)

    # Check existing London queries
    existing = check_existing_london_queries()
    print(f"\nExisting London queries: {existing}")

    # =========================================================
    # STEP 1: Core comparison (Oldenburg, N=2,5,10)
    # =========================================================
    print("\n--- STEP 1: Core Comparison (Oldenburg) ---")
    for n in [2, 5, 10]:
        out_dir = QUERIES_DIR / "step1_core" / f"oldenburg_N{n}"
        generate_queries_for_config("oldenburg", n, RUNS, out_dir)

    # =========================================================
    # STEP 2: Scalability with requests (London, N=10,20,40,60,80)
    # Reuse existing queries - just symlink or verify
    # =========================================================
    print("\n--- STEP 2: Scalability with Requests (London) ---")
    for n in [10, 20, 40, 60, 80]:
        existing_dir = QUERIES_DIR / f"N_{n}"
        if existing_dir.exists() and n in existing:
            print(f"  Reusing {existing[n]} existing queries for N={n}")
        else:
            out_dir = QUERIES_DIR / "step2_scalability" / f"london_N{n}"
            generate_queries_for_config("london", n, RUNS, out_dir)

    # =========================================================
    # STEP 3: Network scalability (All 3 networks, N=20)
    # London N=20 can be reused
    # =========================================================
    print("\n--- STEP 3: Network Scalability (N=20) ---")
    for network in ["oldenburg", "california"]:
        out_dir = QUERIES_DIR / "step3_network" / f"{network}_N20"
        generate_queries_for_config(network, 20, RUNS, out_dir)
    print(f"  London N=20: reusing existing ({existing.get(20, 0)} queries)")

    # =========================================================
    # STEP 4: Ablation study (London, N=2,5)
    # =========================================================
    print("\n--- STEP 4: Ablation Study (London) ---")
    for n in [2, 5]:
        if n in existing:
            print(f"  Reusing existing queries for N={n}")
        else:
            out_dir = QUERIES_DIR / "step4_ablation" / f"london_N{n}"
            generate_queries_for_config("london", n, RUNS, out_dir)

    # =========================================================
    # STEP 5: Search Space Reduction (London, N=10..80 step 8)
    # Some N values overlap with existing, generate missing ones
    # =========================================================
    print("\n--- STEP 5: Search Space Reduction (London) ---")
    for n in range(10, 81, 8):  # 10,18,26,34,42,50,58,66,74
        if n in existing:
            print(f"  Reusing existing queries for N={n}")
        else:
            out_dir = QUERIES_DIR / "step5_searchspace" / f"london_N{n}"
            generate_queries_for_config("london", n, RUNS, out_dir)

    # =========================================================
    # STEP 6: Parallel performance (London, N=60)
    # Reuse existing
    # =========================================================
    print("\n--- STEP 6: Parallel Performance (London, N=60) ---")
    if 60 in existing:
        print(f"  Reusing existing queries for N=60")
    else:
        out_dir = QUERIES_DIR / "step6_parallel" / "london_N60"
        generate_queries_for_config("london", 60, RUNS, out_dir)

    # =========================================================
    # STEP 7A: Capacity sensitivity (London, N=20, C=6,8,10,12)
    # Need separate queries with fixed capacity
    # =========================================================
    print("\n--- STEP 7A: Capacity Sensitivity (London, N=20) ---")
    for cap in [6, 8, 10, 12]:
        out_dir = QUERIES_DIR / "step7_sensitivity" / f"capacity_C{cap}"
        generate_queries_for_config(
            "london", 20, RUNS, out_dir,
            capacity=cap,
            seed_offset=cap * 1000  # Different seeds for different capacities
        )

    # =========================================================
    # STEP 7B: Time window sensitivity (London, N=20, TW=30,60,90,120)
    # Fixed time window duration (both min and max the same)
    # =========================================================
    print("\n--- STEP 7B: Time Window Sensitivity (London, N=20) ---")
    for tw in [30, 60, 90, 120]:
        out_dir = QUERIES_DIR / "step7_sensitivity" / f"timewindow_TW{tw}"
        # For large TW durations, allow a range around the target and relax overlaps
        tw_min = max(15, tw - 10)
        tw_max = tw + 10
        generate_queries_for_config(
            "london", 20, RUNS, out_dir,
            tw_duration_min=tw_min,
            tw_duration_max=tw_max,
            seed_offset=tw * 1000,
            relax_overlaps=(tw >= 60)  # Relax overlaps for larger TW
        )

    # =========================================================
    # Summary
    # =========================================================
    print("\n" + "=" * 60)
    print("QUERY GENERATION COMPLETE")
    print("=" * 60)

    # Count all generated queries
    total = 0
    for root, dirs, files in os.walk(QUERIES_DIR):
        total += len([f for f in files if f.endswith('.txt') and 'query' in f.lower()])
    print(f"Total query files: {total}")


if __name__ == "__main__":
    main()
