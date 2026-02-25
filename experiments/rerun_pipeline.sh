#!/bin/bash
# =============================================================
# Rerun Pipeline — Migrate old results + Rerun Pareto solvers
# =============================================================
#
# This script:
#   1. Migrates old CSV results (Insertion, FoodMatch, LIFO) to new per-route format
#   2. Resets checkpoint for Pareto solvers
#   3. Reruns Pareto solvers (OptLoad, Exact, NoCluster, NoLUPruning)
#      with new per-route CSV output format
#
# Step parameter redistribution:
#   Step 1: Core comparison (Oldenburg, N=2,5,10) — all solvers
#   Step 2: Scalability (London) — OptLoad N=5..35, Insertion/FoodMatch N=10..80
#   Step 3: Network scalability (all networks, N=20)
#   Step 4: Ablation (London, N=5,10,15,20,25,30,35)
#   Step 5: Search space (London, N=5,10,15,20,25,30,35) — OptLoad only
#   Step 6: Parallel (London, N=20, threads=1,2,4,8,16,24)
#   Step 7: Sensitivity (London, N=20, cap/tw variations)
#
# Usage:
#   ./rerun_pipeline.sh                # Full pipeline (migrate + rerun all)
#   ./rerun_pipeline.sh --step 1 4     # Rerun specific steps only
#   ./rerun_pipeline.sh --migrate-only # Only migrate, don't rerun
#   ./rerun_pipeline.sh --rerun-only   # Only rerun (assumes already migrated)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

MIGRATE_ONLY=false
RERUN_ONLY=false
STEPS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --migrate-only) MIGRATE_ONLY=true; shift ;;
        --rerun-only)   RERUN_ONLY=true; shift ;;
        --step)         shift; STEPS="$@"; break ;;
        *)              echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "============================================================"
echo "VRPLU-OptLoad Rerun Pipeline"
echo "============================================================"
echo "Time: $(date)"
echo ""

# Phase 1: Migration
if [ "$RERUN_ONLY" = false ]; then
    echo "--- Phase 1: Migrate old CSV results ---"
    python3 migrate_old_results.py
    echo ""
fi

if [ "$MIGRATE_ONLY" = true ]; then
    echo "Migration complete. Use --rerun-only to run Pareto solvers."
    exit 0
fi

# Phase 2: Reset checkpoint for Pareto solvers
echo "--- Phase 2: Reset checkpoint ---"
python3 run_all_experiments.py --reset-checkpoint
echo ""

# Phase 3: Rerun Pareto solvers only
echo "--- Phase 3: Rerun Pareto solvers (OptLoad, Exact, NoCluster, NoLUPruning) ---"
echo "This will append to the migrated CSV files."
echo ""

if [ -n "$STEPS" ]; then
    echo "Running steps: $STEPS"
    python3 run_all_experiments.py --solvers OptLoad Exact NoCluster NoLUPruning --step $STEPS 2>&1 | tee results/rerun_output.log
else
    echo "Running all steps (1-7)"
    python3 run_all_experiments.py --solvers OptLoad Exact NoCluster NoLUPruning 2>&1 | tee results/rerun_output.log
fi

echo ""
echo "============================================================"
echo "Pipeline complete at $(date)"
echo "Results in: $SCRIPT_DIR/results/"
echo ""
echo "CSV summary:"
for f in results/step*.csv; do
    rows=$(wc -l < "$f")
    solvers=$(cut -d, -f3 "$f" | sort -u | tail -n +2 | tr '\n' ', ')
    echo "  $(basename $f): $rows rows [$solvers]"
done
echo "============================================================"
