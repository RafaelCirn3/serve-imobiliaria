@echo off
setlocal
set "ROBOT_PYTHON=%~dp0..\.venv\Scripts\python.exe"
if not exist "%ROBOT_PYTHON%" set "ROBOT_PYTHON=python"
set "PYTHONPATH=%~dp0"
"%ROBOT_PYTHON%" -m apps.robot.mcp_server
exit /b %errorlevel%
