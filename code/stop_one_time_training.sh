#!/bin/bash

# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Get the number of nodes
JOBNAME=$1
echo "Job name:"
echo $JOBNAME
NUM_PS=$2
NUM_WORKER=$3
ROOT=ozymandias
#NUM_PS=$(gcloud compute instances list | grep -E '^ps-[0-9]+ ' | wc -l)
#NUM_WORKER=$(gcloud compute instances list | grep -E '^worker-[0-9]+ ' | wc -l)

#NUM_PS=$(( NUM_PS - 1 ))
#NUM_WORKER=$(( NUM_WORKER - 1 ))

# Stop parameter servers
#echo "Terminating ps..."
#ZONE=`gcloud compute instances list ${JOBNAME}-ps-0 --format 'csv[no-heading](zone)'`
#gcloud compute ssh ${ROOT}@${JOBNAME}-ps-0 --zone ${ZONE} -- pkill -f t2t-trainer
for  i in $(seq 0 $NUM_PS); do
  echo "Terminating ps-${i}..."
  ZONE=`gcloud compute instances list ${JOBNAME}-ps-${i} --format 'csv[no-heading](zone)'`
#  gcloud compute ssh ${ROOT}@${JOBNAME}-ps --zone ${ZONE} -- sudo pkill -2 mpstat
  gcloud compute ssh ${ROOT}@${JOBNAME}-ps-${i} --zone ${ZONE} -- pkill -f t2t-trainer
  gcloud compute ssh ${ROOT}@${JOBNAME}-ps-${i} --zone ${ZONE} -- sudo pkill -f python
done

# Stop workers
echo "Terminating worker..."
#ZONE=`gcloud compute instances list ${JOBNAME}-${NUM_WORKER}-${MAX_WORKER}-worker-${i} --format 'csv[no-heading](zone)'`
#gcloud compute ssh ${ROOT}@${JOBNAME} --zone ${ZONE} -- pkill -f t2t-trainer
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
