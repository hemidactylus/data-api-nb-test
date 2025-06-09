#!/usr/bin/env bash

# This script must be edited to execute, in sequence,
# all required tests from the available workloads.

set -euo pipefail

CYCLERATE="30"
RAMPUP_CYCLES="1000"
RAMPUP_THREADS="5"
MAIN_CYCLES="5000"
MAIN_THREADS="10"

set -a
. .env
set +a

rm -f TESTS_FINISHED

mkdir -p logs

# Thin, nonvector:

mkdir logs/workload_thin_nonvector_${RUN_TAG}

./nb5 \
  data-api-nb-test/workload_thin_nonvector.yaml \
  astra_dapi_thin_nonvector \
  astraToken=$ASTRA_DB_APPLICATION_TOKEN \
  astraApiEndpoint=$ASTRA_DB_API_ENDPOINT \
  namespace=$ASTRA_DB_KEYSPACE \
  cyclerate=$CYCLERATE \
  rampup-cycles=$RAMPUP_CYCLES \
  rampup-threads=$RAMPUP_THREADS \
  main-cycles=$MAIN_CYCLES \
  main-threads=$MAIN_THREADS \
  --progress console:5s \
  --logs-dir logs/workload_thin_nonvector_${RUN_TAG}

# Thick, vector:

mkdir logs/workload_thick_vector_${RUN_TAG}

./nb5 \
  data-api-nb-test/workload_thick_vector.yaml \
  astra_dapi_thick_vector \
  astraToken=$ASTRA_DB_APPLICATION_TOKEN \
  astraApiEndpoint=$ASTRA_DB_API_ENDPOINT \
  namespace=$ASTRA_DB_KEYSPACE \
  cyclerate=$CYCLERATE \
  rampup-cycles=$RAMPUP_CYCLES \
  rampup-threads=$RAMPUP_THREADS \
  main-cycles=$MAIN_CYCLES \
  main-threads=$MAIN_THREADS \
  --progress console:5s \
  --logs-dir logs/workload_thick_vector_${RUN_TAG}

touch TESTS_FINISHED
