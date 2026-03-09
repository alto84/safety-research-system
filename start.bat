@echo off
REM Quick-start the Simulated Patient Safety
REM Usage: start.bat [port]

set PORT=%1
if "%PORT%"=="" set PORT=8000

echo Starting Simulated Patient Safety on port %PORT%...
python run_server.py --port %PORT% --open
