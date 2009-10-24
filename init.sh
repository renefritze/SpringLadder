#!/bin/bash

if [ x$1 == x ] ; then
	DIR=../common
else
	DIR=${1}
fi

cd $(dirname $0)

if [ ! -d ${DIR} ] ; then
        echo "assumed to be in submodule structure"
        exit 1
fi

for py in $(ls ${DIR}/*.py) ; do
        ln -s ${py} 
done

