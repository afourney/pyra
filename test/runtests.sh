#!/bin/sh
export PYTHONPATH=..:$PYTHONPATH
rm *.pyc
rm -rf __pycache__
rm ../pyra/*.pyc
rm -rf ../pyra/__pycache__
python -m unittest discover -v
#python3 -m unittest discover -v
