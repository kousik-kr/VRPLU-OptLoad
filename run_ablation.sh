#!/bin/bash
# Ablation study runner for OptLoad
# Runs three variants and compares results:
#   1. Full OptLoad (clustering + LU pruning)
#   2. OptLoad without clustering
#   3. OptLoad without LU pruning
#
# Usage: ./run_ablation.sh [--nodes=N]
# Example: ./run_ablation.sh --nodes=6105

set -euo pipefail

ROOT_DIR=$(pwd)
EXTRA_ARGS="${@}"

echo "============================================"
echo "  OptLoad Ablation Study"
echo "============================================"
echo "Extra args: ${EXTRA_ARGS:-none}"
echo ""

# Check and download dataset if needed
if [ -x "$ROOT_DIR/scripts/download-dataset.sh" ]; then
    "$ROOT_DIR/scripts/download-dataset.sh" || {
        echo "Dataset check failed."
        exit 1
    }
fi

cd src/
echo "Compiling..."
javac *.java
echo "Compilation successful."
echo ""

# --- Variant 1: Full OptLoad (clustering + LU pruning) ---
echo "============================================"
echo "  [1/3] Full OptLoad (clustering + LU pruning)"
echo "============================================"
START=$(date +%s%N)
java VRPLoadingUnloadingMain "$ROOT_DIR" --cluster $EXTRA_ARGS
END=$(date +%s%N)
ELAPSED_1=$(( (END - START) / 1000000 ))
echo "  => Completed in ${ELAPSED_1} ms"
echo ""

# --- Variant 2: OptLoad without clustering ---
echo "============================================"
echo "  [2/3] OptLoad WITHOUT Clustering"
echo "============================================"
START=$(date +%s%N)
java VRPLoadingUnloadingMain "$ROOT_DIR" --nocluster $EXTRA_ARGS
END=$(date +%s%N)
ELAPSED_2=$(( (END - START) / 1000000 ))
echo "  => Completed in ${ELAPSED_2} ms"
echo ""

# --- Variant 3: OptLoad without LU pruning ---
echo "============================================"
echo "  [3/3] OptLoad WITHOUT LU Pruning"
echo "============================================"
START=$(date +%s%N)
java VRPLoadingUnloadingMain "$ROOT_DIR" --nolupruning $EXTRA_ARGS
END=$(date +%s%N)
ELAPSED_3=$(( (END - START) / 1000000 ))
echo "  => Completed in ${ELAPSED_3} ms"
echo ""

# --- Summary ---
echo "============================================"
echo "  Ablation Study Summary"
echo "============================================"
echo ""
echo "  Full OptLoad:          ${ELAPSED_1} ms"
echo "  Without Clustering:    ${ELAPSED_2} ms"
echo "  Without LU Pruning:    ${ELAPSED_3} ms"
echo ""

# Detect node count from args for output file names
NODE_COUNT="285050"
for arg in $EXTRA_ARGS; do
    if [[ "$arg" == --nodes=* ]]; then
        NODE_COUNT="${arg#--nodes=}"
    fi
done

echo "Output files:"
echo "  Full OptLoad:       ${ROOT_DIR}/Output_${NODE_COUNT}.txt"
echo "  No Clustering:      ${ROOT_DIR}/OutputNoCluster_${NODE_COUNT}.txt"
echo "  No LU Pruning:      ${ROOT_DIR}/OutputNoLUPruning_${NODE_COUNT}.txt"
echo ""
echo "============================================"
echo "  Ablation study complete!"
echo "============================================"
