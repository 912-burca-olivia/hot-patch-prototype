#!/bin/bash

# Build script for hot patching demo
# Works on Linux, Mac, and Windows (Git Bash/MINGW64)

set -e

echo "=== Building Hot Patch Demo ==="
echo

# Create directory structure
mkdir -p target/classes/com/hotpatch/demo
mkdir -p target/classes/com/hotpatch/agent
mkdir -p target/classes/com/hotpatch/tool
mkdir -p target/classes-patched/com/hotpatch/demo
mkdir -p target/META-INF
mkdir -p target/temp

# Compile original business service
echo "Compiling original business service..."
javac -d target/classes \
    src/main/java/com/hotpatch/demo/BusinessRuleService.java \
    src/main/java/com/hotpatch/demo/BusinessRules.java \
    src/main/java/com/hotpatch/demo/LoadGenerator.java

# Compile all versioned patched rules into versioned output dirs
echo "Compiling versioned patched business rules..."
mkdir -p target/classes-patched
for f in src/main/java/com/hotpatch/demo/BusinessRules-patched-v*.java; do
  [ -f "$f" ] || continue
  ver=$(basename "$f" | sed -E 's/.*-v([0-9]+)\.java/\1/')
  outdir="target/classes-patched/v$ver/com/hotpatch/demo"
  mkdir -p "$outdir"
  # copy & rename to the canonical filename
  tmp="target/temp/com/hotpatch/demo"
  mkdir -p "$tmp"
  cp "$f" "$tmp/BusinessRules.java"
  javac -d "target/classes-patched/v$ver" "$tmp/BusinessRules.java"
  rm -rf target/temp
done

# Compile agent
echo "Compiling hot patch agent..."
javac -d target/classes \
    src/main/java/com/hotpatch/agent/HotPatchAgent.java

# Compile patch applier tool (optional - only if tools.jar is available)
echo "Compiling patch applier tool..."
javac --add-modules jdk.attach \
  -d target/classes \
  src/main/java/com/hotpatch/tool/PatchApplier.java

javac -d target/classes src/main/java/com/hotpatch/tool/RollbackApplier.java


# Create agent manifest
cat > target/META-INF/MANIFEST.MF << EOF
Manifest-Version: 1.0
Premain-Class: com.hotpatch.agent.HotPatchAgent
Agent-Class: com.hotpatch.agent.HotPatchAgent
Can-Redefine-Classes: true
Can-Retransform-Classes: true

EOF

if [ "${SKIP_AGENT_JAR:-0}" = "1" ]; then
  echo "Skipping agent JAR build (SKIP_AGENT_JAR=1)"
else
  echo "Creating agent JAR..."
  jar cfm target/hotpatch-agent.jar target/META-INF/MANIFEST.MF \
      -C target/classes com/hotpatch/agent/
fi

echo
echo "✓ Build complete!"
echo
echo "Generated files:"
echo "  - target/classes/                  (service and original rules)"
echo "  - target/classes-patched/          (patched rules)"
echo "  - target/hotpatch-agent.jar        (Java agent)"
echo
echo "Next steps:"
echo "  1. Start service: ./run-service.sh"
echo "  2. Start load generator: ./run-load.sh"
echo "  3. Apply patch: ./apply-patch.sh"