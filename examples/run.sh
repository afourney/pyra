#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
exec "${PYTHON:-python3}" examples/gcl_shell.py
