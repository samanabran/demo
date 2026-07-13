#!/usr/bin/env bash
#
# run_tests.sh
# ------------
# CI gate. Installs the module into a THROWAWAY scratch database with Odoo's
# test runner enabled and fails (non-zero exit) if the run logs any ERROR or
# traceback. This is the gate future phases must pass before merging.
#
# Design choice — where the scratch DB lives:
#   We reuse the STAGING postgres server (container demo_presentation_staging_db)
#   with a distinct throwaway DB name (${SCRATCH_DB}), and run Odoo itself in a
#   one-off `docker run --rm odoo:19.0` container attached to the staging network.
#   Rationale: it needs no new long-lived infrastructure, never touches the live
#   stack, and the odoo:19.0 image + staging addons are already on disk. The
#   scratch DB is dropped at the end (and on entry), so runs are repeatable.
#   The one dependency is that the staging DB container is up; we start it
#   (idempotently) if it isn't.
#
# Usage: ops/run_tests.sh
#   (no arguments)

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

SCRATCH_DB="sgc_ci_scratch"
LOG_FILE="$(mktemp "${TMPDIR:-/tmp}/sgc_run_tests.XXXXXX.log")"

cleanup() {
  # Best-effort: drop the scratch DB so the next run starts clean.
  docker exec "${STAGING_DB_CONTAINER}" dropdb -U "${DB_USER}" --if-exists "${SCRATCH_DB}" >/dev/null 2>&1 || true
  rm -f "${LOG_FILE}"
}
trap cleanup EXIT

# --- Ensure the staging DB server is available (does NOT touch live) ---------
if ! docker inspect "${STAGING_DB_CONTAINER}" >/dev/null 2>&1; then
  [[ -f "${STAGING_COMPOSE}" ]] || die "staging not initialised; run ops/clone_staging.sh first."
  log "Staging DB container missing; starting it..."
  assert_not_live "${STAGING_DB_CONTAINER}"
  ${DC} -f "${STAGING_COMPOSE}" -p "${STAGING_PROJECT}" up -d db
fi
wait_for_db "${STAGING_DB_CONTAINER}"

# --- Fresh scratch DB --------------------------------------------------------
log "(Re)creating scratch DB '${SCRATCH_DB}'..."
docker exec "${STAGING_DB_CONTAINER}" dropdb -U "${DB_USER}" --if-exists "${SCRATCH_DB}"
docker exec "${STAGING_DB_CONTAINER}" createdb -U "${DB_USER}" "${SCRATCH_DB}"

# --- Run the tests in a one-off Odoo container -------------------------------
log "Installing '${MODULE}' with tests enabled into '${SCRATCH_DB}'..."
set +e
docker run --rm \
  --network "${STAGING_NETWORK}" \
  -v "${STAGING_ADDONS_DIR}:/mnt/extra-addons:ro" \
  odoo:19.0 \
  odoo \
    --db_host=db --db_user="${DB_USER}" --db_password="${DB_PASSWORD}" \
    --addons-path="${ODOO_ADDONS_PATH}" \
    --db-filter="^${SCRATCH_DB}\$" \
    --log-level=test \
    --no-http \
    -d "${SCRATCH_DB}" \
    -i "${MODULE}" \
    --test-enable \
    --stop-after-init \
  2>&1 | tee "${LOG_FILE}"
ODOO_RC="${PIPESTATUS[0]}"
set -e

# --- Evaluate the result -----------------------------------------------------
FAIL=0
if [[ "${ODOO_RC}" -ne 0 ]]; then
  log "FAIL: odoo exited non-zero (${ODOO_RC})."
  FAIL=1
fi
# Odoo logs failed assertions / test errors at ERROR/CRITICAL level and prints
# Python tracebacks. Any of these means the gate should fail.
if grep -Eq '\b(ERROR|CRITICAL)\b' "${LOG_FILE}"; then
  log "FAIL: log contains ERROR/CRITICAL lines:"
  grep -En '\b(ERROR|CRITICAL)\b' "${LOG_FILE}" | head -20 >&2
  FAIL=1
fi
if grep -q 'Traceback (most recent call last)' "${LOG_FILE}"; then
  log "FAIL: log contains a Python traceback."
  FAIL=1
fi

if [[ "${FAIL}" -ne 0 ]]; then
  log "run_tests.sh: TESTS FAILED"
  exit 1
fi

log "run_tests.sh: TESTS PASSED"
exit 0
