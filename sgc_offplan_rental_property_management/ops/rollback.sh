#!/usr/bin/env bash
#
# rollback.sh
# -----------
# Restore the most recent backup for a target (created by
# backup_before_upgrade.sh) and restart that target's Odoo container.
#
# For target 'prod' this touches the LIVE demo, so it requires --confirm.
#
# Usage: ops/rollback.sh <staging|prod> [--confirm] [--file <path>]
#   --confirm      REQUIRED for prod. Acknowledges mutating the live demo.
#   --file <path>  Restore a specific dump instead of the most recent one.

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

TARGET="${1:-}"; shift || true
FILE=""
CONFIRM=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --confirm) CONFIRM=1 ;;
    --file) FILE="${2:-}"; shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "unknown argument: $1 (see --help)" ;;
  esac
  shift
done

case "${TARGET}" in
  staging)
    DB_CONTAINER="${STAGING_DB_CONTAINER}"
    ODOO_CONTAINER="${STAGING_ODOO_CONTAINER}"
    HTTP_PORT=18040
    ;;
  prod)
    DB_CONTAINER="${PROD_DB_CONTAINER}"
    ODOO_CONTAINER="${PROD_ODOO_CONTAINER}"
    HTTP_PORT=18030
    if [[ "${CONFIRM}" -ne 1 ]]; then
      die "rollback prod mutates the LIVE demo; re-run with --confirm"
    fi
    export ALLOW_LIVE=1
    ;;
  *) die "usage: $0 <staging|prod> [--confirm] [--file <path>]" ;;
esac

# Pick the backup file.
if [[ -z "${FILE}" ]]; then
  FILE="$(ls -1t "${BACKUP_DIR}/${TARGET}_${DB_NAME}_"*.dump 2>/dev/null | head -n1 || true)"
  [[ -n "${FILE}" ]] || die "no backups found for '${TARGET}' in ${BACKUP_DIR} (run backup_before_upgrade.sh first)"
fi
[[ -f "${FILE}" ]] || die "backup file not found: ${FILE}"

docker inspect "${DB_CONTAINER}" >/dev/null 2>&1 || die "DB container '${DB_CONTAINER}' not found."

log "Rolling back ${TARGET} DB '${DB_NAME}' from: ${FILE}"
assert_not_live "${DB_CONTAINER}"

# Terminate open connections, drop, recreate, restore. Odoo will reconnect on
# restart below.
log "Dropping and recreating '${DB_NAME}'..."
docker exec "${DB_CONTAINER}" psql -U "${DB_USER}" -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}' AND pid<>pg_backend_pid();" >/dev/null
docker exec "${DB_CONTAINER}" dropdb -U "${DB_USER}" --if-exists "${DB_NAME}"
docker exec "${DB_CONTAINER}" createdb -U "${DB_USER}" "${DB_NAME}"

log "Restoring snapshot..."
docker exec -i "${DB_CONTAINER}" \
  pg_restore -U "${DB_USER}" -d "${DB_NAME}" --no-owner < "${FILE}"

log "Restarting ${TARGET} web process (${ODOO_CONTAINER})..."
assert_not_live "${ODOO_CONTAINER}"
docker restart "${ODOO_CONTAINER}" >/dev/null

if wait_for_http "${HTTP_PORT}"; then
  log "${TARGET} back up after rollback: http://localhost:${HTTP_PORT}/web/login"
else
  log "WARNING: ${TARGET} HTTP not responding after rollback. Check: docker logs ${ODOO_CONTAINER}"
fi

log "rollback.sh done."
