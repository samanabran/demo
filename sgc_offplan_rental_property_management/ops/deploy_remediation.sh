#!/usr/bin/env bash
#
# deploy_remediation.sh
# ---------------------
# Push the current local branch to the remote Odoo server and upgrade the module.
#
# This script is intended to run from a Linux/macOS client (or WSL on Windows).
# The SSH alias "contabo-sgc" must resolve to the target server in ~/.ssh/config.
#
# Steps:
#   1. Back up the remote module directory (timestamped).
#   2. rsync the local module directory to the remote server.
#   3. Run odoo-bin -u <module> -d <db> --stop-after-init --no-http on the server.
#   4. Report pass/fail.
#
# Usage: ops/deploy_remediation.sh

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

# --- Remote server configuration ----------------------------------------------
REMOTE_HOST="contabo-sgc"
REMOTE_MODULE_PATH="/opt/odoo/demo_presentation/addons/${MODULE}"
REMOTE_DB_NAME="demo_presentation_19"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
SSH_CMD="ssh ${SSH_OPTS}"
RSYNC_CMD="rsync -avz --delete -e 'ssh ${SSH_OPTS}'"

# --- Timestamp for backup -----------------------------------------------------
STAMP="$(date +%Y%m%d%H%M%S)"
BACKUP_REMOTE_PATH="/opt/odoo/backups/${MODULE}.backup.${STAMP}"

log "=== deploy_remediation.sh ==="
log "Target: ${REMOTE_HOST} | Module: ${MODULE} | DB: ${REMOTE_DB_NAME}"

# --- Step 1: Backup remote module directory -----------------------------------
# Backup is placed OUTSIDE the addons path so Odoo does not try to load it
# as a module (names with dots inside addons/ cause FileNotFoundError).
log "Backing up remote module directory to ${BACKUP_REMOTE_PATH}..."
${SSH_CMD} "${REMOTE_HOST}" \
  "mkdir -p /opt/odoo/backups && cp -a ${REMOTE_MODULE_PATH} ${BACKUP_REMOTE_PATH}" \
  || die "Remote backup failed."

log "Remote backup created: ${BACKUP_REMOTE_PATH}"

# --- Step 2: Rsync local module to remote -------------------------------------
log "Syncing local module to remote server..."
${RSYNC_CMD} \
  --exclude='.git/' \
  --exclude='__pycache__/' \
  --exclude='.ruff_cache/' \
  --exclude='*.pyc' \
  "${MODULE_DIR}/" \
  "${REMOTE_HOST}:${REMOTE_MODULE_PATH}/" \
  || die "rsync failed."

log "Module synced successfully."

# --- Step 3: Run Odoo upgrade on remote ---------------------------------------
log "Running Odoo module upgrade on remote server..."
${SSH_CMD} "${REMOTE_HOST}" \
  "cd ${LIVE_PROJECT_DIR} && \
   docker exec ${LIVE_ODOO_CONTAINER} \
     odoo \
       --db_host=db --db_user=${DB_USER} --db_password=${DB_PASSWORD} \
       --addons-path=${ODOO_ADDONS_PATH} \
       --db-filter=\"^${REMOTE_DB_NAME}\$\" \
       --log-level=info \
       -d ${REMOTE_DB_NAME} \
       -u ${MODULE} \
       --stop-after-init \
       --no-http" \
  || die "Odoo module upgrade FAILED on remote server."

log "Module upgrade completed successfully on remote server."

# --- Step 4: Report -----------------------------------------------------------
cat <<MSG

=== DEPLOY REMEDIATION RESULT ===
  Server:   ${REMOTE_HOST}
  Module:   ${MODULE}
  DB:       ${REMOTE_DB_NAME}
  Backup:   ${BACKUP_REMOTE_PATH}
  Status:   SUCCESS

The module has been upgraded. Verify on the live site.
MSG

log "deploy_remediation.sh done."
