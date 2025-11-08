#!/bin/bash
# Master benchmark script - comprehensive evaluation
set -euo pipefail

RESULTS_DIR="results"
CSV="$RESULTS_DIR/latency.csv"
LOG="$RESULTS_DIR/benchmark.log"
mkdir -p "$RESULTS_DIR"

echo "=== JVM Hot Patching Benchmark Suite ===" | tee "$LOG"
echo "Started: $(date)" | tee -a "$LOG"
echo

# CSV header with enhanced metrics
cat > "$CSV" << 'HEADER'
timestamp,scenario,run_id,load_rps,op,version,orchestration_ms,client_ms,agent_ms,success
HEADER

# Configuration
LOADS=(0 50 100 200 400 800)  # Wider range
VERSIONS=(v1 v2 v3 v4 v5 v6 v7 v8 v9 v10)
REPEATS=5  # Multiple runs for statistical validity
WARMUP_RUNS=2

echo "Configuration:" | tee -a "$LOG"
echo "  Loads: ${LOADS[*]}" | tee -a "$LOG"
echo "  Versions: ${VERSIONS[*]}" | tee -a "$LOG"
echo "  Repeats per condition: $REPEATS" | tee -a "$LOG"
echo "  Warmup runs: $WARMUP_RUNS" | tee -a "$LOG"
echo | tee -a "$LOG"

# Rebuild to ensure latest code
echo "Building project..." | tee -a "$LOG"
SKIP_AGENT_JAR=1 ./build.sh > /dev/null 2>&1
echo "✓ Build complete" | tee -a "$LOG"
echo

# Start service
echo "Starting BusinessRuleService..." | tee -a "$LOG"
if jps | grep -q BusinessRuleService; then
    pkill -f BusinessRuleService || true
    sleep 2
fi
./run-service.sh > "$RESULTS_DIR/service.log" 2>&1 &
SERVICE_PID=$!
sleep 3

if ! jps | grep -q BusinessRuleService; then
    echo "ERROR: Service failed to start" | tee -a "$LOG"
    exit 1
fi
echo "✓ Service running (PID: $SERVICE_PID)" | tee -a "$LOG"
echo

# Helper functions
run_load() {
    local rps="$1"
    if [ "$rps" -eq 0 ]; then
        LOAD_PID=""
        return
    fi
    ./run-load.sh 5 "$rps" > "$RESULTS_DIR/load_${rps}.log" 2>&1 &
    LOAD_PID=$!
    sleep 2  # Let load stabilize
}

stop_load() {
    if [ -n "${LOAD_PID:-}" ] && kill -0 "$LOAD_PID" 2>/dev/null; then
        kill "$LOAD_PID" 2>/dev/null || true
        wait "$LOAD_PID" 2>/dev/null || true
    fi
    LOAD_PID=""
    sleep 1
}

run_apply() {
    local ver="$1" load="$2" scen="$3" run="$4"
    ./bench-apply.sh "$ver" "$load" "$scen" "$run" 2>&1 | tee -a "$LOG" || echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ"),$scen,$run,$load,patch,$ver,NaN,NaN,NaN,false"
}

run_rollback() {
    local load="$1" scen="$2" run="$3" label="$4"
    ./bench-rollback.sh "$load" "$scen" "$run" "$label" 2>&1 | tee -a "$LOG" || echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ"),$scen,$run,$load,rollback,$label,NaN,NaN,NaN,false"
}

# Scenario 1: Patch Latency vs Load (with statistical repeats)
echo "=== Scenario 1: Patch Latency vs Load ===" | tee -a "$LOG"
SCENARIO="S1_patch_vs_load"
RUN=1

for L in "${LOADS[@]}"; do
    echo "  Testing load: ${L} rps" | tee -a "$LOG"
    run_load "$L"
    
    # Warmup
    echo "    Warmup runs..." | tee -a "$LOG"
    for ((w=1; w<=WARMUP_RUNS; w++)); do
        run_apply "${VERSIONS[0]}" "$L" "${SCENARIO}_warmup" "$RUN" >> "$CSV"
        run_rollback "$L" "${SCENARIO}_warmup" "$RUN" "warmup" >> "$CSV"
        RUN=$((RUN+1))
    done
    
    # Actual measurements
    echo "    Measurement runs..." | tee -a "$LOG"
    for ((r=1; r<=REPEATS; r++)); do
        for V in "${VERSIONS[@]}"; do
            run_apply "$V" "$L" "$SCENARIO" "$RUN" >> "$CSV"
            sleep 0.1
            RUN=$((RUN+1))
        done
    done
    
    stop_load
    echo "    ✓ Completed ${L} rps" | tee -a "$LOG"
done

echo "✓ Scenario 1 complete" | tee -a "$LOG"
echo

# Scenario 2: Rollback Latency vs Load
echo "=== Scenario 2: Rollback Latency vs Load ===" | tee -a "$LOG"
SCENARIO="S2_rollback_vs_load"
RUN=1

for L in "${LOADS[@]}"; do
    echo "  Testing load: ${L} rps" | tee -a "$LOG"
    run_load "$L"
    
    for ((r=1; r<=REPEATS; r++)); do
        # Apply a patch, then rollback
        run_apply "v5" "$L" "${SCENARIO}_setup" "$RUN" >> "$CSV"
        run_rollback "$L" "$SCENARIO" "$RUN" "v5_to_v0" >> "$CSV"
        RUN=$((RUN+1))
    done
    
    stop_load
    echo "    ✓ Completed ${L} rps" | tee -a "$LOG"
done

echo "✓ Scenario 2 complete" | tee -a "$LOG"
echo

# Scenario 3: Sequential Patches (Patch Stack Depth)
echo "=== Scenario 3: Sequential Patch Stack ===" | tee -a "$LOG"
SCENARIO="S3_sequential"
L=200  # Representative load
RUN=1

run_load "$L"
sleep 2

echo "  Applying patches sequentially..." | tee -a "$LOG"
for V in "${VERSIONS[@]}"; do
    run_apply "$V" "$L" "${SCENARIO}_apply" "$RUN" >> "$CSV"
    RUN=$((RUN+1))
    sleep 0.2
done

echo "  Rolling back sequentially..." | tee -a "$LOG"
for ((i=1; i<=${#VERSIONS[@]}; i++)); do
    run_rollback "$L" "${SCENARIO}_rollback" "$RUN" "step_$i" >> "$CSV"
    RUN=$((RUN+1))
    sleep 0.2
done

stop_load
echo "✓ Scenario 3 complete" | tee -a "$LOG"
echo

# Scenario 4: Patch Complexity Analysis (different rule versions)
echo "=== Scenario 4: Patch Complexity Impact ===" | tee -a "$LOG"
SCENARIO="S4_complexity"
L=100
RUN=1

run_load "$L"

# Test each version multiple times to see variation
for V in "${VERSIONS[@]}"; do
    echo "  Testing version: $V" | tee -a "$LOG"
    for ((r=1; r<=10; r++)); do  # More repeats for complexity analysis
        run_apply "$V" "$L" "$SCENARIO" "$RUN" >> "$CSV"
        run_rollback "$L" "${SCENARIO}_rollback" "$RUN" "$V" >> "$CSV"
        RUN=$((RUN+1))
        sleep 0.1
    done
done

stop_load
echo "✓ Scenario 4 complete" | tee -a "$LOG"
echo

# Scenario 5: Sustained Load Pattern
echo "=== Scenario 5: Sustained Load Pattern ===" | tee -a "$LOG"
SCENARIO="S5_sustained"
L=300
RUN=1

run_load "$L"
echo "  Running sustained load test (60 operations)..." | tee -a "$LOG"

for ((i=1; i<=60; i++)); do
    V=${VERSIONS[$((i % ${#VERSIONS[@]}))]}
    run_apply "$V" "$L" "$SCENARIO" "$RUN" >> "$CSV"
    RUN=$((RUN+1))
    sleep 0.5
    
    if ((i % 10 == 0)); then
        echo "    Completed $i/60 operations" | tee -a "$LOG"
    fi
done

stop_load
echo "✓ Scenario 5 complete" | tee -a "$LOG"
echo

# Cleanup
echo "Cleaning up..." | tee -a "$LOG"
stop_load
kill $SERVICE_PID 2>/dev/null || true
wait $SERVICE_PID 2>/dev/null || true

echo | tee -a "$LOG"
echo "=== Benchmark Complete ===" | tee -a "$LOG"
echo "Completed: $(date)" | tee -a "$LOG"
echo "Results saved to: $CSV" | tee -a "$LOG"
echo "Log saved to: $LOG" | tee -a "$LOG"
echo | tee -a "$LOG"

# Generate plots
echo "Generating visualizations..." | tee -a "$LOG"
if command -v python3 >/dev/null 2>&1; then
    python generate-plots.py
    python generate-dashboard.py
    echo "✓ Plots and dashboard generated" | tee -a "$LOG"
    echo "  View results: results/dashboard.html" | tee -a "$LOG"
else
    echo "⚠ Python3 not found - skipping visualization" | tee -a "$LOG"
    echo "  Install Python3 and run: python3 generate-plots.py" | tee -a "$LOG"
fi

echo
echo "All done! 🎉"