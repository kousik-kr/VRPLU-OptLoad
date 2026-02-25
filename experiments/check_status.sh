#!/bin/bash
# Quick experiment progress monitor
# Usage: ./experiments/check_status.sh

cd "$(dirname "$0")/.." || exit 1

echo "============================================================"
echo "VRPLU-OptLoad Experiment Status — $(date)"
echo "============================================================"

# Check if runner is alive
PID=$(ps aux | grep "run_all_experiments" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$PID" ]; then
    echo "Runner: ACTIVE (PID $PID)"
    JAVA=$(ps aux | grep "VRPLoadingUnloadingMain" | grep -v grep | awk '{print $NF}')
    if [ -n "$JAVA" ]; then
        echo "  Currently running: $(ps aux | grep VRPLoadingUnloadingMain | grep -v grep | sed 's/.*queries\///' | sed 's/ --.*//')"
    fi
else
    echo "Runner: NOT RUNNING"
fi

echo ""
python3 -c "
import json, os
cp = json.load(open('experiments/results/checkpoint.json'))
completed = cp.get('completed', [])
from collections import Counter
steps = Counter(c.split('_')[0] for c in completed)
total_needed = {'step1': 150, 'step2': 240, 'step3': 90, 'step4': 240, 'step5': 80, 'step6': 60, 'step7': 80}
print('Step  | Done | Total | Remaining | Progress')
print('------|------|-------|-----------|----------')
total_done = 0
total_all = 0
for s in ['step1','step2','step3','step4','step5','step6','step7']:
    done = steps.get(s, 0)
    total = total_needed[s]
    pct = done/total*100 if total > 0 else 0
    bar = '█' * int(pct/5) + '░' * (20 - int(pct/5))
    print(f'{s} | {done:4d} | {total:5d} | {total-done:9d} | {bar} {pct:.0f}%')
    total_done += done
    total_all += total
pct = total_done/total_all*100
print(f'TOTAL | {total_done:4d} | {total_all:5d} | {total_all-total_done:9d} | {pct:.1f}%')
"

echo ""
echo "CSV files:"
for f in experiments/results/step*.csv; do
    rows=$(($(wc -l < "$f") - 1))
    printf "  %-40s %d rows\n" "$(basename $f)" "$rows"
done
echo "============================================================"
