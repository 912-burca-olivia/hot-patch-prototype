#!/bin/bash
# Master benchmark script - comprehensive evaluation
set -euo pipefail

RESULTS_DIR="results"
CSV="$RESULTS_DIR/latency.csv"
mkdir -p "$RESULTS_DIR"

echo "=== JVM Hot Patching Benchmark Suite ==="
echo "Started: $(date)"
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

echo "Configuration:"
echo "  Loads: ${LOADS[*]}"
echo "  Versions: ${VERSIONS[*]}"
echo "  Repeats per condition: $REPEATS"
echo "  Warmup runs: $WARMUP_RUNS"


# Rebuild to ensure latest code
echo "Building project..."
SKIP_AGENT_JAR=1 ./build.sh > /dev/null 2>&1
echo "✓ Build complete"
echo

# Start service
echo "Starting BusinessRuleService..."
if jps | grep -q BusinessRuleService; then
    pkill -f BusinessRuleService || true
    sleep 2
fi
./run-service.sh >/dev/null 2>&1 &
SERVICE_PID=$!
sleep 3

if ! jps | grep -q BusinessRuleService; then
    echo "ERROR: Service failed to start"
    exit 1
fi
echo "✓ Service running (PID: $SERVICE_PID)"
echo

# Helper functions
run_load() {
    local rps="$1"
    if [ "$rps" -eq 0 ]; then
        LOAD_PID=""
        return
    fi
    ./run-load.sh 5 "$rps" >/dev/null 2>&1 & 
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
    ./bench-apply.sh "$ver" "$load" "$scen" "$run" 2>&1 || echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ"),$scen,$run,$load,patch,$ver,NaN,NaN,NaN,false"
}

run_rollback() {
    local load="$1" scen="$2" run="$3" label="$4"
    ./bench-rollback.sh "$load" "$scen" "$run" "$label" 2>&1 || echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ"),$scen,$run,$load,rollback,$label,NaN,NaN,NaN,false"
}

# Scenario 1: Patch Latency vs Load (with statistical repeats)
echo "=== Scenario 1: Patch Latency vs Load ==="
SCENARIO="S1_patch_vs_load"
RUN=1

for L in "${LOADS[@]}"; do
    echo "  Testing load: ${L} rps"
    run_load "$L"
    
    # Warmup
    echo "    Warmup runs..."
    for ((w=1; w<=WARMUP_RUNS; w++)); do
        run_apply "${VERSIONS[0]}" "$L" "${SCENARIO}_warmup" "$RUN" >> "$CSV"
        run_rollback "$L" "${SCENARIO}_warmup" "$RUN" "warmup" >> "$CSV"
        RUN=$((RUN+1))
    done
    
    # Actual measurements
    echo "    Measurement runs..."
    for ((r=1; r<=REPEATS; r++)); do
        for V in "${VERSIONS[@]}"; do
            run_apply "$V" "$L" "$SCENARIO" "$RUN" >> "$CSV"
            sleep 0.1
            RUN=$((RUN+1))
        done
    done
    
    stop_load
    echo "    ✓ Completed ${L} rps"
done

echo "✓ Scenario 1 complete"
echo

# Scenario 2: Rollback Latency vs Load
echo "=== Scenario 2: Rollback Latency vs Load ==="
SCENARIO="S2_rollback_vs_load"
RUN=1

for L in "${LOADS[@]}"; do
    echo "  Testing load: ${L} rps"
    run_load "$L"
    
    for ((r=1; r<=REPEATS; r++)); do
        # Apply a patch, then rollback
        run_apply "v5" "$L" "${SCENARIO}_setup" "$RUN" >> "$CSV"
        run_rollback "$L" "$SCENARIO" "$RUN" "v5_to_v0" >> "$CSV"
        RUN=$((RUN+1))
    done
    
    stop_load
    echo "    ✓ Completed ${L} rps"
done

echo "✓ Scenario 2 complete"
echo

# Scenario 3: Sequential Patches (Patch Stack Depth)
echo "=== Scenario 3: Sequential Patch Stack ==="
SCENARIO="S3_sequential"
L=400  # Representative load
RUN=1

run_load "$L"
sleep 2

echo "  Applying patches sequentially..."
for V in "${VERSIONS[@]}"; do
    run_apply "$V" "$L" "${SCENARIO}_apply" "$RUN" >> "$CSV"
    RUN=$((RUN+1))
    sleep 0.2
done

echo "  Rolling back sequentially..."
for ((i=1; i<=${#VERSIONS[@]}; i++)); do
    run_rollback "$L" "${SCENARIO}_rollback" "$RUN" "step_$i" >> "$CSV"
    RUN=$((RUN+1))
    sleep 0.2
done

stop_load
echo "✓ Scenario 3 complete"
echo

# Scenario 4: Patch Complexity Analysis (different rule versions)
echo "=== Scenario 4: Patch Complexity Impact ==="
SCENARIO="S4_complexity"
L=400
RUN=1

run_load "$L"

# Test each version multiple times to see variation
for V in "${VERSIONS[@]}"; do
    echo "  Testing version: $V"
    for ((r=1; r<=10; r++)); do  # More repeats for complexity analysis
        run_apply "$V" "$L" "$SCENARIO" "$RUN" >> "$CSV"
        run_rollback "$L" "${SCENARIO}_rollback" "$RUN" "$V" >> "$CSV"
        RUN=$((RUN+1))
        sleep 0.1
    done
done

stop_load
echo "✓ Scenario 4 complete"
echo

# Scenario 5: Sustained Load Pattern
echo "=== Scenario 5: Sustained Load Pattern ==="
SCENARIO="S5_sustained"
L=400
RUN=1

run_load "$L"
echo "  Running sustained load test (60 operations)..."

for ((i=1; i<=60; i++)); do
    V=${VERSIONS[$((i % ${#VERSIONS[@]}))]}
    run_apply "$V" "$L" "$SCENARIO" "$RUN" >> "$CSV"
    RUN=$((RUN+1))
    sleep 0.5
    
    if ((i % 10 == 0)); then
        echo "    Completed $i/60 operations"
    fi
done

stop_load
echo "✓ Scenario 5 complete"
echo


# Scenario 6: Simple vs Heavy Patch (APPLY-ONLY, no rollbacks)
echo "=== Scenario 6: Simple vs Heavy Patch (apply-only) ==="
SCENARIO="S6_simple_vs_heavy_apply_only"
RUN=1

V_SIMPLE="v1"     # pick any “simple” one you like (v1..v10)
V_HEAVY="v11"     # the heavy class above

for L in "${LOADS[@]}"; do
    echo "  Testing load: ${L} rps"
    run_load "$L"

    # tiny warmup (optional)
    for ((w=1; w<=1; w++)); do
        run_apply "$V_SIMPLE" "$L" "${SCENARIO}_warmup" "$RUN" >> "$CSV"; RUN=$((RUN+1))
        run_apply "$V_HEAVY"  "$L" "${SCENARIO}_warmup" "$RUN" >> "$CSV"; RUN=$((RUN+1))
    done

    echo "    Measurement runs..."
    for ((r=1; r<=REPEATS; r++)); do
        # Apply simple over whatever is currently active
        run_apply "$V_SIMPLE" "$L" "$SCENARIO" "$RUN" >> "$CSV"; RUN=$((RUN+1)); sleep 0.1
        # Apply heavy over whatever is currently active
        run_apply "$V_HEAVY"  "$L" "$SCENARIO" "$RUN" >> "$CSV"; RUN=$((RUN+1)); sleep 0.1
    done

    stop_load
    echo "    ✓ Completed ${L} rps"
done

echo "✓ Scenario 6 complete"
echo


# Cleanup
echo "Cleaning up..."
stop_load
kill $SERVICE_PID 2>/dev/null || true
wait $SERVICE_PID 2>/dev/null || true

echo "=== Benchmark Complete ==="
echo "Completed: $(date)"
echo "Results saved to: $CSV"

# Generate plots
echo "Generating visualizations..."
if command -v python3 >/dev/null 2>&1; then
    python generate-plots.py
    python generate-dashboard.py
    echo "✓ Plots and dashboard generated"
    echo "  View results: results/dashboard.html"
else
    echo "Python3 not found - skipping visualization"
    echo "  Install Python3 and run: python3 generate-plots.py"
fi

echo
echo "All done!"