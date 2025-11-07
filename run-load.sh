#!/bin/bash

# Run the load generator

echo "=== Starting Load Generator ==="
echo

# Default: 5 threads, 10 RPS
THREADS=${1:-5}
RPS=${2:-10}

java -cp target/classes com.hotpatch.demo.LoadGenerator $THREADS $RPS