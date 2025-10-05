#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "[Evo] Bootstrapping Termux node…"
pkg update -y
pkg install -y python git openssh

cd "$HOME"
[ -d evopyramid-ai ] || git clone https://github.com/AleeexTk/evopyramid-ai.git
cd evopyramid-ai

if [ -f requirements.txt ]; then pip install -r requirements.txt || true; fi
if [ -f requirements_context.txt ]; then pip install -r requirements_context.txt || true; fi

# Запускаем Trinity-Observer в фоне (лог в $HOME/trinity.log)
nohup python -m apps.core.trinity_observer > "$HOME/trinity.log" 2>&1 &
echo "[Evo] Trinity Observer started."
