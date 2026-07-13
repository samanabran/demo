#!/usr/bin/env bash
#
# deploy_staging.sh
# -----------------
# Apply whatever is currently on the `develop` branch to the staging stack by
# upgrading the module in place, then restarting the staging web process.
# Idempotent and safe to re-run.
#
# Mirrors the live upgrade pattern from the old /tmp/recover_demo_presentation.sh:
#   odoo -d <db> -u <module> --stop-after-init  then  docker restart <container>
#
# Usage: ops/deploy_staging.sh [--no-restart]
#   --no-restart   Run the upgrade but skip the final container restart.

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

RESTART=1
for arg in "$@"; do
  case "$arg" in
    --no-restart) RESTART=0 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "unknown argument: $arg (see --help)" ;;
  esac
done

docker inspect "${STAGING_ODOO_CONTAINER}" >/dev/null 2>&1 \
  || die "staging container '${STAGING_ODOO_CONTAINER}' not found; run clone_staging.sh first."

# Make sure the worktree reflects the tip of develop before upgrading.
WORKTREE_PATH="${STAGING_ADDONS_DIR}/${MODULE}"
if [[ -d "${WORKTREE_PATH}/.git" || -f "${WORKTREE_PATH}/.git" ]]; then
  log "Syncing staging worktree to tip of 'develop'..."
  git -C "${WORKTREE_PATH}" checkout develop
  git -C "${WORKTREE_PATH}" reset --hard develop
fi

assert_not_live "${STAGING_ODOO_CONTAINER}"
log "Upgrading module '${MODULE}' on staging DB '${DB_NAME}'..."
docker exec "${STAGING_ODOO_CONTAINER}" \
  odoo \
    --db_host=db --db_user="${DB_USER}" --db_password="${DB_PASSWORD}" \
    --addons-path="${ODOO_ADDONS_PATH}" \
    --db-filter="^${DB_NAME}\$" \
    --log-level=info \
    -d "${DB_NAME}" \
    -u "${MODULE}" \
    --stop-after-init

if [[ "${RESTART}" -eq 1 ]]; then
  log "Restarting staging web process..."
  docker restart "${STAGING_ODOO_CONTAINER}" >/dev/null
  if wait_for_http 18040; then
    log "Staging back up: http://localhost:18040/web/login"
  else
    log "WARNING: staging HTTP not responding after restart. Check: docker logs ${STAGING_ODOO_CONTAINER}"
  fi
fi

log "deploy_staging.sh done."
