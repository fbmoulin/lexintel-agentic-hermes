@echo off
call .venv\Scripts\activate
pytest
python -m app.evals.run_eval
