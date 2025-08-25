#!/bin/bash
echo "Monitoring orphaned orchestrator processes..."
echo "PID 97131 (enforce-code-quality-compliance)"
echo "PID 97265 (fix-orchestrator-subprocess-execution)"
echo ""

while true; do
    timestamp=$(date '+%H:%M:%S')

    # Check if processes still exist
    if ps -p 97131 > /dev/null 2>&1; then
        proc1_status="RUNNING"
    else
        proc1_status="COMPLETED/DEAD"
    fi

    if ps -p 97265 > /dev/null 2>&1; then
        proc2_status="RUNNING"
    else
        proc2_status="COMPLETED/DEAD"
    fi

    echo "[$timestamp] PID 97131: $proc1_status, PID 97265: $proc2_status"

    # Exit if both processes are done
    if [[ "$proc1_status" == "COMPLETED/DEAD" && "$proc2_status" == "COMPLETED/DEAD" ]]; then
        echo "Both processes completed!"
        break
    fi

    sleep 10
done
