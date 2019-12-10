#!/bin/bash

JOBNAME=$1
echo "Job name:"
echo $JOBNAME
NUM_PS=$2
NUM_WORKER=$3
ROOT=ozymandias

for  i in $(seq 0 $NUM_PS); do
  echo "Terminating ps-${i}..."
  ZONE=`gcloud compute instances list ${JOBNAME}-ps-${i} --format 'csv[no-heading](zone)'`
  gcloud compute ssh ${ROOT}@${JOBNAME}-ps-${i} --zone ${ZONE} -- pkill -f t2t-trainer
done

# Stop workers
echo "Terminating worker..."
if [[ $NUM_WORKER -ge 0 ]]; then
    for  i in $(seq 0 $NUM_WORKER); do
      echo "Terminating worker-${i}..."
      ZONE=`gcloud compute instances list ${JOBNAME}-worker-${i} --format 'csv[no-heading](zone)'`
      gcloud compute ssh ${ROOT}@${JOBNAME}-worker-${i} --zone ${ZONE} -- pkill -f t2t-trainer
    done
fi

# Stop a master
echo "Terminating master-0..."
ZONE=`gcloud compute instances list ${JOBNAME}-master --format 'csv[no-heading](zone)'`
gcloud compute ssh ${ROOT}@${JOBNAME}-master --zone ${ZONE} -- pkill -f t2t-trainer
