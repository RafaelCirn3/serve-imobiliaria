@echo off
setlocal
set "ROBOT_PYTHON=%~dp0..\.venv\Scripts\python.exe"
if not exist "%ROBOT_PYTHON%" set "ROBOT_PYTHON=python"
"%ROBOT_PYTHON%" "%~dp0manage.py" robot-mga %*
exit /b %errorlevel%
