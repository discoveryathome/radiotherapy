#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MPLCONFIGDIR="$PWD/.cache/matplotlib"
.venv/bin/python -m rtpilot.verify
.venv/bin/python -m rtpilot.verify_trial
.venv/bin/python -m unittest discover -s tests -v
