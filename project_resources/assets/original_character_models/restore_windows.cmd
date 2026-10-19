@echo off
cd /d "%~dp0"
py -3 restore_originals.py
if errorlevel 1 (
  echo Restore failed. Check the error above.
  pause
  exit /b 1
)
pause
