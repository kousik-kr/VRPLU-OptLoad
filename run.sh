#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

MODE="single"
BUILD_MODE="compile"
SOLVER="cluster"
DATASET="285050"
QUERY_FILE=""
THREADS=""
TW_FACTORS="0.8,1.0,1.2"
CAPACITY_FACTORS="0.8,1.0,1.2"
SKIP_DOWNLOAD=false

print_help() {
    cat <<'EOF'
Unified runner for VRPLU-OptLoad.

Usage:
  ./run.sh [options]

Core options:
    --mode MODE                 single | ablation | tw-sensitivity | capacity-sensitivity | all-sensitivity
  --solver NAME               cluster | nocluster | nolupruning | exact | foodmatch | lifostack | insertion | bazelmans
  --dataset N                 dataset size suffix N from dataset/nodes_N.txt and dataset/edges_N.txt
  --query FILE                query file to copy and use as Query_N.txt
  --threads N                 ForkJoin parallelism passed to Java driver

Build options:
  --build MODE                compile | none
  --skip-download             skip dataset downloader script

Sensitivity options:
  --tw-factors CSV            comma-separated TW scaling factors (example: 0.7,0.85,1.0,1.15)
  --capacity-factors CSV      comma-separated capacity scaling factors (example: 0.8,1.0,1.2)

Other:
  -h, --help                  show this help

Examples:
  ./run.sh --mode single --solver exact --dataset 6105
  ./run.sh --mode ablation --dataset 285050
  ./run.sh --mode tw-sensitivity --solver cluster --dataset 21048 --tw-factors 0.8,1.0,1.2
  ./run.sh --mode capacity-sensitivity --solver insertion --dataset 6105 --capacity-factors 0.7,1.0,1.3
EOF
}

to_solver_flag() {
    case "$1" in
        cluster|optload|default) echo "--cluster" ;;
        nocluster) echo "--nocluster" ;;
        nolupruning) echo "--nolupruning" ;;
        exact) echo "--exact" ;;
        foodmatch) echo "--foodmatch" ;;
        lifostack|lifo) echo "--lifostack" ;;
        insertion) echo "--insertion" ;;
        bazelmans) echo "--bazelmans" ;;
        *)
            echo "Unknown solver: $1" >&2
            exit 1
            ;;
    esac
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --mode)
                MODE="$2"
                shift 2
                ;;
            --mode=*)
                MODE="${1#*=}"
                shift
                ;;
            --solver)
                SOLVER="$2"
                shift 2
                ;;
            --solver=*)
                SOLVER="${1#*=}"
                shift
                ;;
            --dataset|--nodes)
                DATASET="$2"
                shift 2
                ;;
            --dataset=*|--nodes=*)
                DATASET="${1#*=}"
                shift
                ;;
            --query)
                QUERY_FILE="$2"
                shift 2
                ;;
            --query=*)
                QUERY_FILE="${1#*=}"
                shift
                ;;
            --threads)
                THREADS="$2"
                shift 2
                ;;
            --threads=*)
                THREADS="${1#*=}"
                shift
                ;;
            --tw-factors)
                TW_FACTORS="$2"
                shift 2
                ;;
            --tw-factors=*)
                TW_FACTORS="${1#*=}"
                shift
                ;;
            --capacity-factors)
                CAPACITY_FACTORS="$2"
                shift 2
                ;;
            --capacity-factors=*)
                CAPACITY_FACTORS="${1#*=}"
                shift
                ;;
            --build)
                BUILD_MODE="$2"
                shift 2
                ;;
            --build=*)
                BUILD_MODE="${1#*=}"
                shift
                ;;
            --skip-download)
                SKIP_DOWNLOAD=true
                shift
                ;;
            -h|--help)
                print_help
                exit 0
                ;;
            *)
                echo "Unknown argument: $1" >&2
                print_help
                exit 1
                ;;
        esac
    done
}

validate_inputs() {
    case "$MODE" in
        single|ablation|tw-sensitivity|capacity-sensitivity|all-sensitivity) ;;
        *)
            echo "Invalid mode: $MODE" >&2
            exit 1
            ;;
    esac

    case "$BUILD_MODE" in
        compile|none) ;;
        *)
            echo "Invalid build mode: $BUILD_MODE" >&2
            exit 1
            ;;
    esac

    [[ "$DATASET" =~ ^[0-9]+$ ]] || {
        echo "Dataset must be numeric. Received: $DATASET" >&2
        exit 1
    }

    local nodes_file="$ROOT_DIR/dataset/nodes_${DATASET}.txt"
    local edges_file="$ROOT_DIR/dataset/edges_${DATASET}.txt"
    [[ -f "$nodes_file" ]] || { echo "Missing dataset file: $nodes_file" >&2; exit 1; }
    [[ -f "$edges_file" ]] || { echo "Missing dataset file: $edges_file" >&2; exit 1; }

    if [[ -n "$QUERY_FILE" ]]; then
        [[ -f "$QUERY_FILE" ]] || { echo "Query file not found: $QUERY_FILE" >&2; exit 1; }
    else
        QUERY_FILE="$ROOT_DIR/Query_${DATASET}.txt"
        [[ -f "$QUERY_FILE" ]] || {
            echo "Missing query file: $QUERY_FILE" >&2
            echo "Provide one with --query or create Query_${DATASET}.txt" >&2
            exit 1
        }
    fi
}

compile_code() {
    if [[ "$BUILD_MODE" == "none" ]]; then
        echo "Skipping build (--build none)."
        return
    fi

    echo "Compiling Java sources..."
    (cd "$ROOT_DIR/src" && javac *.java)
}

run_driver() {
    local solver_flag="$1"
    shift

    local args=("$ROOT_DIR" "$solver_flag" "--nodes=${DATASET}" "--query=${QUERY_FILE}")
    if [[ -n "$THREADS" ]]; then
        args+=("--threads=${THREADS}")
    fi
    args+=("$@")

    echo "Running: java -cp src VRPLoadingUnloadingMain ${args[*]}"
    java -cp "$ROOT_DIR/src" VRPLoadingUnloadingMain "${args[@]}"
}

run_ablation() {
    local variants=("--cluster" "--nocluster" "--nolupruning")
    for variant in "${variants[@]}"; do
        local label="${variant#--}"
        echo ""
        echo "=== Ablation variant: ${label} ==="
        run_driver "$variant" "--output-suffix=ABL_${label}"
    done
}

run_tw_sensitivity() {
    local solver_flag="$1"
    IFS=',' read -r -a factors <<< "$TW_FACTORS"
    for factor in "${factors[@]}"; do
        local clean="${factor//./p}"
        echo ""
        echo "=== TW sensitivity factor: ${factor} ==="
        run_driver "$solver_flag" "--tw-scale=${factor}" "--output-suffix=TW_${clean}"
    done
}

run_capacity_sensitivity() {
    local solver_flag="$1"
    IFS=',' read -r -a factors <<< "$CAPACITY_FACTORS"
    for factor in "${factors[@]}"; do
        local clean="${factor//./p}"
        echo ""
        echo "=== Capacity sensitivity factor: ${factor} ==="
        run_driver "$solver_flag" "--capacity-scale=${factor}" "--output-suffix=CAP_${clean}"
    done
}

main() {
    parse_args "$@"

    if [[ "$SKIP_DOWNLOAD" == false && -x "$ROOT_DIR/scripts/download-dataset.sh" ]]; then
        if [[ "$DATASET" == "285050" ]]; then
            "$ROOT_DIR/scripts/download-dataset.sh" || {
                echo "Dataset check/download failed." >&2
                exit 1
            }
        else
            echo "Skipping downloader for dataset $DATASET (downloader targets 285050 by default)."
        fi
    fi

    validate_inputs
    compile_code

    local solver_flag
    solver_flag="$(to_solver_flag "$SOLVER")"

    case "$MODE" in
        single)
            run_driver "$solver_flag"
            ;;
        ablation)
            run_ablation
            ;;
        tw-sensitivity)
            run_tw_sensitivity "$solver_flag"
            ;;
        capacity-sensitivity)
            run_capacity_sensitivity "$solver_flag"
            ;;
        all-sensitivity)
            run_tw_sensitivity "$solver_flag"
            run_capacity_sensitivity "$solver_flag"
            ;;
    esac
}

main "$@"

