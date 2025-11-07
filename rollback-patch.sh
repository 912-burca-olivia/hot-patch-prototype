#!/bin/bash
# Roll back the latest hot patch – HTTP control, Windows-safe
# (Style/prints align with apply-patch.sh)

set -euo pipefail

echo "=== Hot Patch Rollback Script ==="
echo

# Classpath separator differs on Windows
CP_SEP=":"
case "$OS" in
  Windows_NT) CP_SEP=";";;
esac

# Verify service is running (keep the same UX as apply script)
if ! command -v jps >/dev/null 2>&1; then
  echo "Error: jps not found. Ensure JDK bin is on PATH."
  exit 1
fi

PID=$(jps | awk '/BusinessRuleService/{print $1}')
if [ -z "${PID:-}" ]; then
  echo "Error: BusinessRuleService is not running"
  echo "Start it with: ./run-service.sh"
  exit 1
fi

echo "Found BusinessRuleService running with PID: $PID"
echo

# Verify before
echo "=== Before Rollback ==="
curl -s http://localhost:8080/api/verify || true
echo
echo

# Latency start
START_NS=$(date +%s%N 2>/dev/null || python - <<'PY'
import time; print(int(time.time()*1e9))
PY
)

# Build classpath (we only need target/classes to run the client)
AGENT_JAR="target/hotpatch-agent.jar"
CLASSES_DIR="target/classes"
if [ ! -f "$AGENT_JAR" ] || [ ! -d "$CLASSES_DIR" ]; then
  echo "Build artifacts missing. Run: ./build.sh"
  exit 1
fi
CP="${CLASSES_DIR}${CP_SEP}${AGENT_JAR}"

echo "=== Applying Rollback ==="
java -cp "$CP" com.hotpatch.tool.RollbackApplier

# Latency end
END_NS=$(date +%s%N 2>/dev/null || python - <<'PY'
import time; print(int(time.time()*1e9))
PY
)
LATENCY_NS=$((END_NS - START_NS))

# Prefer bc if present, otherwise awk
if command -v bc >/dev/null 2>&1; then
  LATENCY_MS=$(echo "scale=3; $LATENCY_NS/1000000" | bc)
else
  LATENCY_MS=$(awk -v n="$LATENCY_NS" 'BEGIN{printf("%.3f", n/1000000)}')
fi

echo
echo "=== Rollback Applied ==="
echo "Total Latency: ${LATENCY_MS} ms"
echo

sleep 1

echo "=== After Rollback ==="
curl -s http://localhost:8080/api/verify || true
echo
echo

echo "=== Verification ==="
echo "Amount: \$50 (v1 was 0%, v2 was 5%)";  curl -s "http://localhost:8080/api/discount?amount=50";  echo; echo
echo "Amount: \$150 (10% in both)";         curl -s "http://localhost:8080/api/discount?amount=150"; echo; echo
echo "Amount: \$300 (v1 was 10%, v2 was 15%)"; curl -s "http://localhost:8080/api/discount?amount=300"; echo; echo
echo "Amount: \$600 (v1 was 10%, v2 was 25%)"; curl -s "http://localhost:8080/api/discount?amount=600"; echo; echo

echo "✓ Hot patch rollback completed successfully!"
