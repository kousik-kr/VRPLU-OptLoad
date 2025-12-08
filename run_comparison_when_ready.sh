#!/bin/bash

# Monitor all three solvers and run comparison when complete

echo "Monitoring solver progress..."
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
    clear
    echo "=== SOLVER PROGRESS MONITORING ==="
    echo "$(date)"
    echo ""
    
    # Check insertion
    if [ -f /tmp/insertion_run.log ]; then
        insertion_completed=$(grep -c "Finished processing query" /tmp/insertion_run.log || echo "0")
        insertion_current=$(tail -50 /tmp/insertion_run.log | grep "Starting insertion heuristic solver for query" | tail -1 | sed 's/.*query //' || echo "?")
        echo "Insertion: $insertion_completed/140 completed (current: query $insertion_current)"
    else
        insertion_completed=0
        echo "Insertion: Not started"
    fi
    
    # Check LIFO
    if [ -f /tmp/lifo_run.log ]; then
        lifo_completed=$(grep -c "Finished processing query" /tmp/lifo_run.log || echo "0")
        lifo_current=$(tail -50 /tmp/lifo_run.log | grep "Starting LIFO stack solver for query" | tail -1 | sed 's/.*query //' || echo "?")
        echo "LIFO:      $lifo_completed/140 completed (current: query $lifo_current)"
    else
        lifo_completed=0
        echo "LIFO: Not started"
    fi
    
    # Check exact
    if [ -f /tmp/exact_run.log ]; then
        exact_completed=$(grep -c "Finished processing query" /tmp/exact_run.log || echo "0")
        exact_current=$(tail -50 /tmp/exact_run.log | grep "Starting exact algorithm solver for query" | tail -1 | sed 's/.*query //' || echo "?")
        echo "Exact:     $exact_completed/140 completed (current: query $exact_current)"
    else
        exact_completed=0
        echo "Exact: Not started"
    fi
    
    echo ""
    
    # Check if all complete
    if [ "$insertion_completed" -eq 140 ] && [ "$lifo_completed" -eq 140 ] && [ "$exact_completed" -eq 140 ]; then
        echo "=== ALL SOLVERS COMPLETE! ==="
        echo ""
        echo "Running comparison script..."
        python3 /home/koushik/VRPLU-OptLoad/compare_solvers.py
        echo ""
        echo "Comparison complete! Results saved to:"
        echo "  - solver_comparison.csv"
        echo "  - solver_comparison.txt"
        echo ""
        
        if [ -f solver_comparison.txt ]; then
            echo "=== COMPARISON SUMMARY ==="
            cat solver_comparison.txt
        fi
        
        break
    fi
    
    # Show estimated time remaining
    total_completed=$((insertion_completed + lifo_completed + exact_completed))
    total_needed=$((140 * 3))
    percent=$((total_completed * 100 / total_needed))
    echo "Overall progress: $total_completed / $total_needed queries ($percent%)"
    
    # Check if processes are still running
    if ! ps aux | grep -E "java.*VRPLoadingUnloadingMain" | grep -v grep > /dev/null; then
        echo ""
        echo "WARNING: No solver processes detected!"
        echo "Checking logs for errors..."
        break
    fi
    
    echo ""
    echo "Next update in 30 seconds..."
    sleep 30
done

echo ""
echo "Monitoring stopped."
