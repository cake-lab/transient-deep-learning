import os
import time
import googleapiclient.discovery
import googleapiclient
import price_monitor
import threading
import paramiko
import sys
from datetime import datetime


PROJECTNAME = "shijian-18"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = '/Users/ozymandias/Desktop/cloudComputing/shijian-18-key.json'
COMPUTE = googleapiclient.discovery.build('compute', 'v1')

class checkStatus(threading.Thread):
    def __init__(self, compute, project, zone, name):
        threading.Thread.__init__(self)
        self.compute = compute
        self.project = project
        self.zone = zone
        self.name = name

    def run(self):
        flag = 1
        while True:
            request = self.compute.instances().get(project=self.project, zone=self.zone, instance=self.name)
            result = request.execute()

            if result['status'] == 'STAGING' and flag == 1:
                if 'error' in result:
                    raise Exception(result['error'])
                flag = 0

            if result['status'] == 'RUNNING' and flag == 0:
                if 'error' in result:
                    raise Exception(result['error'])
                int_ip = result['networkInterfaces'][0]['networkIP']
                ip = result['networkInterfaces'][0]['accessConfigs'][0]['natIP']
                flag = -1
            elif result['status'] == 'RUNNING' and flag != 0:
                os.system(
                    'while true; do foo=$((ssh -q -o UserKnownHostsFile=/dev/null -o CheckHostIP=no -o StrictHostKeyChecking=no -i $HOME/.ssh/google_compute_engine -A -p 22 ozymandias@' + ip + ' "echo 2>&1" && echo SSH_OK || echo SSH_NOK) | tail -n1); if [ $foo == "SSH_OK" ]; then echo SSH SUCCESS; break; else echo SSH FAILED; fi; done')
                return int_ip

            # time.sleep(2)

class ResourceManager(object):

    def create_instance(self, compute, project, zone, name, preemtible, cpu_num, is_gpu, gpu_type):
        while True:
            try:
                if is_gpu:
                    image_response = compute.images().get(project=PROJECTNAME, image='gpu-updated-3').execute()
                    # image_response = compute.images().get(project=PROJECTNAME, image='gpu-custom-tf').execute()
                    source_disk_image = image_response['selfLink']
                    if gpu_type == 'k80':
                        gpu = 'nvidia-tesla-k80'
                        machine_type = "zones/%s/machineTypes/custom-4-62464-ext" % (zone)
                    elif gpu_type == 'v100':
                        gpu = 'nvidia-tesla-v100'
                        machine_type = "zones/%s/machineTypes/custom-8-62464-ext" % (zone)
                    elif gpu_type == 'p100':
                        gpu = 'nvidia-tesla-p100'
                        machine_type = "zones/%s/machineTypes/custom-8-62464-ext" % (zone)
                else:
                    image_response = compute.images().get(project=PROJECTNAME, image='cpu-updated').execute()
                    source_disk_image = image_response['selfLink']
                    machine_type = "zones/%s/machineTypes/custom-%s-16384-ext" % (zone, str(cpu_num))

                # machine_type = "zones/%s/machineTypes/custom-2-8192-ext" % zone
                # if stress != None:
                #     startup_script = open(
                #         os.path.join(
                #         os.path.dirname(__file__), stress), 'r').read()
                # else:
                #     startup_script = None

                if is_gpu:
                    config = {
                        'name': name,
                        'machineType': machine_type,
                        "minCpuPlatform": "Intel Broadwell", #CPU Platform spec
                        'scheduling': [
                            {
                                'preemptible': preemtible,
                                "onHostMaintenance": "terminate",
                            }
                        ],
                        'serviceAccounts': [
                            {
                                "email": "[SERVICE_ACCOUNT_EMAIL]",
                                "scopes": ["https://www.googleapis.com/auth/cloud-platform"]
                            }
                        ],

                        'disks': [
                            {
                                'boot': True,
                                'autoDelete': True,
                                'diskSizeGb': '100',
                                'initializeParams': {
                                    'sourceImage': source_disk_image,
                                }
                            }
                        ],

                        'networkInterfaces': [{
                            'network': 'global/networks/default',
                            'accessConfigs': [
                                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
                            ]
                        }],

                        'serviceAccounts': [{
                            'email': 'default',
                            'scopes': [
                                'https://www.googleapis.com/auth/devstorage.read_write',
                                'https://www.googleapis.com/auth/logging.write',
                                'https://www.googleapis.com/auth/cloud-platform'
                            ]
                        }],

                        "guestAccelerators":
                            [
                                {
                                    "acceleratorCount": 1,
                                    "acceleratorType": "https://www.googleapis.com/compute/v1/projects/" + project + "/zones/" + zone + "/acceleratorTypes/" + gpu
                                }
                            ]

                        # 'metadata': {
                        #     'items': [{
                        #         'key': 'startup-script',
                        #         'value': startup_script
                        #     }]
                        # }
                    }
                else:
                    config = {
                        'name': name,
                        'machineType': machine_type,
                        "minCpuPlatform": "Intel Broadwell",
                        'scheduling': [
                            {
                                'preemptible': preemtible,
                                "onHostMaintenance": "terminate",
                            }
                        ],
                        'serviceAccounts': [
                            {
                                "email": "[SERVICE_ACCOUNT_EMAIL]",
                                "scopes": ["https://www.googleapis.com/auth/cloud-platform"]
                            }
                        ],

                        'disks': [
                            {
                                'boot': True,
                                'autoDelete': True,
                                'diskSizeGb': '100',
                                'initializeParams': {
                                    'sourceImage': source_disk_image,
                                }
                            }
                        ],

                        'networkInterfaces': [{
                            'network': 'global/networks/default',
                            'accessConfigs': [
                                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
                            ]
                        }],

                        'serviceAccounts': [{
                            'email': 'default',
                            'scopes': [
                                'https://www.googleapis.com/auth/devstorage.read_write',
                                'https://www.googleapis.com/auth/logging.write',
                                'https://www.googleapis.com/auth/cloud-platform'
                            ]
                        }]

                        # 'metadata': {
                        #     'items': [{
                        #         'key': 'startup-script',
                        #         'value': startup_script
                        #     }]
                        # }
                    }

                return compute.instances().insert(
                    project=project,
                    zone=zone,
                    body=config).execute()
            except googleapiclient.errors.HttpError as e:
                print "Error occured when creating instance", e
                pass

    def check_instance_status(self, compute, project, zone, name):
        while True:
            request = compute.instances().get(project=project, zone=zone, instance=name)
            result = request.execute()
            home_var = os.environ['HOME']

            if result['status'] == 'RUNNING':
                command = "echo VM READY"
                username = "ozymandias"
                int_ip = result['networkInterfaces'][0]['networkIP']
                ip = result['networkInterfaces'][0]['accessConfigs'][0]['natIP']
                port = 22
                client = paramiko.SSHClient()
                client.load_system_host_keys()
                client.set_missing_host_key_policy(paramiko.WarningPolicy)
                while True:
                    try:
                        client.connect(ip, port=port, username=username, password=None,
                                       key_filename=home_var+"/.ssh/google_compute_engine")

                        stdin, stdout, stderr = client.exec_command(command)
                        print stdout.read(),
                        break
                    except (paramiko.ssh_exception.BadHostKeyException, paramiko.ssh_exception.AuthenticationException,
                            paramiko.ssh_exception.SSHException, paramiko.ssh_exception.socket.error) as e:
                        print "Retrying SSH to VM"
                        time.sleep(1)
                client.close()
                return int_ip, ip

            # time.sleep(0.001)

    def acquire_resource(self, job_name, num_of_ps, ps_core_num, num_of_worker, limit, zone=None, gpu_type='k80'):

        worker_core_num = 4

        limit = limit
        j = 0

        result = {}
        ps_list = []
        worker_list = []
        master_list = []
        job_name = job_name

        if num_of_worker >= 1:

            vm = {}
            name = job_name + "-master"
            vm['name'] = name
            vm['zone'] = zone
            vm['role'] = "master"
            vm['creation_time'] = datetime.now()
            master_list.append(vm)
            self.create_instance(COMPUTE, PROJECTNAME, zone, name, False, worker_core_num, True, gpu_type)

            j += 1
            limit -= 1

        while j < num_of_worker:
            vm = {}
            tmp = j-1
            name = job_name + "-worker-%d" % tmp
            vm['name'] = name
            vm['zone'] = zone
            vm['role'] = "worker"
            vm['creation_time'] = datetime.now()
            worker_list.append(vm)
            self.create_instance(COMPUTE, PROJECTNAME, zone, name, False, worker_core_num, True, gpu_type)

            j += 1
            limit -= 1

        for i in range(num_of_ps):
            vm = {}
            name = job_name + "-ps-%d" % i
            vm['role'] = "ps"
            vm['name'] = name
            vm['zone'] = zone
            vm['creation_time'] = datetime.now()
            ps_list.append(vm)
            self.create_instance(COMPUTE, PROJECTNAME, zone, name, False, ps_core_num, False, None)


        for vm in ps_list:
            vm['int_ip'], vm['ip'] = self.check_instance_status(COMPUTE, PROJECTNAME, vm['zone'], vm['name'])

        for vm in master_list:
            vm['int_ip'], vm['ip'] = self.check_instance_status(COMPUTE, PROJECTNAME, vm['zone'], vm['name'])

        for vm in worker_list:
            vm['int_ip'], vm['ip'] = self.check_instance_status(COMPUTE, PROJECTNAME, vm['zone'], vm['name'])

        result['master'] = master_list
        result['workers'] = worker_list
        result['ps'] = ps_list

        return result

    def acquire_hetero_resource(self, preemtible, job_name, num_of_ps, ps_core_num, num_of_worker, limit, gpu_array, zone_array):


        worker_core_num = 4

        limit = limit
        j = 0

        result = {}
        ps_list = []
        worker_list = []
        master_list = []

        job_name = job_name

        if num_of_worker >= 1:

            vm = {}
            name = job_name + "-master"
            vm['name'] = name
            vm['zone'] = zone_array[j]
            vm['role'] = "master"
            vm['creation_time'] = datetime.now()
            master_list.append(vm)
            self.create_instance(COMPUTE, PROJECTNAME, zone_array[j], name, preemtible, worker_core_num, True, gpu_array[j])

            j += 1
            limit -= 1

        while j < num_of_worker:
            vm = {}

            tmp = j-1
            name = job_name + "-worker-%d" % tmp
            vm['name'] = name
            vm['zone'] = zone_array[j]
            vm['role'] = "worker"
            vm['creation_time'] = datetime.now()
            worker_list.append(vm)
            self.create_instance(COMPUTE, PROJECTNAME, zone_array[j], name, preemtible, worker_core_num, True, gpu_array[j])

            j += 1
            limit -= 1


        for i in range(num_of_ps):
            vm = {}
            name = job_name + "-ps-%d" % i
            vm['role'] = "ps"
            vm['name'] = name
            vm['zone'] = zone_array[-1-i]
            vm['creation_time'] = datetime.now()
            ps_list.append(vm)
            self.create_instance(COMPUTE, PROJECTNAME, False, zone_array[-1-i], name, False, ps_core_num, False, None)


        for vm in ps_list:
            vm['int_ip'], vm['ip'] = self.check_instance_status(COMPUTE, PROJECTNAME, vm['zone'], vm['name'])

        for vm in master_list:
            vm['int_ip'], vm['ip'] = self.check_instance_status(COMPUTE, PROJECTNAME, vm['zone'], vm['name'])

        for vm in worker_list:
            vm['int_ip'], vm['ip'] = self.check_instance_status(COMPUTE, PROJECTNAME, vm['zone'], vm['name'])

        result['master'] = master_list
        result['workers'] = worker_list
        result['ps'] = ps_list

        return result
