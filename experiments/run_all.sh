#!/bin/bash
# Robust experiment runner script
# This script runs experiments in a way that won't be interrupted by terminal issues

cd /home/gunturi/VRPLU-OptLoad/experiments

# Create log file with timestamp
LOG_FILE="experiment_run_$(date +%Y%m%d_%H%M%S).log"

echo "Starting experiments at $(date)" | tee -a $LOG_FILE
echo "Log file: $LOG_FILE" | tee -a $LOG_FILE
echo "====================================" | tee -a $LOG_FILE

# Run the experiments
python3 simple_runner.py 2>&1 | tee -a $LOG_FILE

echo "====================================" | tee -a $LOG_FILE
echo "Experiments completed at $(date)" | tee -a $LOG_FILE

# Generate charts if results exist
if [ -f "results/experiment_results.json" ]; then
    echo "Generating charts..." | tee -a $LOG_FILE
    python3 generate_charts.py 2>&1 | tee -a $LOG_FILE
fi

echo "All done!" | tee -a $LOG_FILE
