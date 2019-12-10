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

JOBNAME=$1

rm -r /tmp/${JOBNAME}
mkdir /tmp/${JOBNAME}

WORKDIR=/tmp/workdir
ROOT=ozymandias

touch /tmp/${JOBNAME}/job_start_time.txt
date -u > /tmp/${JOBNAME}/job_start_time.txt

if [[ $# -lt 1 ]]; then
  PROJECT_ID=$(gcloud config list project --format "value(core.project)")
  BUCKET="gs://${PROJECT_ID}-ml"
else
  BUCKET=$5
fi

pushd $(dirname $0) >/dev/null

# Get the number of nodes
NUM_PS=$2
NUM_WORKER=$3
NUM_SHARD=$4
MODEL=$6
HPARAM=$7
PROBLEM_DATA=$8
TRAIN_STEPS=$9
CKPT=${10}
AUTOMATION_TEST=${11}
RUN_NUM=${12}
PROFILE=${13}
SET_SLOT=${14}
MAX_WORKER=${15}

NUM_WORKER=$(( NUM_WORKER + 1 ))
#VM_NAME=${JOBNAME}-${NUM_WORKER}-${MAX_WORKER}

NUM_PS=$(( NUM_PS - 1 ))
NUM_WORKER=$(( NUM_WORKER - 2 ))
NUM_SHARD=$(( NUM_SHARD - 1 ))
MAX_WORKER=$(( MAX_WORKER - 1 ))

PORT_BASE=2222
MASTER_INDEX=0

if [[ $AUTOMATION_TEST == 1 ]]; then
    OUTDIR=${BUCKET}/${JOBNAME}-run${RUN_NUM}
else
    OUTDIR=${BUCKET}/${JOBNAME}
fi

case $PROBLEM_DATA in
    image_cifar10)
        DATADIR=${BUCKET}/cifar_data
        ;;
    image_cifar10_plain)
        DATADIR=${BUCKET}/cifar_data_plain
        ;;
    image_mnist)
        DATADIR=${BUCKET}/mnist_data
        ;;
    *)
        echo "Data source not found"
esac

if [[ $AUTOMATION_TEST == 1 ]]; then
    JOBNAME=automation
fi

gcloud compute ssh ${ROOT}@$JOBNAME-ps-0 --zone us-west1-b -- python /home/ozymandias/proj_code/code/xmlrpc_server.py &

# Force stop existing jobs
#echo "Force stop existing jobs."
#./stop_one_time_training.sh $JOBNAME $NUM_PS $NUM_WORKER

# Create TF_CONFIG file
ps_entry="\"ps\": ["
for i in $(seq 0 $NUM_PS); do
  for j in $(seq 0 $NUM_SHARD); do
    port_num=$(( $PORT_BASE + $j ))
    if [[ ! $i -eq $NUM_PS ]] || [[ ! $j -eq $NUM_SHARD ]]; then
      ps_entry="${ps_entry}\"${JOBNAME}-ps-${i}:2222\", "
    else
      ps_entry="${ps_entry}\"${JOBNAME}-ps-${i}:2222\"],"
    fi
  done
done

if [[ $SET_SLOT == 1 ]]; then
    worker_entry="\"worker\": ["
    for i in $(seq 0 $MAX_WORKER); do
      if [[ ! $i -eq $MAX_WORKER ]]; then
        worker_entry="${worker_entry}\"${JOBNAME}-worker-${i}:2222\", "
      else
        worker_entry="${worker_entry}\"${JOBNAME}-worker-${i}:2222\"],"
      fi
    done
elif [[ $NUM_WORKER -ge 0 ]]; then
    worker_entry="\"worker\": ["
    for i in $(seq 0 $NUM_WORKER); do
      if [[ ! $i -eq $NUM_WORKER ]]; then
        worker_entry="${worker_entry}\"${JOBNAME}-worker-${i}:2222\", "
      else
        worker_entry="${worker_entry}\"${JOBNAME}-worker-${i}:2222\"],"
      fi
    done
fi

master_entry=""\"chief"\": ["\"${JOBNAME}-master:2222"\"]"

cat <<EOF > /tmp/${JOBNAME}/tf_config.json
{
  "environment": "cloud",
  "cluster": {
    ${ps_entry}
    ${worker_entry}
    ${master_entry}
  },
  "task": {
    "index": __INDEX__,
    "type": "__ROLE__"
  }
}
EOF

echo "Start a training job."

# Start parameter servers in the background
#echo "Starting ps..."
#ZONE=`gcloud compute instances list $JOBNAME-ps-0 --format 'csv[no-heading](zone)'`
#gcloud compute ssh ${ROOT}@$JOBNAME-ps-0 --zone ${ZONE} -- sudo rm -rf $WORKDIR
#gcloud compute ssh ${ROOT}@$JOBNAME-ps-0 --zone ${ZONE} -- sudo mkdir -p $WORKDIR
#gcloud compute scp --zone ${ZONE} \
#    --recurse \
#    /tmp/${JOBNAME}/tf_config.json start_one_time_traning_server.sh \
#    root@$JOBNAME-ps-0:$WORKDIR
#gcloud compute ssh ${ROOT}@$JOBNAME-ps-0 --zone ${ZONE} -- $WORKDIR/start_one_time_traning_server.sh $DATADIR $OUTDIR 1 0 0 $NUM_PS $NUM_WORKER $NUM_SHARD $MODEL $HPARAM $PROBLEM_DATA $TRAIN_STEPS $CKPT ${JOBNAME}-${NUM_WORKER}-${MAX_WORKER} $PROFILE $SET_SLOT $MAX_WORKER &
for  i in $(seq 0 $NUM_PS); do
  echo "Starting ${JOBNAME}-ps-${i}..."
  ZONE=`gcloud compute instances list ${JOBNAME}-ps-${i} --format 'csv[no-heading](zone)'`
  gcloud compute ssh ${ROOT}@${JOBNAME}-ps-${i} --zone ${ZONE} -- sudo rm -rf $WORKDIR
  gcloud compute ssh ${ROOT}@${JOBNAME}-ps-${i} --zone ${ZONE} -- sudo mkdir -p $WORKDIR
  gcloud compute ssh ${ROOT}@${JOBNAME}-ps-${i} --zone ${ZONE} -- sudo chmod 777 $WORKDIR
  gcloud compute scp --zone ${ZONE} \
    --recurse \
    /tmp/${JOBNAME}/tf_config.json start_one_time_traning_server.sh \
    root@${JOBNAME}-ps-${i}:$WORKDIR
#  gcloud compute ssh ${ROOT}@${JOBNAME}-ps-${i} --zone ${ZONE} -- $WORKDIR/cpu_util_check.sh $HPARAM &
#  for j in $(seq 0 $NUM_SHARD); do
#    sleep 1s
#  if [[ $i == 0 ]]; then
#    gcloud compute ssh ${ROOT}@$JOBNAME-ps-${i} --zone ${ZONE} -- python /home/ozymandias/proj_code/code/xmlrpc_server.py &
#  fi
  gcloud compute ssh ${ROOT}@$JOBNAME-ps-${i} --zone ${ZONE} -- $WORKDIR/start_one_time_traning_server.sh $DATADIR $OUTDIR 1 $i 0 $NUM_PS $NUM_WORKER $NUM_SHARD $MODEL $HPARAM $PROBLEM_DATA $TRAIN_STEPS $CKPT ${JOBNAME} $PROFILE $SET_SLOT $MAX_WORKER &
#  done
done

ZONE=`gcloud compute instances list $JOBNAME-master --format 'csv[no-heading](zone)'`
#echo $ZONE
gcloud compute ssh ${ROOT}@$JOBNAME-master --zone ${ZONE} -- sudo rm -rf $WORKDIR
gcloud compute ssh ${ROOT}@$JOBNAME-master --zone ${ZONE} -- sudo mkdir -p $WORKDIR
gcloud compute scp --zone ${ZONE} \
    --recurse \
  /tmp/${JOBNAME}/tf_config.json start_one_time_traning_server.sh \
  root@$JOBNAME-master:$WORKDIR

# Start workers in the background
if [[ $NUM_WORKER -ge 0 ]]; then
    for  i in $(seq 0 $NUM_WORKER); do
      echo "Starting ${JOBNAME}-worker-${i}..."
      ZONE=`gcloud compute instances list $JOBNAME-worker-${i} --format 'csv[no-heading](zone)'`
      gcloud compute ssh ${ROOT}@$JOBNAME-worker-${i} --zone ${ZONE} -- sudo rm -rf $WORKDIR
      gcloud compute ssh ${ROOT}@$JOBNAME-worker-${i} --zone ${ZONE} -- sudo mkdir -p $WORKDIR
      gcloud compute scp --zone ${ZONE} \
        --recurse \
        /tmp/${JOBNAME}/tf_config.json start_one_time_traning_server.sh \
        root@$JOBNAME-worker-${i}:$WORKDIR
      gcloud compute ssh ${ROOT}@$JOBNAME-worker-${i} --zone ${ZONE} -- $WORKDIR/start_one_time_traning_server.sh $DATADIR $OUTDIR 2 $i 0 $NUM_PS $NUM_WORKER $NUM_SHARD $MODEL $HPARAM $PROBLEM_DATA $TRAIN_STEPS $CKPT ${JOBNAME} $PROFILE $SET_SLOT $MAX_WORKER &
    done
fi

# Start a master
echo "Starting ${JOBNAME}-master..."
ZONE=`gcloud compute instances list $JOBNAME-master --format 'csv[no-heading](zone)'`
gcloud compute ssh ${ROOT}@$JOBNAME-master --zone ${ZONE} -- $WORKDIR/start_one_time_traning_server.sh $DATADIR $OUTDIR 3 $MASTER_INDEX 0 $NUM_PS $NUM_WORKER $NUM_SHARD $MODEL $HPARAM $PROBLEM_DATA $TRAIN_STEPS $CKPT ${JOBNAME} $PROFILE $SET_SLOT $MAX_WORKER


# Cleanup
echo "Done. Force stop remaining processes."
./stop_one_time_training.sh $JOBNAME $NUM_PS $NUM_WORKER

#ORIGIN=$(gsutil ls $BUCKET/$JOBNAME/export/Servo | tail -1)
#echo ""
#echo "Trained model is stored in $ORIGIN"

popd >/dev/null
