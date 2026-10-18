@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Please follow the first-time setup in README.md.
  pause
  exit /b 1
)
if not exist "frontend\dist\index.html" (
  echo Frontend build missing. Run npm run build inside frontend first.
  pause
  exit /b 1
)
echo VisionAssist will open at http://127.0.0.1:8000
echo Keep this window open. Press Ctrl+C to stop the app.
".venv\Scripts\python.exe" -m alembic upgrade head
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
pause
