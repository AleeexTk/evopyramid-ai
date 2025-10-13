<<<<<<< HEAD
#!/usr/bin/env bash
set -e
python3 -m pip install -U pip
python3 -m pip install -r requirements.txt
python3 apps/cli/evocodex_shell.py <<'EOF'
diagnose
=======
Write-Output "[Evo] Local bootstrap…"
if (Test-Path .\venv) {} else { python -m venv venv }
.\venv\Scripts\activate
if (Test-Path requirements.txt) { pip install -r requirements.txt }
if (Test-Path requirements_context.txt) { pip install -r requirements_context.txt }
python -m apps.core.observers.trinity_observer
python -m apps.core.trinity_observer
>>>>>>> main
