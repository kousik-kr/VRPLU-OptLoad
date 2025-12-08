#!/bin/bash

# Test script to run query 1 with all solvers and compare results

echo "=== Testing Query 1 with Different Solvers ==="
echo

# Run with default clustering
echo "1. Running DEFAULT CLUSTERING solver..."
./run.sh 2>&1 | grep -A 30 "Query 1" | head -35
echo

# Run with exact algorithm
echo "2. Running EXACT ALGORITHM solver..."
./run.sh --exact 2>&1 | grep -A 10 "query 1" | head -15
echo

# Run with insertion heuristic
echo "3. Running INSERTION HEURISTIC solver..."
./run.sh --insertion-heuristic 2>&1 | grep -A 10 "query 1" | head -15
echo

# Run with LIFO stack
echo "4. Running LIFO STACK solver..."
./run.sh --lifo-stack 2>&1 | grep -A 10 "query 1" | head -15
echo

echo "=== Comparison Complete ==="
echo "Check output files: Output_*.txt, OutputExact_*.txt, OutputInsertionHeuristic_*.txt, OutputLifoStack_*.txt"
