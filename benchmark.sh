#!/bin/bash
# benchmark.sh: full experiment runner
set -euo pipefail

RESULTS_DIR="results"
CSV="$RESULTS_DIR/latency.csv"
mkdir -p "$RESULTS_DIR"

# header
echo "timestamp,scenario,run_id,load_rps,op,version,orchestration_ms,client_ms,agent_ms" > "$CSV"

# Loads to test; adjust to your box
LOADS=(0 100 250 500)
# Patch versions to apply (must exist in target/classes-patched/)
VERSIONS=(v1 v2 v3 v4 v5 v6 v7 v8 v9 v10)

# Ensure build
SKIP_AGENT_JAR=1 ./build.sh

run_load () {
  local rps="$1"
  if [ "$rps" -eq 0 ]; then
    LOAD_PID=""
    return
  fi
  ./run-load.sh "$rps" >/dev/null 2>&1 &
  LOAD_PID=$!
}

stop_load () {
  if [ -n "${LOAD_PID:-}" ] && kill -0 "$LOAD_PID" 2>/dev/null; then
    kill "$LOAD_PID" || true
    wait "$LOAD_PID" 2>/dev/null || true
  fi
  LOAD_PID=""
}

# S1: Patch latency vs load (with immediate rollback S2)
RUN=1
for L in "${LOADS[@]}"; do
  echo "== Load: ${L} rps =="
  run_load "$L"
  sleep 1

  # Cold run warm-up
  ./bench-apply.sh "${VERSIONS[0]}" "$L" "S1" "$RUN" >> "$CSV"
  ./bench-rollback.sh "$L" "S2" "$RUN" "to_v1" >> "$CSV"
  sleep 0.3

  # Main runs
  for V in "${VERSIONS[@]}"; do
    ./bench-apply.sh "$V" "$L" "S1" "$RUN" >> "$CSV"
    ./bench-rollback.sh "$L" "S2" "$RUN" "to_prev" >> "$CSV"
    sleep 0.2
    RUN=$((RUN+1))
  done

  stop_load
done

# S3: Multi-step stack & sequential rollbacks at a single representative load (choose median)
L=${LOADS[1]:-100}
run_load "$L"; sleep 1
RUN=1
# apply 5 in a row
for V in v1 v2 v3 v4 v5; do
  ./bench-apply.sh "$V" "$L" "S3-apply" "$RUN" >> "$CSV"
  RUN=$((RUN+1))
done
# then rollback 5 in a row
for i in {1..5}; do
  ./bench-rollback.sh "$L" "S3-rollback" "$RUN" "step" >> "$CSV"
  RUN=$((RUN+1))
done
stop_load

echo "Done. Results at $CSV"
