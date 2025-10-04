#!/data/data/com.termux/files/usr/bin/bash
set -e
termux-setup-storage || true
pip install -U pip
pip install -r requirements.txt
python3 apps/core/evo_core.py
