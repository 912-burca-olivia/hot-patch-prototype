#!/bin/bash

# Run the business service with agent pre-loaded

echo "=== Starting Business Rule Service ==="
echo

# Check if already running
if jps | grep -q BusinessRuleService; then
    echo "Warning: BusinessRuleService is already running"
    echo "Kill it with: pkill -f BusinessRuleService"
    exit 1
fi

# Run with agent loaded (allows hot patching)
java -javaagent:target/hotpatch-agent.jar \
     -cp target/classes \
     com.hotpatch.demo.BusinessRuleService