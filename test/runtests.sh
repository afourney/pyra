#!/bin/sh
export PYTHONPATH=..:$PYTHONPATH
python -m unittest discover -v
