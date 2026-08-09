#!/usr/bin/env bash
# Fail fast: without -e the script's exit code is the LAST command's, so a
# failing pytest followed by a passing eval would report green.
set -euo pipefail
source .venv/bin/activate
pytest
python -m app.evals.run_eval
