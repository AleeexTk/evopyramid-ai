#!/usr/bin/env bash
set -euo pipefail

echo "[Evo] Local bootstrap…"

if [ ! -d .venv ]; then
  python -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

pip install -U pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi
if [ -f requirements_context.txt ]; then
  pip install -r requirements_context.txt
fi

python -m apps.core.observers.trinity_observer
python -m apps.core.trinity_observer
