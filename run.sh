#!/bin/bash

export PYTHONPATH=$(pwd):$PYTHONPATH
while [ 1 ]; do
	python Main.py
	sleep 1
done
