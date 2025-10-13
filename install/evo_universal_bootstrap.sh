#!/usr/bin/env bash
set -e

# Universal bootstrap for Termux (Android) and Desktop (Linux/macOS/WSL)
if [ -n "$ANDROID_ROOT" ] && [ -d "/data/data/com.termux" ]; then
  ENV="termux"; PYBIN="python"; PKG="pkg"
else
  ENV="desktop"; PYBIN="python3"; PKG=""
fi

LOG="$HOME/evo_boot.log"
echo "[Evo] === Universal Bootstrap ($ENV) ===" | tee "$LOG"

if [ "$ENV" = "termux" ]; then
  pkg update -y && pkg upgrade -y
  pkg install -y python git openssh curl jq
else
  if ! command -v git >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y git
  fi
  if ! command -v $PYBIN >/dev/null 2>&1; then
    sudo apt-get install -y python3 python3-pip
  fi
fi

cd "$HOME"
if [ ! -d evopyramid-ai ]; then
  echo "[Evo] Cloning repository..." | tee -a "$LOG"
  git clone https://github.com/AleeexTk/evopyramid-ai.git >>"$LOG" 2>&1
else
  echo "[Evo] Updating repository..." | tee -a "$LOG"
  cd evopyramid-ai && git pull >>"$LOG" 2>&1
fi
cd "$HOME/evopyramid-ai"

for f in requirements.txt requirements_context.txt; do
  if [ -f "$f" ]; then
    echo "[Evo] Installing $f..." | tee -a "$LOG"
    $PYBIN -m pip install -r "$f" --break-system-packages >>"$LOG" 2>&1 || echo "[!] $f failed" | tee -a "$LOG"
  fi
done

$PYBIN -m apps.core.keys.key_loader >/dev/null 2>&1 || true
mkdir -p logs

echo "[Evo] Starting Trinity Observer..." | tee -a "$LOG"
nohup $PYBIN -m apps.core.observers.trinity_observer > "logs/trinity_run.log" 2>&1 &
sleep 3
echo "[Evo] Trinity Observer started → logs/trinity_run.log" | tee -a "$LOG"

echo "[Evo] Initializing EEI/EMI & Alignment..." | tee -a "$LOG"
$PYBIN -m apps.core.motivation.evo_efficiency_init >/dev/null 2>&1 || echo "[!] EEI init failed" | tee -a "$LOG"
$PYBIN -m apps.core.motivation.evo_alignment_core >/dev/null 2>&1 || echo "[!] Alignment init failed" | tee -a "$LOG"

echo "[Evo] Checking Trinity status..." | tee -a "$LOG"
ps aux | grep trinity_observer | grep -v grep >>"$LOG" 2>&1 || echo "[!] Trinity not running" | tee -a "$LOG"

echo "[Evo] Last 20 lines of log:" | tee -a "$LOG"
tail -n 20 logs/trinity_run.log | tee -a "$LOG"

if [ "$ENV" = "termux" ]; then
  if ! grep -q "evo_universal_bootstrap.sh" ~/.bashrc 2>/dev/null; then
    echo "bash ~/evopyramid-ai/install/evo_universal_bootstrap.sh" >> ~/.bashrc
    echo "[Evo] Auto-launch enabled in .bashrc" | tee -a "$LOG"
  fi
fi

echo "[Evo] ✅ Bootstrap complete."
echo "[Evo] Review → $LOG"
