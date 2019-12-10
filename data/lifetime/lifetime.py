import argparse
import os
import time
import subprocess
import csv
import googleapiclient.discovery
import googleapiclient
import paramiko
import paramiko.ssh_exception

from six.moves import input

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = '/Users/ozymandias/Desktop/cloudComputing/shijian-18-key.json'
compute = googleapiclient.discovery.build('compute', 'v1')
projectName = "shijian-18"

def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items']

def delete_instance(compute, project, zone, name):
    return compute.instances().delete(
        project=project,
        zone=zone,
        instance=name).execute()

def create_instance(compute, project, zone, name, preemtible, stress=None):
    # image_response = compute.images().getFromFamily(
        # project='debian-cloud', family='debian-9').execute()
    image_response = compute.images().getFromFamily(
        project='ubuntu-os-cloud', family='ubuntu-1604-lts').execute()
    source_disk_image = image_response['selfLink']


    machine_type = "zones/%s/machineTypes/n1-standard-4" % zone
    if stress != None:
        startup_script = open(
            os.path.join(
            os.path.dirname(__file__), stress), 'r').read()
    else:
        startup_script = None

    config = {
        'name': name,
        'machineType': machine_type,
        'scheduling': [
            {
                'preemptible': preemtible
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

        # 'networkInterfaces': [{
        #     'network': 'global/networks/default'
        # }],

        'serviceAccounts': [{
            'email': 'default',
            'scopes': [
                'https://www.googleapis.com/auth/devstorage.read_write',
                'https://www.googleapis.com/auth/logging.write',
                'https://www.googleapis.com/auth/cloud-platform'
            ]
        }],

        'metadata': {
            'items': [{
                'key': 'startup-script',
                'value': startup_script
            }]
        }
    }

    return compute.instances().insert(
        project=project,
        zone=zone,
        body=config).execute()

def gpu_instance(compute, project, zone, name, preemtible, gpu, stress=None):
    # image_response = compute.images().getFromFamily(
        # project='ubuntu-os-cloud', family='ubuntu-1604-lts').execute()
    image_response = compute.images().get(project=projectName, image='gpu-template').execute()
    source_disk_image = image_response['selfLink']


    machine_type = "zones/%s/machineTypes/custom-8-62464-ext" % zone
    if stress != None:
        startup_script = open(
            os.path.join(
            os.path.dirname(__file__), stress), 'r').read()
    else:
        startup_script = None
    if gpu == 'k80':
        gpu_type = 'nvidia-tesla-k80'
    elif gpu == 'p100':
        gpu_type = 'nvidia-tesla-p100'
    else:
        gpu_type = 'nvidia-tesla-v100'

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
            # 'networkIP': '10.142.0.24',
            'accessConfigs': [
                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
            ]
        }],

        # 'networkInterfaces': [{
        #     'network': 'global/networks/default'
        # }],

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
                "acceleratorType": "https://www.googleapis.com/compute/v1/projects/"+project+"/zones/"+zone+"/acceleratorTypes/"+gpu_type
            }
        ],

        'metadata': {
            'items': [{
                'key': 'startup-script',
                'value': startup_script
            }]
        }
    }

    return compute.instances().insert(
        project=project,
        zone=zone,
        body=config).execute()

def wait_for_operation(compute, project, zone, operation):
    then = time.time() * 1000
    # print 'Starting operation: ', then
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation).execute()

        if result['status'] == 'DONE':
            now = time.time() * 1000
            print "done: ", now
            if 'error' in result:
                raise Exception(result['error'])
            print 'Time elapse: ', now - then
            return result

        time.sleep(0.001)

def check_instance_status(compute, project, zone, name):
    then = time.time() * 1000
    flag = 1
    # print 'Initial timestamp: ', then
    while True:
        request = compute.instances().get(project=project, zone=zone, instance=name)
        result = request.execute()

        # print result

        if result['status'] == 'STAGING' and flag == 1:
            now2 = time.time() * 1000
            # print "Staging timestamp: ", now2
            if 'error' in result:
                raise Exception(result['error'])
            provisioning = now2 - then
            time_tmp = time.time() * 1000
            print 'Time elapse Provisioning-Staging: ', provisioning
            flag = 0

        if result['status'] == 'RUNNING':
            now = time.time() * 1000
            # print "Running timestamp: ", now
            if 'error' in result:
                raise Exception(result['error'])
            staging = now - time_tmp
            print 'Time elapse Staging-Running: ', staging
            ip = result['networkInterfaces'][0]['accessConfigs'][0]['natIP']
            return now, ip, provisioning, staging

        time.sleep(0.001)

def check_delete_process(compute, project, zone, name):
    flag = 1
    while True:
        try:
            request = compute.instances().get(project=project, zone=zone, instance=name)
            result = request.execute()
            # print result
            if result['status'] == 'STOPPING' and flag == 1:
                then = time.time() * 1000
                if 'error' in result:
                    raise Exception(result['error'])
                flag = 0

            if result['status'] == 'TERMINATED' and flag == 0:
                now = time.time() * 1000
                if 'error' in result:
                    raise Exception(result['error'])
                stopping = now - then
                time_tmp = time.time() * 1000
                print 'Time elapse stopping an instance: ', stopping
                flag = -1

        except googleapiclient.errors.HttpError:
            now2 = time.time() * 1000
            deleting = now2 - time_tmp
            print 'Time elapse deleting an instance: ', deleting
            return stopping, deleting

def ssh(initime, ip):
    # print "Booting timestamp: ", then
    # os.system('(ssh -q -o UserKnownHostsFile=/dev/null -o CheckHostIP=no -o StrictHostKeyChecking=no -i $HOME/.ssh/google_compute_engine -A -p 22 ozymandias@'+ip+' "echo 2>&1" && echo SSH_OK || echo SSH_NOK) | tail -n1')
    os.system('while true; do foo=$((ssh -q -o UserKnownHostsFile=/dev/null -o CheckHostIP=no -o StrictHostKeyChecking=no -i $HOME/.ssh/google_compute_engine -A -p 22 ozymandias@'+ip+' "echo 2>&1" && echo SSH_OK || echo SSH_NOK) | tail -n1); if [ $foo == "SSH_OK" ]; then echo SSH SUCCESS; break; else echo SSH FAILED; fi; done')
    now = time.time() * 1000
    booting = now - initime
    print 'Time elapse booting: ', booting
    return booting

def check_ssh_availability(ip):
    hostname = ip
    command = "ls"

    username = "ozymandias"
    port = 22
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy)

        client.connect(hostname, port=port, username=username, password=None, key_filename="/Users/ozymandias/.ssh/google_compute_engine")

        stdin, stdout, stderr = client.exec_command(command)
        print stdout.read(),
        return True
    except (paramiko.ssh_exception.BadHostKeyException, paramiko.ssh_exception.AuthenticationException,
            paramiko.ssh_exception.SSHException, paramiko.ssh_exception.socket.error) as e:
        print e
    finally:
        client.close()

for zone_name in ['asia-east1-c','europe-west4-a']:
    for i in range(5,10):
        instance = "a-v100-" + zone_name + '-' + `i`
        gpu_instance(compute, projectName, zone_name, instance, True, 'v100', 'stress.sh')
    for i in range(5,9):
        instance = "a-v100-" + zone_name + '-' + `i` + "less"
        gpu_instance(compute, projectName, zone_name, instance, True, 'v100')
