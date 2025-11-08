#!/bin/bash
# bench-apply.sh: apply one patch and record metrics
set -euo pipefail

VER="${1:?Usage: bench-apply.sh <vN> <load_rps> <scenario> <run_id>}"
LOAD="${2:?}"
SCEN="${3:?}"
RUNID="${4:?}"

CLASSES_DIR="target/classes"
AGENT_JAR="target/hotpatch-agent.jar"
PATCHED_CLASS="target/classes-patched/${VER}/com/hotpatch/demo/BusinessRules.class"

# Classpath separator
CP_SEP=":"; case "$OSTYPE" in msys*|cygwin*|win32*) CP_SEP=";";; esac
CP="${CLASSES_DIR}${CP_SEP}${AGENT_JAR}"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

# Check if patch file exists
if [ ! -f "$PATCHED_CLASS" ]; then
    echo "$(ts),$SCEN,$RUNID,$LOAD,patch,$VER,NaN,NaN,NaN,false"
    exit 1
fi

# Orchestration wall clock (includes all overhead)
START_NS=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time()*1e9))")

# Execute patch
OUT=$(java -cp "$CP" com.hotpatch.tool.PatchApplier "$PATCHED_CLASS" 2>&1) || {
    echo "$(ts),$SCEN,$RUNID,$LOAD,patch,$VER,NaN,NaN,NaN,false"
    exit 1
}

END_NS=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time()*1e9))")
ORCH_MS=$(awk -v n="$((END_NS-START_NS))" 'BEGIN{printf("%.3f", n/1e6)}')

# Parse metrics (prefer METRIC line, fallback to human-readable)
CLIENT_MS=""
AGENT_MS=""
SUCCESS="true"

METRIC=$(echo "$OUT" | grep '^METRIC ' || true)
if [ -n "$METRIC" ]; then
    CLIENT_MS=$(echo "$METRIC" | sed -nE 's/.*client_ms=([0-9.]+).*/\1/p')
    AGENT_MS=$(echo "$METRIC" | sed -nE 's/.*agent_ms=([0-9.]+).*/\1/p')
fi

# Fallback parsing
if [ -z "$CLIENT_MS" ]; then
    CLIENT_MS=$(echo "$OUT" | sed -nE 's/.*Request.*response latency: *([0-9.]+) *ms.*/\1/p' | head -1)
fi
if [ -z "$AGENT_MS" ]; then
    AGENT_MS=$(echo "$OUT" | sed -nE 's/.*OK *([0-9.]+) *ms.*/\1/p' | head -1)
fi

# Check for success
if echo "$OUT" | grep -qi "error\|failed\|exception"; then
    SUCCESS="false"
fi

# Default to NaN if parsing failed
: "${CLIENT_MS:=NaN}"
: "${AGENT_MS:=NaN}"

# Output CSV row
echo "$(ts),$SCEN,$RUNID,$LOAD,patch,$VER,$ORCH_MS,$CLIENT_MS,$AGENT_MS,$SUCCESS"