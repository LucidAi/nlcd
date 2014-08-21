#!/bin/sh
# Author: Vova Zaytsev <zaytsev@usc.edu>

PYTHON=python
THISDIR=`pwd`
ORIGINS=distr/proposal/origins.txt
WORKDIR=/Users/zvm/dev/nlcd_1

${PYTHON} ${THISDIR}/pipelines/pipeline.py          \
    --origins-file-path ${ORIGINS}                  \
    --app-root ${THISDIR}/husky                     \
    --pipeline-root ${THISDIR}/scripts/pipeline     \
    --work-dir ${WORKDIR}                           \
    --first-step 1                                  \
    --last-step 9                                   \
    --n-cpus 4                                      \
    --max-threads 16                                \
    --use-compression 1                             \
    --nlcd-conf-file ${THISDIR}/conf/dev.json       \
    --gse-bottom-threshold 100                      \
    --gse-upper-threshold 1000                      \
    --gse-query-size-heuristic 10                   \
    --verbosity-level 0
