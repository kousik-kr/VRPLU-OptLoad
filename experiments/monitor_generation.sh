#!/bin/bash
# Monitor query generation progress

QUERY_DIR="/home/gunturi/VRPLU-OptLoad/experiments/queries"
LOG_FILE="/home/gunturi/VRPLU-OptLoad/experiments/logs/query_gen_full.log"

echo "Query Generation Monitor"
echo "========================"
echo ""

# Check if process is running
if pgrep -f "tour_query_generator.py" > /dev/null; then
    echo "Status: RUNNING"
else
    echo "Status: NOT RUNNING"
fi

echo ""
echo "Progress by N value:"
echo "--------------------"

total=0
for n in 10 20 40 60 80 100; do
    dir="$QUERY_DIR/N_$n"
    if [ -d "$dir" ]; then
        count=$(ls "$dir"/*.txt 2>/dev/null | wc -l)
        total=$((total + count))
        printf "N=%3d: %3d/100 queries\n" $n $count
    else
        printf "N=%3d:   0/100 queries\n" $n
    fi
done

echo "--------------------"
echo "Total: $total/600 queries"
echo ""

echo "Latest log entries:"
echo "-------------------"
tail -5 "$LOG_FILE" 2>/dev/null || echo "No log file found"
