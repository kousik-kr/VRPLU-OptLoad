#!/bin/bash
# Usage: ./run.sh [solver-flag] [--nodes=N]
#
# Solver flags:
#   --cluster       Default OptLoad (clustering + LU pruning)
#   --nocluster     Ablation: OptLoad without clustering
#   --nolupruning   Ablation: OptLoad without LU pruning
#   --exact         Exact solver
#   --foodmatch     FoodMatch-inspired solver
#   --lifostack     LIFO stack solver
#   --insertion     Greedy insertion solver
#   --bazelmans     Bazelmans baseline solver
#
# Example: ./run.sh --cluster
#          ./run.sh --nocluster --nodes=6105
#          ./run.sh --nolupruning

set -euo pipefail

# Current workspace root
ROOT_DIR=$(pwd)

# Check and download dataset if needed
echo "Checking dataset availability..."
if [ -x "$ROOT_DIR/scripts/download-dataset.sh" ]; then
    "$ROOT_DIR/scripts/download-dataset.sh" || {
        echo "Dataset check failed. Please ensure dataset files are available."
        exit 1
    }
else
    echo "Warning: download-dataset.sh not found, skipping dataset check"
fi

echo ""
echo "Starting compilation and execution..."
echo ""

cd src/

# Compile all Java files
javac *.java

# Run the main Java program
java VRPLoadingUnloadingMain "$ROOT_DIR" "$@"

exit 0

