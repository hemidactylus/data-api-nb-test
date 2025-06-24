#!/usr/bin/env bash

# This script must be edited to execute, in sequence,
# all required tests from the available workloads.

set -euo pipefail

# workload sizing and parameters
CYCLERATE=${CYCLERATE:-"30"}
RAMPUP_CYCLES=${RAMPUP_CYCLES:-"500"}
RAMPUP_THREADS=${RAMPUP_THREADS:-"3"}
MAIN_CYCLES=${MAIN_CYCLES:-"1000"}
MAIN_THREADS=${MAIN_THREADS:-"8"}

# environmental settings
NB5_EXECUTABLE=${NB5_EXECUTABLE:-"./nb5"}
DOTENV_PATH=${DOTENV_PATH:-".env"}
LOG_ROOT_DIR=${LOG_ROOT_DIR:-"logs"}
REPO_ROOT_DIR=${REPO_ROOT_DIR:-"data-api-nb-test"}

set -a
. "${DOTENV_PATH}"
set +a

rm -f TESTS_FINISHED

echo "Environmental settings:"
echo "NB5_EXECUTABLE=${NB5_EXECUTABLE}"
echo "DOTENV_PATH=${DOTENV_PATH}"
echo "LOG_ROOT_DIR=${LOG_ROOT_DIR}"
echo "REPO_ROOT_DIR=${REPO_ROOT_DIR}"

mkdir -p "${LOG_ROOT_DIR}"

# Thin, nonvector:

mkdir -p "${LOG_ROOT_DIR}/${RUN_TAG}_LOG_wl_coll_thin_nonvector"
mkdir -p "${LOG_ROOT_DIR}/${RUN_TAG}_CSV_wl_coll_thin_nonvector"

cat <<EOF > "${LOG_ROOT_DIR}/${RUN_TAG}_CSV_wl_coll_thin_nonvector/metaparameters.log"
# Meta-parameters for this run
CYCLERATE=$CYCLERATE
RAMPUP_CYCLES=$RAMPUP_CYCLES
RAMPUP_THREADS=$RAMPUP_THREADS
MAIN_CYCLES=$MAIN_CYCLES
MAIN_THREADS=$MAIN_THREADS
REPO_COMMIT_SHA=$REPO_COMMIT_SHA
TARGET_API_ENDPOINT=$ASTRA_DB_API_ENDPOINT
EOF

echo -e "\n\nSTARTING WORKLOAD wl_coll_thin_nonvector\n"

${NB5_EXECUTABLE} \
  "${REPO_ROOT_DIR}/wl_coll_thin_nonvector.yaml" \
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
  --logs-dir "${LOG_ROOT_DIR}/${RUN_TAG}_LOG_wl_coll_thin_nonvector" \
  --report-csv-to "${LOG_ROOT_DIR}/${RUN_TAG}_CSV_wl_coll_thin_nonvector" \
  --report-interval 60

# Thick, vector:

mkdir -p "${LOG_ROOT_DIR}/${RUN_TAG}_LOG_wl_coll_thick_vector"
mkdir -p "${LOG_ROOT_DIR}/${RUN_TAG}_CSV_wl_coll_thick_vector"

cat <<EOF > "${LOG_ROOT_DIR}/${RUN_TAG}_CSV_wl_coll_thick_vector/metaparameters.log"
# Meta-parameters for this run
CYCLERATE=$CYCLERATE
RAMPUP_CYCLES=$RAMPUP_CYCLES
RAMPUP_THREADS=$RAMPUP_THREADS
MAIN_CYCLES=$MAIN_CYCLES
MAIN_THREADS=$MAIN_THREADS
REPO_COMMIT_SHA=$REPO_COMMIT_SHA
TARGET_API_ENDPOINT=$ASTRA_DB_API_ENDPOINT
EOF

echo -e "\n\nSTARTING WORKLOAD wl_coll_thick_vector\n"

${NB5_EXECUTABLE} \
  "${REPO_ROOT_DIR}/wl_coll_thick_vector.yaml" \
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
  --logs-dir "${LOG_ROOT_DIR}/${RUN_TAG}_LOG_wl_coll_thick_vector" \
  --report-csv-to "${LOG_ROOT_DIR}/${RUN_TAG}_CSV_wl_coll_thick_vector" \
  --report-interval 60

touch TESTS_FINISHED
