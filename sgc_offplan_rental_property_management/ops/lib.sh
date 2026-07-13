#!/usr/bin/env bash
# Shared configuration and helpers for the sgc_offplan_rental_property_management
# ops scripts. Source this from every script: `source "$(dirname "$0")/lib.sh"`.
#
# Nothing in here mutates state; it only defines variables and helper functions.
set -euo pipefail

# --- Paths -------------------------------------------------------------------
# OPS_DIR   -> this ops/ directory (inside the module repo)
# MODULE_DIR-> the module repo root (the git repo we build worktrees from)
# MODULE    -> the technical name of the Odoo module under test
OPS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${OPS_DIR}/.." && pwd)"
MODULE="sgc_offplan_rental_property_management"

# --- Live stack (READ-ONLY from these scripts, never mutated) -----------------
LIVE_PROJECT_DIR="/opt/odoo/demo_presentation"
LIVE_ADDONS_DIR="${LIVE_PROJECT_DIR}/addons"
LIVE_ODOO_CONTAINER="demo_presentation"
LIVE_DB_CONTAINER="demo_presentation_db"

# --- Staging stack ------------------------------------------------------------
STAGING_DIR="/opt/odoo/demo_presentation_staging"
STAGING_ADDONS_DIR="${STAGING_DIR}/addons"
STAGING_COMPOSE="${STAGING_DIR}/docker-compose.yml"
STAGING_DB_DUMP="${STAGING_DIR}/db_snapshot.dump"
STAGING_PROJECT="demo_presentation_staging"
STAGING_ODOO_CONTAINER="demo_presentation_staging"
STAGING_DB_CONTAINER="demo_presentation_staging_db"
# Default compose network name (project + _default).
STAGING_NETWORK="${STAGING_PROJECT}_default"

# --- Prod stack (the live demo; only deploy_prod.sh may touch it) -------------
PROD_PROJECT_DIR="${LIVE_PROJECT_DIR}"
PROD_COMPOSE="${LIVE_PROJECT_DIR}/docker-compose.yml"
PROD_PROJECT="demo_presentation"
PROD_ODOO_CONTAINER="${LIVE_ODOO_CONTAINER}"
PROD_DB_CONTAINER="${LIVE_DB_CONTAINER}"

# --- Database ----------------------------------------------------------------
DB_NAME="demo_presentation_19"
DB_USER="odoo"
# Odoo addons path used inside the container (mirrors the live compose command).
ODOO_ADDONS_PATH="/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons"

# The DB password is a secret and is NEVER hardcoded here (this file is in git).
# Provide it via the environment or a gitignored ops.env next to this script.
# See ops.env.example for the template.
if [[ -f "${OPS_DIR}/ops.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${OPS_DIR}/ops.env"; set +a
fi
DB_PASSWORD="${DB_PASSWORD:-}"
if [[ -z "${DB_PASSWORD}" ]]; then
  echo "ERROR: DB_PASSWORD is not set. Create ${OPS_DIR}/ops.env (copy ops.env.example) or export DB_PASSWORD." >&2
  exit 1
fi

# --- Backups -----------------------------------------------------------------
BACKUP_DIR="${OPS_DIR}/backups"
BACKUP_KEEP=5

# --- Docker binary compatibility ---------------------------------------------
# This host only ships the standalone `docker-compose` (v2.27.0); the
# `docker compose` plugin is not installed. Resolve once here.
if command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
elif docker compose version >/dev/null 2>&1; then
  DC="docker compose"
else
  echo "ERROR: neither 'docker-compose' nor 'docker compose' is available." >&2
  exit 1
fi

# --- Helpers -----------------------------------------------------------------
log()  { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# Guardrail: refuse to run docker mutations against the live containers from any
# script that isn't deploy_prod.sh. This is a defense-in-depth check so an
# accidental variable mix-up can't stop/restart the live demo.
assert_not_live() {
  local target="$1"
  if [[ "${ALLOW_LIVE:-0}" != "1" ]]; then
    if [[ "$target" == "${LIVE_ODOO_CONTAINER}" || "$target" == "${LIVE_DB_CONTAINER}" ]]; then
      die "refusing to mutate live container '${target}' (set ALLOW_LIVE=1 only from deploy_prod.sh)"
    fi
  fi
}

# Wait until a postgres container answers pg_isready (up to ~60s).
wait_for_db() {
  local container="$1"
  local i
  for i in $(seq 1 60); do
    if docker exec "$container" pg_isready -U "${DB_USER}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  die "database container '${container}' did not become ready in time"
}

# Wait until an Odoo container is serving HTTP on the given host port (up to ~90s).
wait_for_http() {
  local port="$1"
  local i
  for i in $(seq 1 45); do
    if curl -sf -o /dev/null "http://localhost:${port}/web/login"; then
      return 0
    fi
    sleep 2
  done
  return 1
}
