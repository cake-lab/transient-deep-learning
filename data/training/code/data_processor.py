import googleapiclient.discovery
import googleapiclient
from datetime import datetime
import os
import sqlite3
import csv

PROJECTNAME = "shijian-18"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = '/Users/ozymandias/Desktop/cloudComputing/shijian-18-key.json'
COMPUTE = googleapiclient.discovery.build('compute', 'v1')

def write_file():
    zones = ['us-west1-b', 'us-central1-a']
    VMs = ['-master']

    with open('/Users/ozymandias/Desktop/vm_data.csv', mode='w') as input:
        writer = csv.writer(input, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['VM_name', 'Uptime', 'Revoked'])
        for zone in zones:
            for run in range(1,runs+1):
                for vm in VMs:
                    res, name, revoked = get_vm_data('v100-spot-'+zone+'-run'+str(run)+vm)
                    if res != None:
                        writer.writerow([name, res, revoked])


def select_running_host_by_region(host_name, status, role=None):
    db_conn = sqlite3.connect('/Users/ozymandias/desktop/spotTrain_data/v100/v100.db',
                              check_same_thread=False)
    cursor = db_conn.cursor()

    try:
        if role:
            query = '''SELECT * FROM cluster_status WHERE host_name=? AND status=? AND role=?'''
            cursor.execute(query, (host_name, status, role,))
        else:
            query = '''SELECT * FROM cluster_status WHERE host_name=? AND status=?'''
            cursor.execute(query, (host_name, status,))
        all_rows = cursor.fetchall()
    except Exception as e:
        print "An error occured when selecting server in DB:", e
        db_conn.rollback()
    finally:
        cursor.close()

    return all_rows

def get_vm_data(host_name):
    entry = select_running_host_by_region(host_name, 'TERMINATED')
    if len(entry) != 0:
        revoked = entry[0][8]
        name = entry[0][0]
        res = datetime.strptime(entry[0][6], '%Y-%m-%d %H:%M:%S.%f') - datetime.strptime(entry[0][5],
                                                                                         '%Y-%m-%d %H:%M:%S.%f')
        return res.total_seconds(), name, revoked

def train_data_processor(path):
    with open(path+"train_data.csv") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader, None)
        data = []
        entry = {}
        # entry['zone'] = None
        entry['run'] = None
        entry['accuracy'] = 0.0
        entry['duration'] = 0
        for row in csv_reader:
            # print row
            if row[1] == '0':
                # entry['zone'] = row[3]
                entry['run'] = row[3]
                start_time = row[0]
            if int(row[1]) >= 64000:
                end_time = row[0]
                entry['duration'] = float(end_time) - float(start_time)
                entry['accuracy'] = row[2]
                data.append(entry)
                entry = {}

    print data
    csv_file.close()

    with open(path+'train_data_processed.csv', mode='w') as input:
        writer = csv.writer(input, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Run', 'Duration', 'Accuracy'])
        for item in data:
            writer.writerow([item['run'], item['duration'], item['accuracy']])

def process_cost(path, num_v100, num_p100, num_k80, num_ps):

    with open('/Users/ozymandias/Desktop/spotTrain_data/8-spot/train_data_processed.csv') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader, None)
        train_data = []
        entry = {}
        entry['run'] = None
        entry['time'] = None
        entry['accuracy'] = None
        for cluster in csv_reader:
            entry['run'] = cluster[0] + '-run' + cluster[1]
            entry['time'] = cluster[2]
            entry['accuracy'] = cluster[3]
            train_data.append(entry)
            entry = {}
            entry['run'] = None
            entry['time'] = None
            entry['accuracy'] = None
    # print train_data

    with open('/Users/ozymandias/Desktop/spotTrain_data/8-spot/vm_data.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader, None)
        count = 0
        cost = []
        entry = {}
        entry['cost'] = 0
        entry['run'] = None
        entry['zone'] = None
        max = 0.
        for row in csv_reader:
            print row
            count += 1
            entry['run'] = row[0].split('-')[4][3:]
            entry['zone'] = row[0].split('-')[0] + '-' + row[0].split('-')[1] + '-' + row[0].split('-')[2] + '-' + row[0].split('-')[3]
            # entry['cost'] += float(train_data[(count - 1) // 4]['time']) * 0.00020083
            #### 0.00020083 on demand
            if row[2] == 'Job completed' or row[2] == 'Job Completed' or row[2] == 'Manually stopped due to revoked master':
                entry['cost'] += float(train_data[(count -1) // 8]['time']) * 0.000071
            else:
                entry['cost'] += float(row[1]) * 0.000071
            if count % 8 == 0: ######
                entry['cost'] += float(train_data[(count -1) // 8]['time']) * 0.0000397
                cost.append(entry)
                entry = {}
                entry['cost'] = 0
                entry['run'] = None
                entry['zone'] = None
                max = 0
        print cost
        write_processed(cost, path)


def write_processed(cost, path):
    with open(path+'cost.csv', mode='w') as input:
        writer = csv.writer(input, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # writer.writerow(['Zone', 'Run', 'Cost'])
        writer.writerow(['Run', 'Cost'])
        for item in cost:
            writer.writerow([item['run'], item['cost']])

def heatmap_data_generator():
    with open('/Users/ozymandias/Desktop/spotTrain_data/2-spot/vm_data.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader, None)
        vm_data = []
        ventry = {}
        ventry['name'] = None
        ventry['time'] = None
        ventry['accuracy'] = None
        for vm in csv_reader:
            ventry = {}
            ventry['name'] = vm[0]
            ventry['time'] = vm[1]
            ventry['reltime'] = None
            run = vm[0].split('-')[0] + '-' +vm[0].split('-')[1]+'-'+vm[0].split('-')[2]+'-'+vm[0].split('-')[3]
            if run != 'us-east1-c-run7':
                vm_data.append(ventry)
            ventry = {}
            ventry['name'] = None
            ventry['time'] = None
            ventry['reltime'] = None

    with open('/Users/ozymandias/Desktop/spotTrain_data/4-spot/train_data_processed.csv') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader, None)
        train_data = []
        entry = {}
        entry['run'] = None
        entry['time'] = None
        entry['accuracy'] = None
        for cluster in csv_reader:
            entry['run'] = cluster[0] + '-run' + cluster[1]
            entry['time'] = cluster[2]
            entry['accuracy'] = cluster[3]
            train_data.append(entry)
            entry = {}
            entry['run'] = None
            entry['time'] = None
            entry['accuracy'] = None

    count = 0
    for item in vm_data:
        # print train_data[count // 4]['time'], float(item['time'])
        # if abs(float(train_data[count // 4]['time']) - float(item['time']))<50:
            # print 'rei'
        if float(item['time']) / float(train_data[count // 4]['time']) > 1:
            item['reltime'] = 1
        else:
            item['reltime'] = float(item['time']) / float(train_data[count // 4]['time'])
        # count += 1

    val = []
    subval = []
    label = []
    for i in vm_data:
        count += 1
        subval.append(i['reltime'])
        if count % 4 == 0:
            val.append(subval)
            subval = []

    with open('/Users/ozymandias/Desktop/heat.csv', mode='w') as input:
        writer = csv.writer(input, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['reltime', 'name'])
        for item in vm_data:
            writer.writerow([item['reltime'], item['name']])

if __name__ == '__main__':
    write_file()
    process_cost('/Users/ozymandias/Desktop/spotTrain_data/experiment_1ps_vs_2ps/2ps2v/', 2, 0, 0, 2)
    train_data_processor('/Users/ozymandias/Desktop/spotTrain_data/2e1c1w-p100/')
    # heatmap_data_generator()