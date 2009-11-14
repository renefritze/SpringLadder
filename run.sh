#!/bin/bash

export PYTHONPATH=$(pwd):$PYTHONPATH
while [ 1 ]; do
	python Main.py
	echo sleeping
	sleep 3
done
