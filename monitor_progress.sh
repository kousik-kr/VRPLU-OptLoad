#!/bin/bash

# Monitor progress of solver runs

echo "=== INSERTION SOLVER PROGRESS ==="
if [ -f /tmp/insertion_run.log ]; then
    last_query=$(tail -50 /tmp/insertion_run.log | grep "Starting insertion heuristic solver for query" | tail -1 | sed 's/.*query //')
    echo "Currently processing query: $last_query"
    
    completed=$(grep -c "Finished processing query" /tmp/insertion_run.log || echo "0")
    echo "Completed queries: $completed / 140"
    
    if [ -f OutputInsertion_285050.txt ]; then
        lines=$(wc -l < OutputInsertion_285050.txt)
        echo "Output file lines: $lines"
    fi
else
    echo "Insertion solver not started yet"
fi

echo ""
echo "=== LIFO SOLVER PROGRESS ==="
if [ -f /tmp/lifo_run.log ]; then
    last_query=$(tail -50 /tmp/lifo_run.log | grep "Starting LIFO stack solver for query" | tail -1 | sed 's/.*query //')
    echo "Currently processing query: $last_query"
    
    completed=$(grep -c "Finished processing query" /tmp/lifo_run.log || echo "0")
    echo "Completed queries: $completed / 140"
else
    echo "LIFO solver not started yet"
fi

echo ""
echo "=== EXACT SOLVER PROGRESS ==="
if [ -f /tmp/exact_run.log ]; then
    last_query=$(tail -50 /tmp/exact_run.log | grep "Starting exact algorithm solver for query" | tail -1 | sed 's/.*query //')
    echo "Currently processing query: $last_query"
    
    completed=$(grep -c "Finished processing query" /tmp/exact_run.log || echo "0")
    echo "Completed queries: $completed / 140"
else
    echo "Exact solver not started yet"
fi

echo ""
echo "=== BACKGROUND PROCESSES ==="
ps aux | grep -E "(run.sh|VRPLoadingUnloadingMain)" | grep -v grep || echo "No solver processes found"
