#!/usr/bin/env bash
source .venv/bin/activate
pytest
python -m app.evals.run_eval
