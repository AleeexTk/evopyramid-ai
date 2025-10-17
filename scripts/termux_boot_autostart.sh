#!/data/data/com.termux/files/usr/bin/bash
# EvoPyramid Termux boot synchronizer and launcher (runtime-integrated)

set -euo pipefail

DEFAULT_HOME="${HOME:-/data/data/com.termux/files/home}"
EVO_PARENT_DIR="${EVO_PARENT_DIR:-$DEFAULT_HOME}"            # ← default to $HOME, avoid /storage for git safety
REPO_NAME="${REPO_NAME:-evopyramid-ai}"
REPO_URL="${REPO_URL:-https://github.com/AleeexTk/evopyramid-ai.git}"
LOCAL_DIR="${LOCAL_DIR:-$EVO_PARENT_DIR/$REPO_NAME}"
LOG_DIR="${LOG_DIR:-$EVO_PARENT_DIR/logs/termux_boot}"
PY_ENV="${PY_ENV:-/data/data/com.termux/files/usr/bin/python3}"
ENTRY_POINT="${PYTHON_ENTRYPOINT:-apps.core.trinity_observer}"
GIT_REMOTE="${GIT_REMOTE:-origin}"
GIT_BRANCH="${GIT_BRANCH:-main}"
RUNTIME_SCRIPT_REL="core/runtime/main.py"

expand_path() {
  case "$1" in
    "~"|"~"/*)
      printf '%s\n' "${HOME}${1:1}"
      ;;
    *)
      printf '%s\n' "$1"
      ;;
  esac
}

EVO_PARENT_DIR="$(expand_path "$EVO_PARENT_DIR")"
LOCAL_DIR="$(expand_path "$LOCAL_DIR")"
LOG_DIR="$(expand_path "$LOG_DIR")"

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/boot-$(date +%Y%m%d-%H%M%S).log"
touch "$LOG_FILE"

log() {
  printf '[%s] %s\n' "$(date +%Y-%m-%dT%H:%M:%S%z)" "$1" | tee -a "$LOG_FILE"
}

log "Termux boot runtime initialising"

# --- sanity checks ---
if [ ! -x "$PY_ENV" ]; then
  if command -v python3 >/dev/null 2>&1; then
    PY_ENV="$(command -v python3)"
    log "Using fallback python interpreter at $PY_ENV"
  else
    log "Python interpreter not found; aborting"
    exit 1
  fi
fi

if ! command -v git >/dev/null 2>&1; then
  log "git not found in PATH; install it via 'pkg install git'"
  exit 1
fi

# --- ensure repo present (clone or refresh) ---
ensure_repository_materialised() {
  if [ -f "$LOCAL_DIR/$RUNTIME_SCRIPT_REL" ]; then
    return
  fi

  if [ -d "$LOCAL_DIR/.git" ]; then
    log "Repository detected but runtime script missing; refreshing working tree"
    (
      cd "$LOCAL_DIR" && \
      git fetch "$GIT_REMOTE" "$GIT_BRANCH" >>"$LOG_FILE" 2>&1 || true
      git reset --hard "$GIT_REMOTE/$GIT_BRANCH" >>"$LOG_FILE" 2>&1 || true
    )
  else
    log "Cloning repository into $LOCAL_DIR"
    mkdir -p "$(dirname -- "$LOCAL_DIR")"
    if ! git clone "$REPO_URL" "$LOCAL_DIR" >>"$LOG_FILE" 2>&1; then
      log "git clone failed; ensure network access and credentials"
      exit 1
    fi
  fi
}

ensure_repository_materialised

if [ ! -f "$LOCAL_DIR/$RUNTIME_SCRIPT_REL" ]; then
  log "Runtime entry script $LOCAL_DIR/$RUNTIME_SCRIPT_REL missing"
  exit 1
fi

# --- pass config to Python runtime ---
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

# include legacy migration paths if they exist (optional)
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

# --- run orchestrator (single entry point) ---
log "Invoking EvoRuntime orchestrator"
"$PY_ENV" "$LOCAL_DIR/$RUNTIME_SCRIPT_REL" --environment termux --log-file "$LOG_FILE"
STATUS=$?
if [ $STATUS -ne 0 ]; then
  log "Runtime orchestrator exited with status $STATUS"
  exit $STATUS
fi

log "Termux boot runtime completed"
