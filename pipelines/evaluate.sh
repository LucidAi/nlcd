#!/bin/sh

PYTHON=python
THISDIR=`pwd`
WORKDIR=/Users/zvm/dev/nlcd_eval

${PYTHON} ${THISDIR}/pipelines/evaluate.py                      \
    --pipeline-root ${THISDIR}/scripts/pipeline                 \
    --app-root ${THISDIR}/husky                                 \
    --work-dir ${WORKDIR}                                       \
    --first-step 3                                              \
    --last-step 3                                               \
    --n-cpus 4                                                  \
    --max-threads 50                                            \
    --use-compression 1                                         \
    --nlcd-conf-file ${THISDIR}/fab/dev.json                    \
    --gold distr/gold/titles.authors.sources.dates.extr.csv     \
    --cse distr/gold/cse.annotations.json						\
    --verbosity-level 0
