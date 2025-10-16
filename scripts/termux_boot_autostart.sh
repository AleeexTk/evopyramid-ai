#!/data/data/com.termux/files/usr/bin/bash
# EvoPyramid Termux boot synchronizer and launcher (runtime-integrated)

set -euo pipefail

DEFAULT_HOME="${HOME:-/data/data/com.termux/files/home}"
EVO_PARENT_DIR="${EVO_PARENT_DIR:-$DEFAULT_HOME}"
REPO_NAME="${REPO_NAME:-evopyramid-ai}"
REPO_URL="${REPO_URL:-https://github.com/AleeexTk/evopyramid-ai.git}"
LOCAL_DIR="${LOCAL_DIR:-$EVO_PARENT_DIR/$REPO_NAME}"
LOG_DIR="${LOG_DIR:-$EVO_PARENT_DIR/logs/termux_boot}"
PY_ENV="${PY_ENV:-/data/data/com.termux/files/usr/bin/python3}"
ENTRY_POINT="${PYTHON_ENTRYPOINT:-apps.core.trinity_observer}"
GIT_REMOTE="${GIT_REMOTE:-origin}"
GIT_BRANCH="${GIT_BRANCH:-main}"
RUNTIME_SCRIPT="core/runtime/main.py"

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/boot-$(date +%Y%m%d-%H%M%S).log"
touch "$LOG_FILE"

log() {
  printf '[%s] %s\n' "$(date +%Y-%m-%dT%H:%M:%S%z)" "$1" | tee -a "$LOG_FILE"
}

log "Termux boot runtime initialising"

if [ ! -x "$PY_ENV" ]; then
  if command -v python3 >/dev/null 2>&1; then
    PY_ENV="$(command -v python3)"
    log "Using fallback python interpreter at $PY_ENV"
  else
    log "Python interpreter not found; aborting"
    exit 1
  fi
fi

if [ ! -f "$RUNTIME_SCRIPT" ]; then
  log "Runtime entry script $RUNTIME_SCRIPT missing"
  exit 1
fi

export EVO_RUNTIME_REPO_DIR="$LOCAL_DIR"
export EVO_RUNTIME_REPO_URL="$REPO_URL"
export EVO_RUNTIME_LOGS_DIR="$LOG_DIR"
export EVO_RUNTIME_ENTRY_POINT="$ENTRY_POINT"
export EVO_RUNTIME_GIT_REMOTE="$GIT_REMOTE"
export EVO_RUNTIME_GIT_BRANCH="$GIT_BRANCH"
export EVO_RUNTIME_PYTHON_BIN="$PY_ENV"
export EVO_RUNTIME_AUTO_SAFE_DIRECTORY="true"
export EVO_RUNTIME_PUSH_CHANGES="true"
export EVO_RUNTIME_EXTRA_WAKE_LOCK="1"

# Include legacy migration paths so first boot can relocate repositories.
LEGACY_PATHS=(
  "/storage/emulated/0/EVO_LOCAL/$REPO_NAME"
  "/sdcard/EVO_LOCAL/$REPO_NAME"
)
MIGRATE_FROM=""
for path in "${LEGACY_PATHS[@]}"; do
  if [ -d "$path" ]; then
    MIGRATE_FROM+="$path:"
  fi
done
if [ -n "$MIGRATE_FROM" ]; then
  export EVO_RUNTIME_MIGRATE_SOURCES="${MIGRATE_FROM%:}"
fi

log "Invoking EvoRuntime orchestrator"
"$PY_ENV" "$RUNTIME_SCRIPT" --environment termux --log-file "$LOG_FILE"
STATUS=$?
if [ $STATUS -ne 0 ]; then
  log "Runtime orchestrator exited with status $STATUS"
  exit $STATUS
fi

log "Termux boot runtime completed"
