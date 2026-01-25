#!/bin/bash
# Run VRP-LU experiments
cd /home/gunturi/VRPLU-OptLoad/experiments
python3 run_full_experiments.py --timeout 120 > experiment_output.log 2>&1
echo "Experiments completed. Check experiment_output.log for details."
