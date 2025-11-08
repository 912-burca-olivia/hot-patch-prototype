#!/bin/bash
# Quick benchmark script - for faster testing (fewer repeats)
set -euo pipefail

echo "=== Quick Benchmark Mode ==="
echo "This runs a faster version with fewer repeats"
echo "For full benchmark, use: ./run-benchmark.sh"
echo

# Quick configuration
RESULTS_DIR="results"
CSV="$RESULTS_DIR/latency_quick.csv"
LOG="$RESULTS_DIR/benchmark_quick.log"
mkdir -p "$RESULTS_DIR"

# Reduced configuration for quick testing
LOADS=(0 100 400)  # Just 3 load levels
VERSIONS=(v1 v2 v3 v4 v5)  # First 5 versions only
REPEATS=2  # Reduced repeats

echo "Configuration:" | tee "$LOG"
echo "  Loads: ${LOADS[*]}" | tee -a "$LOG"
echo "  Versions: ${VERSIONS[*]}" | tee -a "$LOG"
echo "  Repeats: $REPEATS" | tee -a "$LOG"
echo "  Estimated time: 5-10 minutes" | tee -a "$LOG"
echo

# CSV header
cat > "$CSV" << 'HEADER'
timestamp,scenario,run_id,load_rps,op,version,orchestration_ms,client_ms,agent_ms,success
HEADER

# Build
echo "Building..." | tee -a "$LOG"
SKIP_AGENT_JAR=1 ./build.sh > /dev/null 2>&1
echo "✓ Build complete" | tee -a "$LOG"

# Start service
echo "Starting service..." | tee -a "$LOG"
if jps | grep -q BusinessRuleService; then
    pkill -f BusinessRuleService || true
    sleep 2
fi
./run-service.sh > "$RESULTS_DIR/service_quick.log" 2>&1 &
SERVICE_PID=$!
sleep 3

if ! jps | grep -q BusinessRuleService; then
    echo "ERROR: Service failed to start" | tee -a "$LOG"
    exit 1
fi
echo "✓ Service started" | tee -a "$LOG"

# Helper functions
run_load() {
    local rps="$1"
    if [ "$rps" -eq 0 ]; then
        LOAD_PID=""
        return
    fi
    ./run-load.sh 5 "$rps" > /dev/null 2>&1 &
    LOAD_PID=$!
    sleep 1
}

stop_load() {
    if [ -n "${LOAD_PID:-}" ] && kill -0 "$LOAD_PID" 2>/dev/null; then
        kill "$LOAD_PID" 2>/dev/null || true
        wait "$LOAD_PID" 2>/dev/null || true
    fi
    LOAD_PID=""
    sleep 0.5
}

# Quick Scenario 1: Patch vs Load
echo
echo "=== Quick Test: Patch vs Load ===" | tee -a "$LOG"
RUN=1

for L in "${LOADS[@]}"; do
    echo "  Testing ${L} rps..." | tee -a "$LOG"
    run_load "$L"
    
    for ((r=1; r<=REPEATS; r++)); do
        for V in "${VERSIONS[@]}"; do
            ./bench-apply.sh "$V" "$L" "Q1_patch" "$RUN" 2>&1 | tee -a "$LOG" >> "$CSV" || true
            RUN=$((RUN+1))
        done
    done
    
    stop_load
done

# Quick Scenario 2: Rollback
echo
echo "=== Quick Test: Rollback ===" | tee -a "$LOG"

for L in "${LOADS[@]}"; do
    echo "  Testing ${L} rps..." | tee -a "$LOG"
    run_load "$L"
    
    for ((r=1; r<=REPEATS; r++)); do
        ./bench-apply.sh "v3" "$L" "Q2_setup" "$RUN" 2>&1 >> "$CSV" || true
        ./bench-rollback.sh "$L" "Q2_rollback" "$RUN" "quick" 2>&1 | tee -a "$LOG" >> "$CSV" || true
        RUN=$((RUN+1))
    done
    
    stop_load
done

# Quick Scenario 3: Sequential
echo
echo "=== Quick Test: Sequential ===" | tee -a "$LOG"
L=100
run_load "$L"

for V in "${VERSIONS[@]}"; do
    ./bench-apply.sh "$V" "$L" "Q3_apply" "$RUN" 2>&1 | tee -a "$LOG" >> "$CSV" || true
    RUN=$((RUN+1))
done

for ((i=1; i<=${#VERSIONS[@]}; i++)); do
    ./bench-rollback.sh "$L" "Q3_rollback" "$RUN" "step$i" 2>&1 | tee -a "$LOG" >> "$CSV" || true
    RUN=$((RUN+1))
done

stop_load

# Cleanup
echo
echo "Cleaning up..." | tee -a "$LOG"
stop_load
kill $SERVICE_PID 2>/dev/null || true
wait $SERVICE_PID 2>/dev/null || true

echo
echo "=== Quick Benchmark Complete! ===" | tee -a "$LOG"
echo "Results: $CSV" | tee -a "$LOG"
echo

# Generate plots
echo "Generating plots..." | tee -a "$LOG"
if command -v python3 >/dev/null 2>&1; then
    # Use quick CSV
    mv results/latency.csv results/latency_backup.csv 2>/dev/null || true
    mv results/latency_quick.csv results/latency.csv
    
    python3 generate-plots.py
    python3 generate-dashboard.py
    
    # Restore original if it existed
    mv results/latency.csv results/latency_quick.csv
    mv results/latency_backup.csv results/latency.csv 2>/dev/null || true
    
    echo "✓ Plots generated" | tee -a "$LOG"
    echo "  View: results/dashboard.html" | tee -a "$LOG"
else
    echo "⚠ Python3 not found - skipping plots" | tee -a "$LOG"
fi

echo
echo "Quick benchmark complete! For full results, run: ./run-benchmark.sh"