#!/usr/bin/python
import xmlrpclib
import json
import os
import syslog
from datetime import datetime
import socket
import googleapiclient
import googleapiclient.discovery

def main():
    name = socket.gethostname()
    compute = googleapiclient.discovery.build('compute', 'v1')
    projectName = "shijian-18"
    rpc_server_name = name.split('-')[0] + '-' + 'ps-0'
    request = compute.instances().get(project=projectName, zone='us-west1-b', instance=rpc_server_name)
    response = request.execute()
    ps_ip = response['networkInterfaces'][0]['networkIP'].encode("utf-8")

    s = xmlrpclib.ServerProxy('http://' + ps_ip + ':8000')
    # with open("/tmp/job_config.txt","r") as fp:
    #     s_type = fp.readline().rstrip('\n')
    #     s_index = fp.readline().rstrip('\n')
    try:
        role = name.split('-')[1]
        if role == 'master':
            role = 'chief'
            index = '0'
        else:
            index = name.split('-')[2]
        s.serverDown(role, index, name)
    except Exception as e:
        print('Encountered error', e)
        syslog.syslog('Encountered error')

if __name__ == '__main__':
    out_file = open("/home/ozymandias/serverDown.log", "w")
    out_file.write(str(datetime.utcnow()))
    out_file.write('\n')
    main()
    out_file.write(str(datetime.utcnow()))
    out_file.close()