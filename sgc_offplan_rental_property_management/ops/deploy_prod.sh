#!/usr/bin/env bash
#
# deploy_prod.sh
# --------------
# Upgrade the module in place on the LIVE demo stack (container
# demo_presentation), then restart it. Same pattern as deploy_staging.sh but
# aimed at production, so it REFUSES to run without an explicit --confirm flag.
#
# !! This touches the live client demo. Only run it deliberately, ideally right
# !! after backup_before_upgrade.sh prod and after the change has passed on
# !! staging + ops/run_tests.sh.
#
# Usage: ops/deploy_prod.sh --confirm [--no-restart]
#   --confirm      REQUIRED. Acknowledges that this mutates the live demo.
#   --no-restart   Run the upgrade but skip the final container restart.

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

CONFIRM=0
RESTART=1
for arg in "$@"; do
  case "$arg" in
    --confirm)    CONFIRM=1 ;;
    --no-restart) RESTART=0 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "unknown argument: $arg (see --help)" ;;
  esac
done

if [[ "${CONFIRM}" -ne 1 ]]; then
  cat >&2 <<MSG
REFUSING TO RUN: deploy_prod.sh mutates the LIVE demo (container ${PROD_ODOO_CONTAINER}).
This will upgrade module '${MODULE}' on the live DB '${DB_NAME}' and restart the
live web process.

Re-run with --confirm once you have:
  1. run ops/backup_before_upgrade.sh prod
  2. verified the change on staging
  3. passed ops/run_tests.sh

  ops/deploy_prod.sh --confirm
MSG
  exit 2
fi

cat >&2 <<MSG
WARNING: proceeding to upgrade the LIVE demo (${PROD_ODOO_CONTAINER}).
MSG

docker inspect "${PROD_ODOO_CONTAINER}" >/dev/null 2>&1 \
  || die "live container '${PROD_ODOO_CONTAINER}' not found."

# deploy_prod.sh is the ONLY script permitted to touch the live containers.
export ALLOW_LIVE=1

log "Upgrading module '${MODULE}' on LIVE DB '${DB_NAME}'..."
docker exec "${PROD_ODOO_CONTAINER}" \
  odoo \
    --db_host=db --db_user="${DB_USER}" --db_password="${DB_PASSWORD}" \
    --addons-path="${ODOO_ADDONS_PATH}" \
    --db-filter="^${DB_NAME}\$" \
    --log-level=info \
    -d "${DB_NAME}" \
    -u "${MODULE}" \
    --stop-after-init

if [[ "${RESTART}" -eq 1 ]]; then
  log "Restarting LIVE web process..."
  docker restart "${PROD_ODOO_CONTAINER}" >/dev/null
  if wait_for_http 18030; then
    log "Live back up: http://localhost:18030/web/login"
  else
    log "WARNING: live HTTP not responding after restart. Check: docker logs ${PROD_ODOO_CONTAINER}"
  fi
fi

log "deploy_prod.sh done."
