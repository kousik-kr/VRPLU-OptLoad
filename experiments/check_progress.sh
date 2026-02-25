#!/bin/bash
# Check experiment progress
RESULTS_DIR="/home/koushik/VRPLU-OptLoad/experiments/results"

echo "=== Experiment Progress ==="
echo ""

# Check if process is running
if pgrep -f "run_all_experiments" > /dev/null; then
    echo "Status: RUNNING (PID: $(pgrep -f run_all_experiments))"
else
    echo "Status: NOT RUNNING"
fi
echo ""

# Check checkpoint
if [ -f "$RESULTS_DIR/checkpoint.json" ]; then
    COMPLETED=$(python3 -c "import json; d=json.load(open('$RESULTS_DIR/checkpoint.json')); print(len(d.get('completed',[])))")
    echo "Total completed runs: $COMPLETED"
    echo ""
    echo "Last 5 completed:"
    python3 -c "import json; d=json.load(open('$RESULTS_DIR/checkpoint.json')); [print(f'  {x}') for x in d.get('completed',[])[-5:]]"
fi
echo ""

# Check CSV files
echo "=== CSV files ==="
for csv in "$RESULTS_DIR"/step*.csv; do
    if [ -f "$csv" ]; then
        lines=$(wc -l < "$csv")
        echo "  $(basename $csv): $((lines-1)) data rows"
    fi
done
echo ""

# Show last log lines
if [ -f "$RESULTS_DIR/experiment_log.txt" ]; then
    echo "=== Last 10 log lines ==="
    tail -10 "$RESULTS_DIR/experiment_log.txt"
fi
