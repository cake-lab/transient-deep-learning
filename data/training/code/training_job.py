import googleapiclient.discovery
import googleapiclient
from datetime import datetime
import os
import time
import argparse
import sys
import subprocess
import threading
import paramiko
import resource_acquisition
from datastore import StatusDAO as dao

PROJECTNAME = "shijian-18"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = '/Users/ozymandias/Desktop/cloudComputing/shijian-18-key.json'
COMPUTE = googleapiclient.discovery.build('compute', 'v1')
IS_CREATING = False
JOB_DONE = 0
CURRENT_RUN = 0
CAN_CREATE_JOB = False
STOPPING_CLUSTER = False

def main(job_name, num_ps, num_worker, run_num, preemptible=True, db=None, zone_array=None, gpu_array=None):
    global CURRENT_RUN
    global CAN_CREATE_JOB
    print db
    CURRENT_RUN = run_num
    model = 'resnet'
    hparam = 'resnet_cifar_32_vanilla'
    problem = 'image_cifar10'
    bucket_dir = 'gs://shijian-18-ml/30-cluster'
    num_ps_core = '4'
    train_steps = '64000'
    ckpt_frequency = '4000'
    zone = zone
    profile = '0'

    thread2 = monitor_thread(job_name, zone, db)
    thread2.start()
    threads = []

    while JOB_DONE < 15:
        if CAN_CREATE_JOB:
            CAN_CREATE_JOB = False
            thread_1 = job_thread(False, preemptible, job_name + zone + '-run'+str(CURRENT_RUN), num_ps, num_ps_core, num_worker, bucket_dir, model, hparam,
                                 problem, train_steps, ckpt_frequency, '1', profile, 100, eval_zone, db, gpu_array, zone_array)
            threads.append(thread_1)
            thread_1.start()

class monitor_thread(threading.Thread):
    def __init__(self, job_name, region, db):
        super(monitor_thread, self).__init__()
        self.region = region
        self.job_name = job_name
        # self.worker_up_array = [1,1,1] #######
        self.monitor = dao(db)

    def run(self):
        global IS_CREATING
        global JOB_DONE
        global CAN_CREATE_JOB
        global CURRENT_RUN
        global STOPPING_CLUSTER
        while JOB_DONE < 15:
            job_name = self.job_name + self.region + '-run' + str(CURRENT_RUN) #######
            result = self.check_db(job_name, 'RUNNING', 'master') or self.check_db(job_name, 'PROVISIONING', 'master') or self.check_db(job_name, 'STAGING', 'master')
            if not STOPPING_CLUSTER:
                if len(result) != 0 and not IS_CREATING:
                    print 'Job running'
                    for i in range(3): #######
                        if self.worker_up_array[i] == 1:
                            worker_status = self.check_status(job_name+'-worker-'+str(i), self.region)
                            if worker_status['status'] == 'STOPPING' or worker_status['status'] == 'TERMINATED':
                                self.monitor.update_entry(job_name + '-worker-'+str(i), 'TERMINATED', datetime.now(), 'Revoked')
                                self.worker_up_array[i] = 0
                                print 'Worker' + str(i) + ' is stopping'
                    master_status = self.check_status(job_name + '-master', self.region)
                    if master_status['status'] == 'STOPPING' or master_status['status'] == 'TERMINATED':
                        self.monitor.update_entry(job_name + '-master', 'TERMINATED', datetime.now(), 'Revoked')
                        print 'Master down, terminating cluster'
                        self.stop_cluster(job_name, 'Manually stopped due to revoked master')
                        print 'Termination done'
                elif len(result) == 0 and not IS_CREATING:
                    print 'Currently no job is running, creating new job'
                    CAN_CREATE_JOB = True
                elif IS_CREATING:
                    print 'Job is being created'
                else:
                    print 'result:', result
                    print 'is_creating', IS_CREATING
                    print 'can_create_job', CAN_CREATE_JOB
            time.sleep(10)

        print 'All jobs finished, terminating monitor'

    def stop_cluster(self, job_name, reason):
        global STOPPING_CLUSTER
        global JOB_DONE
        global CURRENT_RUN
        STOPPING_CLUSTER = True
        done = [1,1,1] #######
        self.retry_stop(self.region, job_name + '-ps-0')
        self.retry_stop(self.region, job_name + '-master')
        self.monitor.update_entry(job_name + '-master', 'TERMINATED', datetime.now(), reason)
        self.retry_stop('asia-east1-a', job_name + '-evaluator')
        for i in range(3): #######
            if self.worker_up_array[i] == 1:
                self.retry_stop(self.region, job_name+'-worker-'+str(i))
                self.monitor.update_entry(job_name + '-worker-' + str(i), 'TERMINATED', datetime.now(), reason)
        while done != [0,0,0]: #######
            print 'Stopping whole cluster, please stand by'
            ps_status = self.check_status(job_name + '-ps-0', self.region)
            master_status = self.check_status(job_name + '-master', self.region)
            eval_status = self.check_status(job_name + '-evaluator', 'asia-east1-a')
            if ps_status['status'] == 'TERMINATED':
                done[1] = 0
            if master_status['status'] == 'TERMINATED':
                done[0] = 0
            for i in range(1): #######
                worker_status = self.check_status(job_name + '-worker-'+str(i), self.region)
                if worker_status['status'] == 'TERMINATED':
                    done[i+2] = 0
            if eval_status['status'] == 'TERMINATED':
                done[-1] = 0

            time.sleep(10)
        JOB_DONE += 1
        CURRENT_RUN += 1
        STOPPING_CLUSTER = False

    def check_status(self, vm_name, zone):
        while True:
            try:
                request = COMPUTE.instances().get(project=PROJECTNAME, zone=zone, instance=vm_name)
                response = request.execute()
            except:
                continue
            break
        return response

    def retry_stop(self, zone, instance):
        while True:
            try:
                COMPUTE.instances().stop(project=PROJECTNAME, zone=zone, instance=instance).execute()
            except:
                continue
            break

    def check_db(self, job_name, status, role):
        result = self.monitor.select_running_host_by_region(job_name, self.region, status, role)
        return result

class job_thread(threading.Thread):
    def __init__(self,train_only, preemptible, job_name, num_ps, ps_core_num, num_worker, bucket_dir, model, hparam_set, problem, train_steps, ckpt_frequency, run_num, profile, limit, zone, eval_zone, db, gpu):
        super(job_thread, self).__init__()
        self.preemptible = preemptible
        self.train_only = train_only
        self.job_name = job_name
        self.num_ps = num_ps
        self.num_worker = num_worker
        self.ps_core_num = ps_core_num
        self.bucket_dir = bucket_dir
        self.model = model
        self.hparam_set = hparam_set
        self.problem = problem
        self.train_steps = train_steps
        self.ckpt_frequency = ckpt_frequency
        self.run_num = str(run_num)
        self.profile = profile
        self.limit = limit
        self.zone_array = zone_array
        self.eval_zone = eval_zone
        self.monitor = dao(db)
        self.gpu_array = gpu_array

    def run(self):
        global IS_CREATING
        IS_CREATING = True
        self.create_eval()
        self.start_job()

    def check_status(self, vm_name, zone):
        while True:
            try:
                request = COMPUTE.instances().get(project=PROJECTNAME, zone=zone, instance=vm_name)
                response = request.execute()
            except:
                continue
            break
        return response

    def retry_stop(self, zone, instance):
        while True:
            try:
                COMPUTE.instances().stop(project=PROJECTNAME, zone=zone, instance=instance).execute()
            except:
                continue
            break

    def stop_cluster(self, job_name, reason):
        global STOPPING_CLUSTER
        global JOB_DONE
        global CURRENT_RUN
        STOPPING_CLUSTER = True
        done = [1,1,1] #######
        self.retry_stop(self.zone, job_name + '-ps-0')
        self.monitor.update_entry(job_name + '-master', 'TERMINATED', datetime.now(), reason)
        self.retry_stop(self.zone, job_name + '-master')
        self.retry_stop('asia-east1-a', job_name + '-evaluator')
        for i in range(3): #######
            worker_status = self.check_status(job_name + '-worker-' + str(i), self.zone)
            if worker_status['status'] != 'TERMINATED' and worker_status['status'] != 'STOPPING':
                self.monitor.update_entry(job_name + '-worker-' + str(i), 'TERMINATED', datetime.now(), reason)
                self.retry_stop(self.zone, job_name + '-worker-' + str(i))
        while done != [0,0,0]: #######
            print 'Stopping whole cluster, please stand by'
            ps_status = self.check_status(job_name + '-ps-0', self.zone)
            master_status = self.check_status(job_name + '-master', self.zone)
            eval_status = self.check_status(job_name + '-evaluator', 'asia-east1-a')
            if ps_status['status'] == 'TERMINATED':
                done[1] = 0
            if master_status['status'] == 'TERMINATED':
                done[0] = 0
            for i in range(3): #######
                worker_status = self.check_status(job_name + '-worker-'+str(i), self.zone)
                if worker_status['status'] == 'TERMINATED':
                    done[i+2] = 0
            if eval_status['status'] == 'TERMINATED':
                done[-1] = 0
        JOB_DONE += 1
        CURRENT_RUN += 1
        STOPPING_CLUSTER = False

    def start_job(self):
        job = resource_acquisition.ResourceManager()
        global IS_CREATING
        global CURRENT_RUN
        worker_temp = str(int(self.num_worker) - 1)
        if not self.train_only:
            server_lists = job.acquire_hetero_resource(self.preemptible, self.job_name, int(self.num_ps), int(self.ps_core_num), int(self.num_worker), self.limit, gpu_array, zone_array)
            self.add_vm_to_db(server_lists, 'master', 0)
            for i in range(int(worker_temp)):
                self.add_vm_to_db(server_lists, 'workers', i)
            IS_CREATING = False
        subprocess.call(
            ["./start_one_time_training.sh", self.job_name, self.num_ps, worker_temp, '1', self.bucket_dir, self.model, self.hparam_set,
             self.problem, self.train_steps, self.ckpt_frequency, '0', self.run_num, self.profile])
        master_status = self.check_status(self.job_name + '-master', self.zone)
        if master_status['status'] == 'RUNNING':
            self.stop_cluster(self.job_name, 'Job completed')
        return

    def add_vm_to_db(self, server_lists, role, index):
        int_ip = self.get_ip_from_vm(server_lists, role, index)
        self.monitor.add_host(server_lists[role][index]['name'], int_ip, self.job_name, self.zone,
                         server_lists[role][index]['creation_time'], role)

    def get_ip_from_vm(self, server_lists, role, index):
        request = COMPUTE.instances().get(project=PROJECTNAME, zone=self.zone, instance=server_lists[role][index]['name'])
        result = request.execute()
        int_ip = result['networkInterfaces'][0]['networkIP']
        return int_ip

    def create_eval(self):
        job = resource_acquisition.ResourceManager()
        vm_name = self.job_name + '-evaluator'
        job.create_instance(COMPUTE, PROJECTNAME, self.eval_zone, vm_name, False, '4', True, 'k80')
        job.check_instance_status(COMPUTE, PROJECTNAME, self.eval_zone, vm_name)
        os.system(
            'gcloud compute scp --zone ' + self.eval_zone + ' --recurse start-evaluator.sh ozymandias@' + self.job_name + '-evaluator:~')
        os.system(
            'gcloud compute ssh ozymandias@' + self.job_name + '-evaluator --zone ' + self.eval_zone + ' -- bash start-evaluator.sh ' + self.job_name + ' &')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--job_name',
        type=str,
        required=True,
        help='Job name')
    parser.add_argument(
        '--num-ps',
        type=str,
        required=True,
        help='Number of parameter servers')
    parser.add_argument(
        '--num-worker',
        type=str,
        required=True,
        help='Number of workers')
    parser.add_argument(
        '--zone',
        type=str,
        required=True,
        help='Which zone to use for cluster')
    parser.add_argument(
            '--run-num',
            type=int,
            required=True,
            help='Number of runs')
    parser.add_argument(
        '--db',
        type=str,
        help='Target database')
    parser.add_argument(
        '--gpu',
        type=str,
        help='GPU type')
    parser.add_argument(
        '--preemptible',
        type=bool,
        help='Use transient')
    parser.add_argument(
        '--eval-zone',
        type=str,
        required=True,
        help='Which zone to use for evaluator')
    parser.add_argument(
        '--train-only',
        type=bool,
        default=False,
        help='Use existing cluster')
    parser.add_argument(
        '--zone-array',
        type=str,
        required=True,
        help='Zones to use for training cluster')
    parser.add_argument(
        '--gpu-array',
        type=str,
        required=True,
        help='GPU to use for individual workers')
    args = parser.parse_args()

    main(**vars(args))