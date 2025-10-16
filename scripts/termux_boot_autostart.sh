#!/data/data/com.termux/files/usr/bin/bash
# EvoPyramid Termux boot synchronizer and launcher

set -euo pipefail

EVO_PARENT_DIR="${EVO_PARENT_DIR:-/storage/emulated/0/EVO_LOCAL}"
REPO_NAME="${REPO_NAME:-evopyramid-ai}"
REPO_URL="${REPO_URL:-https://github.com/AleeexTk/evopyramid-ai.git}"
LOCAL_DIR="${LOCAL_DIR:-$EVO_PARENT_DIR/$REPO_NAME}"
LOG_DIR="${LOG_DIR:-$EVO_PARENT_DIR/logs/termux_boot}"
PY_ENV="${PY_ENV:-/data/data/com.termux/files/usr/bin/python3}"
PYTHON_ENTRYPOINT="${PYTHON_ENTRYPOINT:-apps.core.trinity_observer}"
GIT_REMOTE="${GIT_REMOTE:-origin}"
GIT_BRANCH="${GIT_BRANCH:-main}"
WAKE_LOCK_HELD=0

LOG_FILE="$LOG_DIR/boot-$(date +%Y%m%d-%H%M%S).log"
LOG_READY=0

if ! mkdir -p "$LOG_DIR"; then
  printf '[%s] Unable to create log directory %s\n' "$(date +%Y-%m-%dT%H:%M:%S%z)" "$LOG_DIR" >&2
  exit 1
fi

if ! touch "$LOG_FILE"; then
  printf '[%s] Unable to create log file %s\n' "$(date +%Y-%m-%dT%H:%M:%S%z)" "$LOG_FILE" >&2
  exit 1
fi

LOG_READY=1

log() {
  local message="$1"
  if (( LOG_READY )); then
    printf '[%s] %s\n' "$(date +%Y-%m-%dT%H:%M:%S%z)" "$message" | tee -a "$LOG_FILE"
  else
    printf '[%s] %s\n' "$(date +%Y-%m-%dT%H:%M:%S%z)" "$message" >&2
  fi
}

cleanup() {
  if (( WAKE_LOCK_HELD )) && command -v termux-wake-unlock >/dev/null 2>&1; then
    termux-wake-unlock || true
    WAKE_LOCK_HELD=0
    log "Wake lock released"
  fi
}

trap cleanup EXIT

if command -v termux-wake-lock >/dev/null 2>&1; then
  if termux-wake-lock; then
    WAKE_LOCK_HELD=1
    log "Wake lock acquired"
  else
    log "Unable to acquire wake lock"
  fi
else
  log "termux-wake-lock not available"
fi

log "EvoPyramid boot sync initiated"

if ! mkdir -p "$EVO_PARENT_DIR"; then
  log "Failed to ensure parent directory $EVO_PARENT_DIR"
  exit 1
fi

if [[ ! -d "$LOCAL_DIR/.git" ]]; then
  if [[ -d "$LOCAL_DIR" ]]; then
    log "Directory $LOCAL_DIR exists without git metadata"
  else
    log "Repository missing – cloning $REPO_URL into $LOCAL_DIR"
    if ! git clone "$REPO_URL" "$LOCAL_DIR" >>"$LOG_FILE" 2>&1; then
      log "Git clone failed"
      exit 1
    fi
  fi
fi

cd "$LOCAL_DIR" || { log "Cannot enter $LOCAL_DIR"; exit 1; }

if [[ ! -d .git ]]; then
  log "Directory $LOCAL_DIR is not a git repository"
  exit 1
fi

log "Fetching latest $GIT_REMOTE/$GIT_BRANCH"
if ! git fetch "$GIT_REMOTE" "$GIT_BRANCH" >>"$LOG_FILE" 2>&1; then
  log "git fetch failed"
  exit 1
fi

log "Saving local modifications"
if ! git stash push -u -m "termux-auto-$(date +%s)" >>"$LOG_FILE" 2>&1; then
  log "No local changes to stash"
fi

log "Resetting to $GIT_REMOTE/$GIT_BRANCH"
if ! git reset --hard "$GIT_REMOTE/$GIT_BRANCH" >>"$LOG_FILE" 2>&1; then
  log "git reset failed"
  exit 1
fi

if git stash list | grep -q "termux-auto"; then
  log "Reapplying stashed changes"
  if ! git stash pop >>"$LOG_FILE" 2>&1; then
    log "Stash reapply encountered issues"
  fi
else
  log "No stash entries to reapply"
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  log "Committing local adjustments"
  git add -A >>"$LOG_FILE" 2>&1
  if git commit -m "Termux auto-sync $(date +%Y-%m-%d)" >>"$LOG_FILE" 2>&1; then
    log "Local commit created"
  else
    log "Commit skipped"
  fi

  log "Pushing updates to $GIT_REMOTE/$GIT_BRANCH"
  if git push "$GIT_REMOTE" HEAD:"$GIT_BRANCH" --force-with-lease >>"$LOG_FILE" 2>&1; then
    log "Push completed"
  else
    log "Push failed"
  fi
else
  log "No changes detected after sync"
fi

if [[ -x "$PY_ENV" ]]; then
  RUNTIME_BIN="$PY_ENV"
else
  if command -v python3 >/dev/null 2>&1; then
    RUNTIME_BIN="$(command -v python3)"
    log "Using fallback python interpreter at $RUNTIME_BIN"
  else
    log "Python interpreter not found; skipping runtime launch"
    exit 0
  fi
fi

log "Launching EvoPyramid runtime module $PYTHON_ENTRYPOINT"
nohup "$RUNTIME_BIN" -m "$PYTHON_ENTRYPOINT" >>"$LOG_FILE" 2>&1 &
log "Runtime started with PID $!"

log "EvoPyramid boot sync complete"
