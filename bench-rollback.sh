#!/bin/bash
# bench-rollback.sh: rollback and record metrics
set -euo pipefail

LOAD="${1:?Usage: bench-rollback.sh <load_rps> <scenario> <run_id> <version_label>}"
SCEN="${2:?}"
RUNID="${3:?}"
VERLAB="${4:?}"

CLASSES_DIR="target/classes"
AGENT_JAR="target/hotpatch-agent.jar"
CP_SEP=":"; case "$OSTYPE" in msys*|cygwin*|win32*) CP_SEP=";";; esac
CP="${CLASSES_DIR}${CP_SEP}${AGENT_JAR}"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

# Orchestration wall clock
START_NS=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time()*1e9))")

# Execute rollback
OUT=$(java -cp "$CP" com.hotpatch.tool.RollbackApplier 2>&1) || {
    echo "$(ts),$SCEN,$RUNID,$LOAD,rollback,$VERLAB,NaN,NaN,NaN,false"
    exit 1
}

END_NS=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time()*1e9))")
ORCH_MS=$(awk -v n="$((END_NS-START_NS))" 'BEGIN{printf("%.3f", n/1e6)}')

# Parse metrics
CLIENT_MS=""
AGENT_MS=""
SUCCESS="true"

METRIC=$(echo "$OUT" | grep '^METRIC ' || true)
if [ -n "$METRIC" ]; then
    CLIENT_MS=$(echo "$METRIC" | sed -nE 's/.*client_ms=([0-9.]+).*/\1/p')
    AGENT_MS=$(echo "$METRIC" | sed -nE 's/.*agent_ms=([0-9.]+).*/\1/p')
fi

if [ -z "$CLIENT_MS" ]; then
    CLIENT_MS=$(echo "$OUT" | sed -nE 's/.*Request.*response latency: *([0-9.]+) *ms.*/\1/p' | head -1)
fi
if [ -z "$AGENT_MS" ]; then
    AGENT_MS=$(echo "$OUT" | sed -nE 's/.*OK *([0-9.]+) *ms.*/\1/p' | head -1)
fi

# Check for errors
if echo "$OUT" | grep -qi "error\|failed\|exception\|no previous version"; then
    SUCCESS="false"
fi

: "${CLIENT_MS:=NaN}"
: "${AGENT_MS:=NaN}"

echo "$(ts),$SCEN,$RUNID,$LOAD,rollback,$VERLAB,$ORCH_MS,$CLIENT_MS,$AGENT_MS,$SUCCESS"