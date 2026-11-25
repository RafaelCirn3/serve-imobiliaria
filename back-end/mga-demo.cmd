@echo off
setlocal
cd /d "%~dp0"
set "ROBOT_PYTHON=%~dp0..\.venv\Scripts\python.exe"
if not exist "%ROBOT_PYTHON%" set "ROBOT_PYTHON=python"
"%ROBOT_PYTHON%" manage.py migrate --settings=config.robot_demo_settings --noinput
if errorlevel 1 exit /b %errorlevel%
"%ROBOT_PYTHON%" manage.py robot-mga --arquivo apps/robot/fixtures/mga/avulsos-novembro-2026.pdf --contexto apps/robot/fixtures/mga/demo-context.json --aplicar --output reports/mga/demo-result.json --settings=config.robot_demo_settings
exit /b %errorlevel%
