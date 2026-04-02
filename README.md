# VRPLU-OptLoad

Java solver for Vehicle Routing with Loading and Unloading constraints (VRP-LU), with one unified runner script.

## Requirements

- Java 11+
- Bash shell
- Python 3.x only if you use experiment scripts outside the main runner

## Dataset and query naming

For dataset size N, files must match this naming:

- dataset/nodes_N.txt
- dataset/edges_N.txt
- Query_N.txt

The runner validates this match before execution.

## Unified runner

Use run.sh for all workflows.

```bash
./run.sh [options]
```

### Main options

- --mode: single | ablation | tw-sensitivity | capacity-sensitivity | all-sensitivity
- --solver: cluster | nocluster | nolupruning | exact | foodmatch | lifostack | insertion | bazelmans
- --dataset N: choose dataset suffix N
- --query FILE: override query input file (copied internally as Query_N.txt)
- --threads N: set ForkJoin parallelism for Java execution
- --build compile|none: compile sources before running or skip build
- --skip-download: skip dataset downloader script
- --tw-factors CSV: factors for TW sensitivity mode
- --capacity-factors CSV: factors for capacity sensitivity mode

## Examples

Single run with exact solver on dataset 6105:

```bash
./run.sh --mode single --solver exact --dataset 6105
```

Single run with custom query file:

```bash
./run.sh --mode single --solver cluster --dataset 21048 --query ./my_queries.txt
```

Ablation study (cluster, nocluster, nolupruning):

```bash
./run.sh --mode ablation --dataset 285050
```

Time-window sensitivity analysis:

```bash
./run.sh --mode tw-sensitivity --solver cluster --dataset 21048 --tw-factors 0.8,1.0,1.2
```

Capacity sensitivity analysis:

```bash
./run.sh --mode capacity-sensitivity --solver insertion --dataset 6105 --capacity-factors 0.7,1.0,1.3
```

Run both TW and capacity sensitivity in one command:

```bash
./run.sh --mode all-sensitivity --solver cluster --dataset 21048 --tw-factors 0.8,1.0,1.2 --capacity-factors 0.8,1.0,1.2
```

## Output files

Outputs are written to repository root.

- Single run: standard solver prefixes (for example OutputExact_N.txt)
- Ablation mode: suffix ABL_variant is added
- TW sensitivity mode: suffix TW_factor is added
- Capacity sensitivity mode: suffix CAP_factor is added

## Query format

```text
D <depot_node_id>
C <vehicle_capacity>
S <pickup_node>,<dropoff_node> <pickup_start>,<pickup_end> <dropoff_start>,<dropoff_end> <amount>
```

Times are minutes from midnight.
