# VRPLU-OptLoad Experiment Framework

## Overview

This framework provides a complete experimental pipeline for evaluating VRP-LU (Vehicle Routing Problem with Loading and Unloading) algorithms. It includes:

- **Phase C**: Query Generation
- **Phase D**: Algorithm Execution
- **Phase E**: Network Scalability Experiments
- **Phase F**: Plot Generation
- **Phase G**: Sanity Validation

## Features

- ✅ **Checkpoint/Resume**: Experiments can be interrupted and resumed from where they left off
- ✅ **Comprehensive Logging**: All operations are logged for debugging and auditing
- ✅ **Modular Design**: Each phase can be run independently
- ✅ **Configurable**: Easy to adjust parameters via command line or config file
- ✅ **Publication-Ready Plots**: Generates high-quality figures for papers

## Quick Start

### 1. Install Dependencies

```bash
cd experiments
pip install -r requirements.txt
```

### 2. Run All Experiments

```bash
python run_experiments.py
```

### 3. Check Progress

```bash
python run_experiments.py --status
```

### 4. Resume After Interruption

Just run the same command again - it will automatically resume:

```bash
python run_experiments.py
```

## Directory Structure

```
experiments/
├── __init__.py
├── config.py                    # Configuration settings
├── run_experiments.py           # Main orchestrator script
├── generate_plots.py            # Standalone plot generator
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── phase_c_query_generation.py  # Query generation
├── phase_d_algorithm_execution.py # Algorithm execution
├── phase_e_scalability.py       # Network scalability
├── phase_f_plot_generation.py   # Plot generation
├── phase_g_validation.py        # Solution validation
├── utils/
│   ├── __init__.py
│   └── logger.py                # Logging and checkpointing
├── queries/                     # Generated queries (auto-created)
├── results/                     # Experiment results (auto-created)
├── plots/                       # Generated plots (auto-created)
├── logs/                        # Log files (auto-created)
└── checkpoints/                 # Checkpoint files (auto-created)
```

## Usage Examples

### Run Specific Phases

```bash
# Generate queries only
python run_experiments.py --phase C

# Run algorithms only (requires Phase C completed)
python run_experiments.py --phase D

# Generate plots only (requires Phase D completed)
python run_experiments.py --phase F

# Run validation
python run_experiments.py --phase G
```

### Custom Parameters

```bash
# Use specific N values and runs
python run_experiments.py --n-values 10 20 40 --runs 50

# Set algorithm timeout
python run_experiments.py --timeout 300

# Custom experiment name (for multiple experiments)
python run_experiments.py --name experiment_v2
```

### Reset and Start Fresh

```bash
# Reset everything
python run_experiments.py --reset

# Reset specific phase
python run_experiments.py --reset --phase D
```

### Generate Specific Plots

```bash
# All plots
python generate_plots.py

# Specific plot types
python generate_plots.py --type distance lu_cost runtime

# Plots for specific N values
python generate_plots.py --type pareto --n 60 80

# Custom output directory and format
python generate_plots.py --output ./paper_figures --format pdf eps
```

## Configuration

Edit `config.py` to customize:

### Query Generation (Phase C)
```python
N_VALUES = [10, 20, 40, 60, 80, 100]  # Number of requests
RUNS_PER_N = 100                       # Runs per N value
WORK_START = 540                       # 9:00 AM
WORK_END = 1140                        # 7:00 PM
DEMAND_MIN = 1
DEMAND_MAX = 5
CAPACITY_MIN = 8
CAPACITY_MAX = 12
```

### Algorithm Execution (Phase D)
```python
SOLVERS = {
    "Exact": "--exact",
    "ExactLIFO": "--lifostack",
    "Insertion": "--insertion",
    "OptLoad": "--cluster",
    "FoodMatch": "--foodmatch",
    "Bazelmans": "--bazelmans",
}
TIMEOUT_SECONDS = 600  # 10 minutes per query
```

### Network Scalability (Phase E)
```python
FIXED_N = 60
SUBGRAPH_PERCENTAGES = [0.25, 0.50, 1.00]
ALGORITHMS_TO_RUN = ["OptLoad", "Insertion"]
```

## Output Files

### Results
- `results/algorithm_results.json` - All algorithm execution results
- `results/scalability/scalability_results.json` - Scalability experiment results
- `results/validation_results.json` - Solution validation results

### Queries
- `queries/N_10/query_1.txt` - Query file (VRP-LU format)
- `queries/N_10/query_1_meta.json` - Query metadata with seed
- `queries/query_index.json` - Index of all generated queries

### Plots
- `plots/distance_vs_n.png` / `.pdf`
- `plots/lu_cost_vs_n.png` / `.pdf`
- `plots/served_requests_vs_n.png` / `.pdf`
- `plots/runtime_boxplots.png` / `.pdf`
- `plots/pareto_front_n60.png` / `.pdf`
- `plots/ablation_n60.png` / `.pdf`
- `plots/scalability_comparison.png` / `.pdf`

### Logs
- `logs/vrplu_experiment_20260121_143022.log` - Timestamped log file

### Checkpoints
- `checkpoints/vrplu_experiment_checkpoint.json` - Progress checkpoint

## Experiment Design

### Phase C: Query Generation

For each N in {10, 20, 40, 60, 80, 100}:
- Generate 100 queries
- Each query has:
  - Random depot node
  - Random capacity (8-12)
  - N service requests with:
    - Random pickup/delivery nodes
    - Valid time windows (pickup before delivery)
    - Random demands (1-5)
  - Deterministic seed for reproducibility

### Phase D: Algorithm Execution

For each query:
- Run each algorithm (Exact, LIFO, Insertion, OptLoad, etc.)
- Log metrics: LU cost, distance, served requests, runtime
- Save to results file

### Phase E: Network Scalability

- Fix N = 60 requests
- Extract 25%, 50%, 100% of network nodes
- Generate queries within each subgraph
- Compare OptLoad vs Insertion baseline

### Phase F: Plot Generation

Generate publication-quality plots:
- Distance vs N with error bars
- LU Cost vs N with error bars
- Service Rate vs N
- Runtime boxplots by algorithm
- Pareto fronts (Distance vs LU Cost)
- Ablation study bar charts
- Scalability comparison

### Phase G: Sanity Validation

For every solution:
- ✓ Pickup precedes delivery
- ✓ Capacity never exceeded
- ✓ Time windows satisfied
- ✓ LU cost verified via stack simulation

## Troubleshooting

### "Phase X requires Phase Y to be completed first"
Run the prerequisite phase first, or run all phases in order.

### "No results to plot"
Make sure Phase D has completed successfully.

### "Compilation failed"
Ensure Java and Maven are properly installed and the project compiles:
```bash
cd /path/to/VRPLU-OptLoad
mvn compile
```

### "matplotlib not available"
Install the plotting dependencies:
```bash
pip install matplotlib seaborn
```

### Experiment seems stuck
Check the log file for the current operation. Large N values with exact solver may take significant time.

### Reset and start fresh
```bash
python run_experiments.py --reset
```

## Extending the Framework

### Adding New Algorithms

1. Add the solver flag to `config.py`:
```python
SOLVERS["NewAlgorithm"] = "--newalgo"
```

2. Implement the solver in Java (following the Solver interface)

3. Re-run Phase D:
```bash
python run_experiments.py --reset --phase D
python run_experiments.py --phase D
```

### Adding New Plots

1. Add a new method to `PlotGenerator` in `phase_f_plot_generation.py`
2. Call it from `generate_all_plots()`
3. Run Phase F to generate the new plot

## License

See main project LICENSE file.
