#!/usr/bin/env bash

set -euo pipefail

REMOTE_URL="${REMOTE_URL:-https://github.com/AleeexTk/evopyramid-ai.git}"
REPO_DIR="${REPO_DIR:-$HOME/evopyramid-ai}"
BRANCH="${BRANCH:-main}"
CONFIG_SOURCE="${CONFIG_SOURCE:-EvoMETA/evo_config.yaml}"
CONFIG_TARGET_DIR="${CONFIG_TARGET_DIR:-$HOME/.config/evocore}"
SKIP_INSTALL=0
SKIP_SMOKE=0

usage() {
  cat <<'EOF'
Usage: termux_evocore_sync.sh [options]

Synchronise a Termux node with the latest EvoPyramid/EvoCore state.

Options:
  --branch <name>       Git branch to checkout before syncing (default: main)
  --skip-install        Skip dependency installation steps.
  --skip-smoke          Skip the lightweight smoke check after syncing.
  --help                Display this help message and exit.

Environment overrides:
  REMOTE_URL            Git remote to clone when the repository is missing.
  REPO_DIR              Target directory for the repository clone.
  CONFIG_SOURCE         Path (inside the repo) of the EvoCore config template.
  CONFIG_TARGET_DIR     Destination directory for installed configs.
EOF
}

log() {
  printf '[EvoSync] %s\n' "$*"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch)
      [[ $# -lt 2 ]] && { echo "Missing value for --branch" >&2; exit 1; }
      BRANCH="$2"
      shift 2
      ;;
    --skip-install)
      SKIP_INSTALL=1
      shift
      ;;
    --skip-smoke)
      SKIP_SMOKE=1
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

ensure_repo() {
  if [[ -d "$REPO_DIR/.git" ]]; then
    log "Repository found at $REPO_DIR"
    return
  fi

  log "Repository not found – cloning from $REMOTE_URL"
  git clone "$REMOTE_URL" "$REPO_DIR"
}

update_repo() {
  cd "$REPO_DIR"
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull --rebase origin "$BRANCH"
}

install_dependencies() {
  (( SKIP_INSTALL )) && { log "Dependency installation skipped"; return; }

  cd "$REPO_DIR"

  if command -v python >/dev/null 2>&1 && command -v pip >/dev/null 2>&1; then
    if [[ -f requirements.txt ]]; then
      log "Installing requirements.txt dependencies"
      pip install -r requirements.txt || log "requirements.txt install failed (continuing)"
    fi

    if [[ -f requirements_context.txt ]]; then
      log "Installing requirements_context.txt dependencies"
      pip install -r requirements_context.txt || log "requirements_context.txt install failed (continuing)"
    fi
  else
    log "Python or pip not available – skipping dependency installation"
  fi
}

sync_configs() {
  cd "$REPO_DIR"
  if [[ -f "$CONFIG_SOURCE" ]]; then
    mkdir -p "$CONFIG_TARGET_DIR"
    cp "$CONFIG_SOURCE" "$CONFIG_TARGET_DIR/evo_config.yaml"
    log "EvoCore config synced to $CONFIG_TARGET_DIR/evo_config.yaml"
  else
    log "Config source $CONFIG_SOURCE not found – skipping config sync"
  fi
}

run_smoke_check() {
  (( SKIP_SMOKE )) && { log "Smoke check skipped"; return; }

  if ! command -v python >/dev/null 2>&1; then
    log "Python not available – skipping smoke check"
    return
  fi

  cd "$REPO_DIR"

  if python -m compileall apps/core >/dev/null 2>&1; then
    log "Smoke check passed (python -m compileall apps/core)"
  else
    log "Smoke check encountered issues – inspect output above"
  fi
}

ensure_repo
update_repo
install_dependencies
sync_configs
run_smoke_check

log "Termux ↔ EvoCore sync complete"
