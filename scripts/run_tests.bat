@echo off
rem Fail fast: without the errorlevel checks the script's exit code is the
rem LAST command's, so a failing pytest followed by a passing eval reports green.
call .venv\Scripts\activate
if errorlevel 1 exit /b 1
pytest
if errorlevel 1 exit /b 1
python -m app.evals.run_eval
if errorlevel 1 exit /b 1
