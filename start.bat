@echo off
REM Quick-start the Predictive Safety Platform
REM Usage: start.bat [port]

set PORT=%1
if "%PORT%"=="" set PORT=8000

echo Starting Predictive Safety Platform on port %PORT%...
python run_server.py --port %PORT% --open
