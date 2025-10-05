Write-Output "[Evo] Local bootstrap…"
if (Test-Path .\venv) {} else { python -m venv venv }
.\venv\Scripts\activate
if (Test-Path requirements.txt) { pip install -r requirements.txt }
if (Test-Path requirements_context.txt) { pip install -r requirements_context.txt }
python -m apps.core.observers.trinity_observer
