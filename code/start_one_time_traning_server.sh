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

#export LD_LIBRARY_PATH=/usr/local/cuda-9.0/extras/CUPTI/lib64:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda-9.0/lib64/
export PATH=$PATH:/snap/bin
export PATH=/home/ozymandias/.local/bin:$PATH
#which t2t-trainer
#echo $PATH
#cat /home/ozymandias/.local/bin/t2t-trainer
#cd tensor2tensor
#git pull
#cd ~

WORKDIR=/tmp/workdir

cd $(dirname $0)
DATADIR=$1
OUTDIR=$2
TYPE=$3
IND=$4
SHARD_IND=$5
NUM_PS=$6
NUM_WORKER=$7
NUM_SHARD=$8
MODEL=$9
HPARAM=${10}
PROBLEM_DATA=${11}
TRAIN_STEPS=${12}
CKPT=${13}
JOBNAME=${14}
if [ ${15} -eq 1 ]; then
    PROFILE=True
else
    PROFILE=False
fi
SET_SLOT=${16}
MAX_WORKER=${17}
DEBUG=${18}

if [ $TYPE -eq 1 ]; then
  ROLE="ps"
  INDEX=$(($4+$5))
  touch train_config.txt
  echo ${DATADIR} >> train_config.txt
  echo ${OUTDIR} >> train_config.txt
  echo ${NUM_PS} >> train_config.txt
  echo ${NUM_WORKER} >> train_config.txt
  echo ${NUM_SHARD} >> train_config.txt
  echo ${MODEL} >> train_config.txt
  echo ${HPARAM} >> train_config.txt
  echo ${PROBLEM_DATA} >> train_config.txt
  echo ${TRAIN_STEPS} >> train_config.txt
  echo ${CKPT} >> train_config.txt
  echo ${JOBNAME} >> train_config.txt
  if [ "$PROFILE" == "True" ]; then
    echo 1 >> train_config.txt
  else
    echo 0 >> train_config.txt
  fi
  echo ${SET_SLOT} >> train_config.txt
  echo ${MAX_WORKER} >> train_config.txt
elif [ $TYPE -eq 2 ]; then
  ROLE="worker"
  INDEX=$4
else
  ROLE="chief"
  INDEX=$4
fi

NUM_PS=$(( NUM_PS + 1 ))
NUM_WORKER=$(( NUM_WORKER + 1 ))
MAX_WORKER=$(( MAX_WORKER + 1 ))
#echo THIS IS THE INDEX OF SHARD $SHARD_IND
#echo THIS IS THE NUMBER OF SHARD $NUM_SHARD
#echo THIS IS THE NUMBER OF WORKERS $NUM_WORKER
#echo THIS IS THE NUMBER OF PS $NUM_PS

NUM_SHARD=$(( NUM_SHARD + 1 ))

export TF_CONFIG=$(sed "s/__INDEX__/$INDEX/;s/__ROLE__/$ROLE/" tf_config.json)
export PYTHONPATH="$PWD":"${PYTHONPATH}"

if [[ $DEBUG == 1 ]]; then
  echo DEBUGGING LOGS
  echo $TF_CONFIG
  echo $SET_SLOT
  echo --master=grpc://${IP}:2222 --data_dir=${DATADIR} --output_dir=${OUTDIR} --ps_replicas=$(( NUM_SHARD * NUM_PS )) --worker_replicas=$(( MAX_WORKER + 1 )) --worker_gpu=1 --worker_id=$(( INDEX + 1 )) --ps_gpu=0 --schedule=train --worker_job='/job:worker' --model=${MODEL} --hparams_set=${HPARAM} --problem=${PROBLEM_DATA} --train_steps=${TRAIN_STEPS} --save_checkpoints_secs=0 --local_eval_frequency=${CKPT} --dbgprofile=${PROFILE}

fi

if [[ $TYPE == 1 ]]; then
#  echo This is a PS
  t2t-trainer --schedule=run_std_server
elif [[ $TYPE == 2 ]]; then
#  echo This is a worker
  IP=`gcloud compute instances list ${JOBNAME}-worker-${INDEX} --format 'csv[no-heading](INTERNAL_IP)'`
#  echo $IP
#  echo WORKER: $SET_SLOT
#  sleep $(( 10 * $INDEX ))s
#  sleep $(( 10 * $INDEX + 30 ))s
#  sudo python /home/ozymandias/proj_code/code/spotTrain/startup.py
  if [[ $SET_SLOT == 1 ]]; then
    t2t-trainer --master=grpc://${IP}:2222 --data_dir=${DATADIR} --output_dir=${OUTDIR} --ps_replicas=$(( NUM_SHARD * NUM_PS )) --worker_replicas=$(( MAX_WORKER + 1 )) --worker_gpu=1 --worker_id=$(( INDEX + 1 )) --ps_gpu=0 --schedule=train --worker_job='/job:worker' --model=${MODEL} --hparams_set=${HPARAM} --problem=${PROBLEM_DATA} --train_steps=${TRAIN_STEPS} --save_checkpoints_secs=0 --local_eval_frequency=${CKPT} --dbgprofile=${PROFILE}
  else
    t2t-trainer --master=grpc://${IP}:2222 --data_dir=${DATADIR} --output_dir=${OUTDIR} --ps_replicas=$(( NUM_SHARD * NUM_PS )) --worker_replicas=$(( NUM_WORKER + 1 )) --worker_gpu=1 --worker_id=$(( INDEX + 1 )) --ps_gpu=0 --schedule=train --worker_job='/job:worker' --model=${MODEL} --hparams_set=${HPARAM} --problem=${PROBLEM_DATA} --train_steps=${TRAIN_STEPS} --save_checkpoints_secs=0 --local_eval_frequency=${CKPT} --dbgprofile=${PROFILE}
  fi
else
#  echo This is the master
  IP=`gcloud compute instances list ${JOBNAME}-master --format 'csv[no-heading](INTERNAL_IP)'`
#  echo $IP
#  echo MASTER: $SET_SLOT
#  sudo python /home/ozymandias/proj_code/code/spotTrain/startup.py
  if [[ $SET_SLOT == 1 ]]; then
    t2t-trainer --master=grpc://${IP}:2222 --data_dir=${DATADIR} --output_dir=${OUTDIR} --ps_replicas=$(( NUM_SHARD * NUM_PS )) --worker_replicas=$(( MAX_WORKER + 1 )) --worker_gpu=1 --worker_id=0 --ps_gpu=0 --schedule=train --worker_job='/job:chief' --model=${MODEL} --hparams_set=${HPARAM} --problem=${PROBLEM_DATA} --train_steps=${TRAIN_STEPS} --save_checkpoints_secs=0 --local_eval_frequency=${CKPT} --dbgprofile=${PROFILE}
  else
    t2t-trainer --master=grpc://${IP}:2222 --data_dir=${DATADIR} --output_dir=${OUTDIR} --ps_replicas=$(( NUM_SHARD * NUM_PS )) --worker_replicas=$(( NUM_WORKER + 1 )) --worker_gpu=1 --worker_id=0 --ps_gpu=0 --schedule=train --worker_job='/job:chief' --model=${MODEL} --hparams_set=${HPARAM} --problem=${PROBLEM_DATA} --train_steps=${TRAIN_STEPS} --save_checkpoints_secs=0 --local_eval_frequency=${CKPT} --dbgprofile=${PROFILE}
  fi
fi