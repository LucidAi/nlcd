#!/bin/sh

PYTHON=python
THISDIR=`pwd`
ORIGINS=${THISDIR}/test/1.origins.txt
WORKDIR=/Users/zvm/dev/nlcd

# ${THISDIR} java -mx1000m -cp vendor/stanford-ner/stanford-ner.jar edu.stanford.nlp.ie.NERServer \
#                        -loadClassifier vendor/stanford-ner-models/english.all.3class.distsim.crf.ser.gz -port 9191

${PYTHON} ${THISDIR}/scripts/pipeline.py        	\
    --origins-file-path ${ORIGINS}              	\
    --app-root ${THISDIR}/fenrir                	\
    --pipeline-root ${THISDIR}/scripts/pipeline 	\
    --work-dir ${WORKDIR}                       	\
    --first-step 11                             	\
    --last-step 11                                	\
    --n-cpus 4                                  	\
    --max-threads 8                              	\
    --use-compression 1                         	\
    --gold-dates-norm distr/gold/dates.norm.csv 	\
    --eval-dates-norm distr/eval/dates.norm.csv 	\
    --gold-extr distr/gold/dates.authors.extr.csv	\
	--eval-extr distr/eval/ 						\
    --nlcd-conf-file ${THISDIR}/fab/dev.json
