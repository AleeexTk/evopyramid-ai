#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_FILE="$REPO_ROOT/EvoMETA/evo_config.yaml"
VENV_PATH="$REPO_ROOT/.venv"

if [ ! -d "$VENV_PATH" ]; then
  python3 -m venv "$VENV_PATH"
fi

# shellcheck source=/dev/null
source "$VENV_PATH/bin/activate"

pip install --upgrade pip >/dev/null
pip install -r "$REPO_ROOT/requirements.txt" 2>/dev/null || true

export EVO_CONFIG="$CONFIG_FILE"
export PYTHONPATH="$REPO_ROOT/apps:$PYTHONPATH"

cd "$REPO_ROOT"
python -m core.evo_core
