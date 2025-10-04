#!/usr/bin/env bash
set -e
python3 -m pip install -U pip
python3 -m pip install -r requirements.txt
python3 apps/cli/evocodex_shell.py <<'EOF'
diagnose
