# /usr/bin/env bash

PYTHON=python
THISDIR=`pwd`
ORIGINS=$THISDIR/test/1.origins.txt
WORKDIR=/Volumes/1TB/workdir

$PYTHON $THISDIR/scripts/pipeline.py               \
    --origins-file-path $ORIGINS                \
    --app-root $THISDIR/fenrir                  \
    --pipeline-root $THISDIR/scripts/pipeline   \
    --work-dir $WORKDIR                         \
    --first-step 1                              \
    --n-cpus 4                                  \
    --max-threads 10                            \
    --nlcd-conf-file $THISDIR/fab/dev.json
