#!/usr/bin/env bash

# This script must be edited to execute, in sequence,
# all required tests from the available workloads.

set -euo pipefail

CYCLERATE="30"
RAMPUP_CYCLES="500"
RAMPUP_THREADS="3"
MAIN_CYCLES="1000"
MAIN_THREADS="8"

set -a
. .env
set +a

rm -f TESTS_FINISHED

mkdir -p logs

# Thin, nonvector:

mkdir logs/${RUN_TAG}_wl_coll_thin_nonvector

cat <<EOF > logs/${RUN_TAG}_wl_coll_thin_nonvector/metaparameters.log
# Meta-parameters for this run
CYCLERATE=$CYCLERATE
RAMPUP_CYCLES=$RAMPUP_CYCLES
RAMPUP_THREADS=$RAMPUP_THREADS
MAIN_CYCLES=$MAIN_CYCLES
MAIN_THREADS=$MAIN_THREADS
REPO_COMMIT_SHA=$REPO_COMMIT_SHA
EOF

echo -e "\n\nSTARTING WORKLOAD wl_coll_thin_nonvector\n"

./nb5 \
  data-api-nb-test/wl_coll_thin_nonvector.yaml \
  sc_astra_dataapi_coll_thin_nonvector \
  astraToken=$ASTRA_DB_APPLICATION_TOKEN \
  astraApiEndpoint=$ASTRA_DB_API_ENDPOINT \
  namespace=$ASTRA_DB_KEYSPACE \
  cyclerate=$CYCLERATE \
  rampup-cycles=$RAMPUP_CYCLES \
  rampup-threads=$RAMPUP_THREADS \
  main-cycles=$MAIN_CYCLES \
  main-threads=$MAIN_THREADS \
  --progress console:5s \
  --logs-dir logs/${RUN_TAG}_wl_coll_thin_nonvector

# Thick, vector:

mkdir logs/${RUN_TAG}_wl_coll_thick_vector

cat <<EOF > logs/${RUN_TAG}_wl_coll_thick_vector/metaparameters.log
# Meta-parameters for this run
CYCLERATE=$CYCLERATE
RAMPUP_CYCLES=$RAMPUP_CYCLES
RAMPUP_THREADS=$RAMPUP_THREADS
MAIN_CYCLES=$MAIN_CYCLES
MAIN_THREADS=$MAIN_THREADS
REPO_COMMIT_SHA=$REPO_COMMIT_SHA
EOF

echo -e "\n\nSTARTING WORKLOAD wl_coll_thick_vector\n"

./nb5 \
  data-api-nb-test/wl_coll_thick_vector.yaml \
  sc_astra_dataapi_coll_thick_vector \
  astraToken=$ASTRA_DB_APPLICATION_TOKEN \
  astraApiEndpoint=$ASTRA_DB_API_ENDPOINT \
  namespace=$ASTRA_DB_KEYSPACE \
  cyclerate=$CYCLERATE \
  rampup-cycles=$RAMPUP_CYCLES \
  rampup-threads=$RAMPUP_THREADS \
  main-cycles=$MAIN_CYCLES \
  main-threads=$MAIN_THREADS \
  --progress console:5s \
  --logs-dir logs/${RUN_TAG}_wl_coll_thick_vector

touch TESTS_FINISHED
