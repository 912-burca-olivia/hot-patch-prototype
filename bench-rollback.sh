#!/bin/bash
# bench-rollback.sh: rollback and print a CSV row
set -euo pipefail

LOAD="${1:?Usage: bench-rollback.sh <load_rps> <scenario> <run_id> <version_label>}"
SCEN="${2:?}"
RUNID="${3:?}"
VERLAB="${4:?}"   # e.g., "to_v2"

CLASSES_DIR="target/classes"
AGENT_JAR="target/hotpatch-agent.jar"
CP_SEP=":"; case "$OSTYPE" in msys*|cygwin*|win32*) CP_SEP=";";; esac
CP="${CLASSES_DIR}${CP_SEP}${AGENT_JAR}"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

START_NS=$(date +%s%N 2>/dev/null || python - <<'PY'
import time; print(int(time.time()*1e9))
PY
)

OUT=$(java -cp "$CP" com.hotpatch.tool.RollbackApplier)

END_NS=$(date +%s%N 2>/dev/null || python - <<'PY'
import time; print(int(time.time()*1e9))
PY
)
ORCH_MS=$(awk -v n="$((END_NS-START_NS))" 'BEGIN{printf("%.3f", n/1e6)}')

CLIENT_MS=""; AGENT_MS=""
METRIC=$(echo "$OUT" | awk '/^METRIC /{print}')
if [ -n "$METRIC" ]; then
  CLIENT_MS=$(echo "$METRIC" | sed -nE 's/.*client_ms=([0-9.]+).*/\1/p')
  AGENT_MS=$(echo "$METRIC" | sed -nE 's/.*agent_ms=([0-9.]+).*/\1/p')
fi
if [ -z "$CLIENT_MS" ]; then
  CLIENT_MS=$(echo "$OUT" | sed -nE 's/.*Request→response latency: *([0-9.]+) *ms.*/\1/p')
fi
if [ -z "$AGENT_MS" ]; then
  AGENT_MS=$(echo "$OUT" | sed -nE 's/.*OK *([0-9.]+) *ms.*/\1/p')
fi
: "${CLIENT_MS:=NaN}"
: "${AGENT_MS:=NaN}"

echo "$(ts),$SCEN,$RUNID,$LOAD,rollback,$VERLAB,$ORCH_MS,$CLIENT_MS,$AGENT_MS"
