#!/usr/bin/env bash

# This script must be edited to execute, in sequence,
# all required tests from the available workloads.

set -euo pipefail

set -a
. .env
set +a

mkdir -p logs
mkdir logs/astra_dapi_thin_write1_${RUN_TAG}

./nb5 \
  data-api-nb-test/workload_thin.yaml \
  astra_dapi_thin_write1 \
  astraToken=$ASTRA_DB_APPLICATION_TOKEN \
  astraApiEndpoint=$ASTRA_DB_API_ENDPOINT \
  namespace=$ASTRA_DB_KEYSPACE \
  cyclerate=30 rampup-cycles=500 rampup-threads=5 main-cycles=2000 main-threads=10 \
  --progress console:5s \
  --logs-dir logs/astra_dapi_thin_write1_${RUN_TAG}

touch TESTS_FINISHED
