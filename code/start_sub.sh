#!/bin/bash

JOBNAME=$1

WORKDIR=/tmp/workdir
ROOT=ozymandias

VMNAME=$2
INDEX=$3
ZONE=$4
ROLE="worker"

gcloud compute ssh ${ROOT}@${VMNAME} --zone ${ZONE} -- sudo rm -rf $WORKDIR
gcloud compute ssh ${ROOT}@${VMNAME} --zone ${ZONE} -- sudo mkdir -p $WORKDIR

gcloud compute scp --zone ${ZONE} \
    --recurse \
  ${WORKDIR}/tf_config.json ${WORKDIR}/start_one_time_traning_server.sh \
  root@${VMNAME}:${WORKDIR}

readarray config < $WORKDIR/train_config.txt

gcloud compute ssh ${ROOT}@$VMNAME --zone ${ZONE} -- $WORKDIR/start_one_time_traning_server.sh ${config[0]} ${config[1]} 2 $INDEX 0 ${config[2]} ${config[3]} ${config[4]} ${config[5]} ${config[6]} ${config[7]} ${config[8]} ${config[9]} ${config[10]} ${config[11]} ${config[12]} ${config[13]} 1 &


