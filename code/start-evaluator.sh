#!/bin/bash

export LD_LIBRARY_PATH=/usr/local/cuda-9.0/extras/CUPTI/lib64:$LD_LIBRARY_PATH
cd tensor2tensor
git pull
cd ~

cd $(dirname $0)
OUTDIR=$1
DATADIR=$2
MODEL=$3
HPARAM=$4
PROBLEM_DATA=$5
TRAIN_STEPS=$6
CKPT=$7
JOBNAME=$8

t2t-trainer \
    --worker_job='/job:localhost' \
    --data_dir=gs://shijian-18-ml/cifar_data \
    --output_dir=gs://shijian-18-ml/30-cluster/${OUTDIR} \
    --schedule=continuous_eval \
    --model=resnet \
    --problem=image_cifar10 \
    --hparams_set=resnet_cifar_32_vanilla