#!/bin/bash
# bench-apply.sh: apply one patch version and print a CSV row
set -euo pipefail

VER="${1:?Usage: bench-apply.sh <vN> <load_rps> <scenario> <run_id>}"
LOAD="${2:?}"
SCEN="${3:?}"
RUNID="${4:?}"

CLASSES_DIR="target/classes"
AGENT_JAR="target/hotpatch-agent.jar"
PATCHED_CLASS="target/classes-patched/${VER}/com/hotpatch/demo/BusinessRules.class"

CP_SEP=":"; case "$OSTYPE" in msys*|cygwin*|win32*) CP_SEP=";";; esac
CP="${CLASSES_DIR}${CP_SEP}${AGENT_JAR}"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

# Orchestration wall clock
START_NS=$(date +%s%N 2>/dev/null || python - <<'PY'
import time; print(int(time.time()*1e9))
PY
)

OUT=$(java -cp "$CP" com.hotpatch.tool.PatchApplier "$PATCHED_CLASS")

END_NS=$(date +%s%N 2>/dev/null || python - <<'PY'
import time; print(int(time.time()*1e9))
PY
)
ORCH_MS=$(awk -v n="$((END_NS-START_NS))" 'BEGIN{printf("%.3f", n/1e6)}')

# Parse metrics
CLIENT_MS=""
AGENT_MS=""

# 1) Prefer METRIC line if present
METRIC=$(echo "$OUT" | awk '/^METRIC /{print}')
if [ -n "$METRIC" ]; then
  CLIENT_MS=$(echo "$METRIC" | sed -nE 's/.*client_ms=([0-9.]+).*/\1/p')
  AGENT_MS=$(echo "$METRIC" | sed -nE 's/.*agent_ms=([0-9.]+).*/\1/p')
fi

# 2) Fallback: robust regex from human-friendly lines
if [ -z "$CLIENT_MS" ]; then
  CLIENT_MS=$(echo "$OUT" | sed -nE 's/.*Request→response latency: *([0-9.]+) *ms.*/\1/p')
fi
if [ -z "$AGENT_MS" ]; then
  # Matches: "HTTP 200 from agent: OK 12.345 ms" (and "(rollback)")
  AGENT_MS=$(echo "$OUT" | sed -nE 's/.*OK *([0-9.]+) *ms.*/\1/p')
fi

# Last resort: set to NaN strings so CSV remains parseable
: "${CLIENT_MS:=NaN}"
: "${AGENT_MS:=NaN}"

echo "$(ts),$SCEN,$RUNID,$LOAD,patch,$VER,$ORCH_MS,$CLIENT_MS,$AGENT_MS"
