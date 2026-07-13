#!/usr/bin/env bash
#
# backup_before_upgrade.sh
# ------------------------
# pg_dump the target DB to a timestamped custom-format file under ops/backups/.
# Keeps the last ${BACKUP_KEEP} backups per target and prunes older ones.
# Read-only with respect to Odoo; only reads the DB.
#
# Usage: ops/backup_before_upgrade.sh <staging|prod>

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

TARGET="${1:-}"
case "${TARGET}" in
  staging) DB_CONTAINER="${STAGING_DB_CONTAINER}" ;;
  prod)    DB_CONTAINER="${PROD_DB_CONTAINER}" ;;
  -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  *) die "usage: $0 <staging|prod>" ;;
esac

docker inspect "${DB_CONTAINER}" >/dev/null 2>&1 \
  || die "DB container '${DB_CONTAINER}' not found."

mkdir -p "${BACKUP_DIR}"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${BACKUP_DIR}/${TARGET}_${DB_NAME}_${STAMP}.dump"

log "Backing up ${TARGET} DB '${DB_NAME}' from '${DB_CONTAINER}' (read-only)..."
# pg_dump only reads; safe against the live DB.
docker exec "${DB_CONTAINER}" pg_dump -U "${DB_USER}" -Fc "${DB_NAME}" > "${OUT}.tmp"
mv "${OUT}.tmp" "${OUT}"
log "Backup written: ${OUT} ($(du -h "${OUT}" | cut -f1))"

# Prune: keep only the newest ${BACKUP_KEEP} backups for this target.
log "Pruning old ${TARGET} backups (keeping ${BACKUP_KEEP})..."
mapfile -t OLD < <(ls -1t "${BACKUP_DIR}/${TARGET}_${DB_NAME}_"*.dump 2>/dev/null | tail -n +$((BACKUP_KEEP + 1)))
for f in "${OLD[@]:-}"; do
  [[ -n "$f" ]] || continue
  log "  removing $(basename "$f")"
  rm -f "$f"
done

# Emit the path on stdout so rollback.sh / callers can capture it.
echo "${OUT}"
log "backup_before_upgrade.sh done."
