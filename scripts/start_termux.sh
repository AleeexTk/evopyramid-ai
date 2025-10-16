#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

termux-setup-storage || true

echo "[Evo] Bootstrapping Termux node…"
pkg update -y
pkg install -y python git openssh

cd "$HOME"
if [ ! -d evopyramid-ai ]; then
  git clone https://github.com/AleeexTk/evopyramid-ai.git
fi
cd evopyramid-ai

pip install -U pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt || true
fi
if [ -f requirements_context.txt ]; then
  pip install -r requirements_context.txt || true
fi

python -m apps.core.keys.key_loader >/dev/null 2>&1 || true
mkdir -p logs
nohup python -m apps.core.observers.trinity_observer > "logs/trinity_run.log" 2>&1 &
echo "[Evo] Trinity Observer started. Logs → $PWD/logs/trinity_run.log"
nohup python -m apps.core.trinity_observer > "$HOME/trinity.log" 2>&1 &
echo "[Evo] Legacy Trinity Observer started. Logs → $HOME/trinity.log"
