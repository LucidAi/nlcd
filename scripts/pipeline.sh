#!/bin/sh

PYTHON=python
THISDIR=`pwd`
ORIGINS=${THISDIR}/test/1.origins.txt
WORKDIR=/Users/zvm/dev/nlcd

# ${THISDIR} java -mx1000m -cp vendor/stanford-ner/stanford-ner.jar edu.stanford.nlp.ie.NERServer \
#                        -loadClassifier vendor/stanford-ner-models/english.all.3class.distsim.crf.ser.gz -port 9191

${PYTHON} ${THISDIR}/scripts/pipeline.py        \
    --origins-file-path ${ORIGINS}              \
    --app-root ${THISDIR}/fenrir                \
    --pipeline-root ${THISDIR}/scripts/pipeline \
    --work-dir ${WORKDIR}                       \
    --first-step 4                              \
    --last-step 4                               \
    --n-cpus 4                                  \
    --max-threads 64                            \
    --use-compression 1							\
    --nlcd-conf-file ${THISDIR}/fab/dev.json
