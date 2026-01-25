# VRP-LU Experiment Final Report

**Generated:** 2026-01-22 20:29:55

## Executive Summary

- **Total Experiments:** 3000
- **Algorithms Tested:** 5
- **N Values:** 10, 20, 40, 60, 80, 100
- **Runs per Configuration:** 100

## Results Overview

### Bazelmans

- Total runs: 600
- Success rate: 94.8%
- Total requests served: 6674

| N | Runs | Success | Avg Served | Avg LU Cost | Avg Runtime |
|---|------|---------|------------|-------------|-------------|
| 10 | 100 | 99 | 11.6 | 53.8 | 14089ms |
| 20 | 100 | 99 | 11.7 | 59.6 | 35177ms |
| 40 | 100 | 96 | 11.6 | 60.2 | 53588ms |
| 60 | 100 | 96 | 10.9 | 57.3 | 80754ms |
| 80 | 100 | 90 | 10.7 | 54.2 | 99478ms |
| 100 | 100 | 89 | 10.4 | 52.3 | 108489ms |

### ExactLIFO

- Total runs: 600
- Success rate: 98.8%
- Total requests served: 4675

| N | Runs | Success | Avg Served | Avg LU Cost | Avg Runtime |
|---|------|---------|------------|-------------|-------------|
| 10 | 100 | 96 | 7.6 | 40.7 | 565ms |
| 20 | 100 | 100 | 7.6 | 58.7 | 1458ms |
| 40 | 100 | 100 | 7.8 | 66.8 | 2008ms |
| 60 | 100 | 100 | 8.5 | 69.8 | 2611ms |
| 80 | 100 | 98 | 7.1 | 52.9 | 3008ms |
| 100 | 100 | 99 | 8.2 | 71.7 | 3885ms |

### FoodMatch

- Total runs: 600
- Success rate: 99.2%
- Total requests served: 4694

| N | Runs | Success | Avg Served | Avg LU Cost | Avg Runtime |
|---|------|---------|------------|-------------|-------------|
| 10 | 100 | 98 | 7.3 | 40.1 | 537ms |
| 20 | 100 | 100 | 8.3 | 55.0 | 1243ms |
| 40 | 100 | 99 | 7.2 | 55.4 | 1711ms |
| 60 | 100 | 100 | 8.9 | 64.3 | 2662ms |
| 80 | 100 | 99 | 6.9 | 49.8 | 2996ms |
| 100 | 100 | 99 | 8.3 | 61.8 | 3619ms |

### Insertion

- Total runs: 600
- Success rate: 99.5%
- Total requests served: 9604

| N | Runs | Success | Avg Served | Avg LU Cost | Avg Runtime |
|---|------|---------|------------|-------------|-------------|
| 10 | 100 | 100 | 14.0 | 69.5 | 5924ms |
| 20 | 100 | 98 | 14.6 | 82.1 | 18448ms |
| 40 | 100 | 99 | 16.5 | 99.6 | 28794ms |
| 60 | 100 | 100 | 16.2 | 102.7 | 40672ms |
| 80 | 100 | 100 | 17.1 | 109.2 | 48480ms |
| 100 | 100 | 100 | 17.7 | 115.9 | 65571ms |

### OptLoad

- Total runs: 600
- Success rate: 0.2%
- Total requests served: 17

| N | Runs | Success | Avg Served | Avg LU Cost | Avg Runtime |
|---|------|---------|------------|-------------|-------------|
| 10 | 100 | 0 | 0.0 | 0.0 | 1150ms |
| 20 | 100 | 0 | 0.0 | 0.0 | 763ms |
| 40 | 100 | 0 | 0.0 | 0.0 | 607ms |
| 60 | 100 | 0 | 0.0 | 0.0 | 796ms |
| 80 | 100 | 0 | 0.0 | 0.0 | 989ms |
| 100 | 100 | 1 | 0.2 | 0.4 | 50675ms |

## Charts

The following charts are available in the `results/charts/` directory:

1. **scalability_served.png** - Requests served vs N
2. **lu_cost.png** - L-U cost vs N
3. **runtime.png** - Runtime vs N
4. **comparison_bar.png** - Algorithm comparison at N=60

## Methodology

### Query Generation
- Tour-based queries with realistic time windows
- A* pathfinding for accurate travel time estimation
- Working hours: 9 AM - 7 PM (540-1140 minutes)

### Execution
- Each query run with 300s timeout
- Results parsed from solver output files
- Checkpoint-based resumability

