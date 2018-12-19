#!/bin/bash

rm -rf dist
python setup.py bdist_wheel sdist --formats gztar && twine upload dist/*
