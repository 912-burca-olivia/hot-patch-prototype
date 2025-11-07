#!/bin/bash
# Apply hot patch and measure latency – HTTP control, Windows-safe
# (Prints and flow preserved exactly as your previous script)

set -euo pipefail

echo "=== Hot Patch Application Script ==="
echo

# Classpath separator differs on Windows 
CP_SEP=":"
case "$OS" in
  Windows_NT) CP_SEP=";";;
esac

# Locate the service PID (kept only to verify the service is running & preserve prints)
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
echo "=== Before Patching ==="
curl -s http://localhost:8080/api/verify || true
echo
echo

# Latency start
START_NS=$(date +%s%N 2>/dev/null || python - <<'PY'
import time; print(int(time.time()*1e9))
PY
)

# Build classpath: compiled classes + (optional) agent jar
AGENT_JAR="target/hotpatch-agent.jar"
CLASSES_DIR="target/classes"
PATCHED_CLASS="target/classes-patched/com/hotpatch/demo/BusinessRules.class"

if [ ! -f "$AGENT_JAR" ] || [ ! -d "$CLASSES_DIR" ] || [ ! -f "$PATCHED_CLASS" ]; then
  echo "Build artifacts missing. Run: ./build.sh"
  exit 1
fi

CP="${CLASSES_DIR}${CP_SEP}${AGENT_JAR}"

echo "=== Applying Hot Patch ==="
# HTTP-based PatchApplier: posts bytes to the agent's local HTTP endpoint (no PID, no --add-modules)
java -cp "$CP" com.hotpatch.tool.PatchApplier "$PATCHED_CLASS"

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
echo "=== Patch Applied ==="
echo "Total Latency: ${LATENCY_MS} ms"
echo

sleep 1

echo "=== After Patching ==="
curl -s http://localhost:8080/api/verify || true
echo
echo

echo "=== Verification ==="
echo "Amount: \$50 (should be 5% in v2, was 0% in v1)";  curl -s "http://localhost:8080/api/discount?amount=50";  echo; echo
echo "Amount: \$150 (should be 10% in both)";            curl -s "http://localhost:8080/api/discount?amount=150"; echo; echo
echo "Amount: \$300 (should be 15% in v2, was 10% in v1)";curl -s "http://localhost:8080/api/discount?amount=300"; echo; echo
echo "Amount: \$600 (should be 25% in v2, was 10% in v1)";curl -s "http://localhost:8080/api/discount?amount=600"; echo; echo

echo "✓ Hot patch completed successfully!"
