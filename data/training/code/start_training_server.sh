#!/bin/bash

export LD_LIBRARY_PATH=/usr/local/cuda-9.0/extras/CUPTI/lib64:$LD_LIBRARY_PATH
cd tensor2tensor
git pull
cd ~

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

NUM_PS=$(( NUM_PS + 1 ))
NUM_WORKER=$(( NUM_WORKER + 1 ))
MAX_WORKER=$(( MAX_WORKER + 1 ))

if [ $TYPE -eq 1 ]; then
  ROLE="ps"
  INDEX=$(($4+$5))
elif [ $TYPE -eq 2 ]; then
  ROLE="worker"
  INDEX=$4
else
  ROLE="chief"
  INDEX=$4
fi

NUM_SHARD=$(( NUM_SHARD + 1 ))

export TF_CONFIG=$(sed "s/__INDEX__/$INDEX/;s/__ROLE__/$ROLE/" tf_config.json)
export PYTHONPATH="$PWD":"${PYTHONPATH}"

if [[ $TYPE == 1 ]]; then
  t2t-trainer --schedule=run_std_server
elif [[ $TYPE == 2 ]]; then
  IP=`gcloud compute instances list ${JOBNAME}-worker-${INDEX} --format 'csv[no-heading](INTERNAL_IP)'`
#  echo $IP
  echo WORKER: $SET_SLOT
  sleep $(( 10 * $INDEX + 40 ))s
  if [[ $SET_SLOT == 1 ]]; then
    t2t-trainer --master=grpc://${IP}:2222 --data_dir=${DATADIR} --output_dir=${OUTDIR} --ps_replicas=$(( NUM_SHARD * NUM_PS )) --worker_replicas=$(( MAX_WORKER + 1 )) --worker_gpu=1 --worker_id=$(( INDEX + 1 )) --ps_gpu=0 --schedule=train --worker_job='/job:worker' --model=${MODEL} --hparams_set=${HPARAM} --problem=${PROBLEM_DATA} --train_steps=${TRAIN_STEPS} --save_checkpoints_secs=0 --local_eval_frequency=${CKPT} --dbgprofile=${PROFILE}
  else
    t2t-trainer --master=grpc://${IP}:2222 --data_dir=${DATADIR} --output_dir=${OUTDIR} --ps_replicas=$(( NUM_SHARD * NUM_PS )) --worker_replicas=$(( NUM_WORKER + 1 )) --worker_gpu=1 --worker_id=$(( INDEX + 1 )) --ps_gpu=0 --schedule=train --worker_job='/job:worker' --model=${MODEL} --hparams_set=${HPARAM} --problem=${PROBLEM_DATA} --train_steps=${TRAIN_STEPS} --save_checkpoints_secs=0 --local_eval_frequency=${CKPT} --dbgprofile=${PROFILE}
  fi
else
  IP=`gcloud compute instances list ${JOBNAME}-master --format 'csv[no-heading](INTERNAL_IP)'`
#  echo $IP
  echo MASTER: $SET_SLOT
  if [[ $SET_SLOT == 1 ]]; then
    t2t-trainer --master=grpc://${IP}:2222 --data_dir=${DATADIR} --output_dir=${OUTDIR} --ps_replicas=$(( NUM_SHARD * NUM_PS )) --worker_replicas=$(( MAX_WORKER + 1 )) --worker_gpu=1 --worker_id=0 --ps_gpu=0 --schedule=train --worker_job='/job:chief' --model=${MODEL} --hparams_set=${HPARAM} --problem=${PROBLEM_DATA} --train_steps=${TRAIN_STEPS} --save_checkpoints_secs=0 --local_eval_frequency=${CKPT} --dbgprofile=${PROFILE}
  else
    t2t-trainer --master=grpc://${IP}:2222 --data_dir=${DATADIR} --output_dir=${OUTDIR} --ps_replicas=$(( NUM_SHARD * NUM_PS )) --worker_replicas=$(( NUM_WORKER + 1 )) --worker_gpu=1 --worker_id=0 --ps_gpu=0 --schedule=train --worker_job='/job:chief' --model=${MODEL} --hparams_set=${HPARAM} --problem=${PROBLEM_DATA} --train_steps=${TRAIN_STEPS} --save_checkpoints_secs=0 --local_eval_frequency=${CKPT} --dbgprofile=${PROFILE}
  fi
fi