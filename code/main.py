import os
import argparse
import sys
import subprocess
import time
import googleapiclient.discovery
import googleapiclient
import resource_acquisition
import threading
import paramiko

COMPUTE = googleapiclient.discovery.build('compute', 'v1')

def main(proj_name, cred_path, job_name, num_ps, ps_core_num, num_worker, num_shard, bucket_dir, model, hparam_set, problem, train_steps, ckpt_frequency, automation_test, profile, limit, setSlot, maxWorker, zone=None, gpu=None, hetero, gpu_array=None, zone_array=None):
    PROJECTNAME = proj_name
    if os.path.exists(cred_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
    else:
        print("Please provide a valid credential path.")
        return
    job = resource_acquisition.ResourceManager()
    if hetero = '1':
        server_lists = job.acquire_hetero_resource(proj_name, cred_path, job_name, int(num_ps), int(ps_core_num), int(num_worker), limit, gpu_array, zone_array)
    else:
        server_lists = job.acquire_resource(proj_name, cred_path, job_name, int(num_ps), int(ps_core_num), int(num_worker), limit, zone=zone, gpu_type=gpu)
    worker_temp = str(int(num_worker)-1)
    subprocess.call(
        ["./start_one_time_training.sh", job_name, num_ps, worker_temp, num_shard, bucket_dir, model, hparam_set,
         problem, train_steps, ckpt_frequency, automation_test, '0', str(profile), str(setSlot), str(maxWorker)])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--proj-name',
        type=str,
        required=True,
        help='The name for your GCE project.')
    parser.add_argument(
        '--cred-path',
        type=str,
        required=True,
        help='GCE credential.')
    parser.add_argument(
        '--job-name',
        type=str,
        required=True,
        help='The name for your deep learning job.')
    parser.add_argument(
        '--num-ps',
        type=str,
        required=True,
        help='Number of parameter servers to be used for training.')
    parser.add_argument(
        '--ps-core-num',
        type=str,
        required=True,
        help='Number of vCPU cores per parameter servers.')
    parser.add_argument(
        '--num-worker',
        type=str,
        required=True,
        help='Number of workers to be used for training.')
    parser.add_argument(
        '--num-shard',
        type=str,
        required=True,
        help='Number of shards the parameter files should be partitioned into.')
    parser.add_argument(
        '--bucket-dir',
        type=str,
        required=True,
        default="gs://shijian-18-ml",
        help='Source bucket of external storage.')
    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Deep neural network to be trained.')
    parser.add_argument(
        '--hparam-set',
        type=str,
        required=True,
        help='Hyperparameter for the model.')
    parser.add_argument(
        '--problem',
        type=str,
        required=True,
        help='Problem dataset to be trained on.')
    parser.add_argument(
        '--train-steps',
        type=str,
        required=True,
        help='How many steps to train the model.')
    parser.add_argument(
        '--ckpt-frequency',
        type=str,
        required=True,
        help='How frequent to dump checkpoint files.')
    parser.add_argument(
        '--automation-test',
        type=str,
        required=False,
        default='0',
        help='Enter 1 for test.')
    parser.add_argument(
        '--profile',
        type=int,
        required=False,
        default=0,
        help='Enter 1 to profile the training session.')
    parser.add_argument(
        '--limit',
        type=int,
        required=False,
        default=8,
        help='How many workers the primary region can support.')
    parser.add_argument(
        '--setSlot',
        type=str,
        required=False,
        default='0',
        help='Whether to set the sparse mapping slots. 1 to apply.')
    parser.add_argument(
        '--maxWorker',
        type=int,
        required=False,
        default=8,
        help='Number of potential workers.')
    parser.add_argument(
        '--zone',
        type=str,
        required=True,
        help='Which zone to run.')
    parser.add_argument(
        '--gpu',
        type=str,
        required=False,
        help='What GPU to use for initial workers.')
    parser.add_argument(
        '--hetero',
        type=str,
        required=False,
        help='Enter 1 for heterogeneous cluster.')
    parser.add_argument(
        '--gpu-array',
        type=str,
        required=False,
        nargs='+',
        help='What GPUs to use for initial workers.')
    parser.add_argument(
        '--zone-array',
        type=str,
        nargs='+',
        required=False,
        help='What zones to use for initial workers.')    
    # parser.add_argument(
    #     '--data-dir',
    #     type=str,
    #     required=True,
    #     help='The directory where the input data is stored.')
    # parser.add_argument(
    #     '--job-dir',
    #     type=str,
    #     required=True,
    #     help='The directory where the model will be stored.')
    args = parser.parse_args()

    main(**vars(args))