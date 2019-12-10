gsutil cp gs://shijian-18-ml/resnet32-4/model.ckpt-0.data-00000-of-00001 gs://shijian-18-ml/resnet32-4-copy/
gsutil cp gs://shijian-18-ml/resnet32-4/model.ckpt-0.index gs://shijian-18-ml/resnet32-4-copy/
gsutil cp gs://shijian-18-ml/resnet32-4/model.ckpt-0.meta gs://shijian-18-ml/resnet32-4-copy/

gsutil cp --recurse gs://shijian-18-ml/cifar gs://shijian-18-ml/30-cluster/

## Finished

us-east1-c run1, run2, run3, run4, run5, run6, run7, run8
us-west1-b run1, run2, run3, run5, run6, run7, run8
europe-west1-b run1, run2, run3, run4, run5, run6, run7, run8
us-central1-c run1, run2, run3, run4, run5, run6, run7, run8

## Problematic runs

us-central1-c run5(Not in DB)

## Retrying

us-west1-b run2
europe-west1-b 
us-central1-c 

## Revoc

us-west1-b-run2-worker-2 2019-02-12 16:32:41.164458
us-west1-b-run2-worker-0 2019-02-12 16:33:47.731902
us-east1-c-run3-worker-0 2019-02-12 12:20:33.351
europe-west1-b-run3-worker-0 2019-02-12 13:00:57.800313
us-west1-b-run7-worker-0 2019-02-12 13:37:40.958104
us-central1-c-run3-worker-0 2019-02-12 14:20:48.230392
us-central1-c-run8-worker-1 2019-02-12 14:48:20.667359
us-west1-b-run8-worker-2 2019-02-12 14:53:52.577811
us-central1-c-run4-worker-0 2019-02-12 15:29:53.777
us-central1-c-run4-worker-1 2019-02-12 15:29:21.426649
us-central1-c-run5-worker-0 2019-02-12 16:51:09.432099
us-west1-b-run4-worker-0 2019-02-12 17:05:09.77864

## Down time

us-west2-b-run2-master0 2019-02-12 18:14:23.453
us-west2-b-run2-worker1 2019-02-12 18:14:40.076