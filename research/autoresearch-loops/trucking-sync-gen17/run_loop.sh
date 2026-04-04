#!/usr/bin/env bash
# Gen16 Autoresearch Benchmark Script
# Usage: ./run_loop.sh [script_name] [num_runs]
# Defaults: sync_daily_optimized.py, 3 runs

set -euo pipefail
cd "$(dirname "$0")"

SCRIPT="${1:-sync_daily_optimized.py}"
RUNS="${2:-3}"

echo "=== Benchmarking: $SCRIPT ($RUNS runs) ==="
echo ""

declare -a rpms
declare -a upserts
declare -a totals

for i in $(seq 1 "$RUNS"); do
    echo "--- Run $i/$RUNS ---"
    output=$(python3 "$SCRIPT" 2>&1)
    echo "$output" | tail -8

    # Extract metrics (macOS-compatible sed)
    rpm=$(echo "$output" | grep 'RPM:' | tail -1 | sed 's/.*RPM: \([0-9]*\).*/\1/' || echo "0")
    upsert=$(echo "$output" | grep 'Phase 3+4' | sed 's/.*: \([0-9]*\)ms.*/\1/' || echo "0")
    total=$(echo "$output" | grep 'Total pipeline time' | sed 's/.*: \([0-9.]*\)s.*/\1/' || echo "0")

    rpms+=("$rpm")
    upserts+=("$upsert")
    totals+=("$total")
    echo ""
done

echo "=== RESULTS: $SCRIPT ==="
echo "RPMs: ${rpms[*]}"
echo "Upsert(ms): ${upserts[*]}"
echo "Total(s): ${totals[*]}"

# Calculate median RPM (sort + pick middle)
sorted_rpms=($(printf '%s\n' "${rpms[@]}" | sort -n))
mid=$(( (RUNS - 1) / 2 ))
echo "Median RPM: ${sorted_rpms[$mid]}"

sorted_upserts=($(printf '%s\n' "${upserts[@]}" | sort -n))
echo "Median Upsert(ms): ${sorted_upserts[$mid]}"
