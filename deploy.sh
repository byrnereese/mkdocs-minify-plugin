#!/bin/bash

rm -rf dist
python3 setup.py bdist_wheel sdist --formats gztar && twine upload dist/*
