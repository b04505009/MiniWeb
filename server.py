from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
import tempfile
import hashlib
import string
import sys
import subprocess
import pandas as pd
import datetime
import threading
from S2P import P2P
from flmt_predict import predict
from keras.models import load_model
from mongokit import Connection, Document


IDSet = set()
dir_name = tempfile.mkdtemp()
#csv_dir = tempfile.mkdtemp()

server = Flask(__name__)
model = load_model("./model/model-00002-0.98101-0.06041.h5")
model2 = load_model("./model/model-00001-0.98077-0.06064.h5")

class ExportingThread(threading.Thread):
    def __init__(self):
        self.status = "nothing"
        super().__init__()

    def run(self):
        pass
    def update(self,status):
        self.status = status

exporting_threads = {}
thread_id = 0
    
# configuration
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017

# create the little application object
server = Flask(__name__)
server.config.from_object(__name__)

# connect to the database
connection = Connection(server.config['MONGODB_HOST'],
                        server.config['MONGODB_PORT'])

# !!!!!!!!!!!!!!!!!!!!!!!!!!
connection.test_db.drop_collection('test_col')
# !!!!!!!!!!!!!!!!!!!!!!!!!!

@connection.register
class Record(Document):
    __collection__ = 'test_col'
    __database__ = 'test_db'
    structure = {
        'ID': str,
        'joy_flow_num': int,
        'flmt_flow_num': int,
        'time': str,
    }
    use_dot_notation = True


def valid_name(name):
    return all(c in string.hexdigits for c in name)

# magic_number of pcap : b'\x4d\x3c\xb2\xa1'
# magic_number of pcap : b'\xa1\xv2\xc3\xd4'


def check_magic_number(file_content, magic):
    return file_content[:len(magic)] == magic


@server.route('/')
@server.route('/home')
def home():
    return render_template('home.html')


@server.route('/upload')
def upload():
    global exporting_threads
    global thread_id
    thread_id = (thread_id + 1)%100
    exporting_threads[thread_id] = ExportingThread()
    exporting_threads[thread_id].start()
    return render_template('upload.html',thread_id = thread_id)

@server.route('/status/<int:thread_id>')
def status(thread_id):
    global exporting_threads
    return str(exporting_threads[thread_id].status)


@server.route('/result', methods=['GET', 'POST'])
def result():
    classifier_names = [
        'label(score)', 'sa', 'da', 'sp', 'dp', 'pr', 'pkt_in', 'pkt_out'
    ]
    joy_label = []
    joy_sa = []
    joy_da = []
    joy_sp = []
    joy_dp = []
    joy_pr = []
    joy_label = [0, 1, 2]
    joy_sa = [0, 1, 2]
    joy_da = [0, 1, 2]
    joy_sp = [0, 1, 2]
    joy_dp = [0, 1, 2]
    joy_pr = [0, 1, 2]
    joy_flow_num = len(joy_label)
    if request.method == 'POST':
        print(request.files.get('upload'))
        print(dir_name)
        if request.files.get('upload') != None:
            upload = request.files.get('upload')
            content = upload.read()
            ID = hashlib.sha256(content).hexdigest()
            
            print(connection.Record.find())
            if connection.Record.find_one() is not None and connection.Record.find_one({"ID":ID}) is not None:
                return redirect('results/'+ ID)
            
            IDSet.add(ID)
            #upload.save(dir_name + '/' + ID)
            with open(dir_name + '/' + ID + '.pcap', 'wb') as file:
                file.write(content)
            file_dir_name = str(dir_name + '/' +
                                ID + '.pcap')
            print('file_dir_name: '+file_dir_name)
            print('dir_name: '+ dir_name)
            
            global exporting_threads
            global thread_id
            
            flmt_df = flowmeter_result(file_dir_name, ID ,model ,model2)
            flmt_df.to_json(dir_name + '/' + ID + '_flmt', compression = 'gzip')
            print("flowmeter good")
            exporting_threads[thread_id].update("flmt")
            joy_df = P2P(file_dir_name)
            joy_df.to_json(dir_name + '/' + ID + '_joy', compression = 'gzip')
            print("joy good")
            exporting_threads[thread_id].update("joy")
             
            os.remove(dir_name + '/' + ID + '.pcap')
            os.remove(dir_name + '/' + ID + '.pcap_Flow.csv')
            

            joy_label = joy_df['label'].tolist()
            joy_sa = joy_df['sa'].tolist()
            joy_da = joy_df['da'].tolist()
            joy_sp = joy_df['sp'].tolist()
            joy_dp = joy_df['dp'].tolist()
            joy_pr = joy_df['pr'].tolist()
            joy_flow_num = len(joy_label)

            flmt_label = flmt_df['tor label'].round(2).tolist()
            flmt_sa = flmt_df['Src IP'].tolist()
            flmt_da = flmt_df['Dst IP'].tolist()
            flmt_sp = flmt_df['Src Port'].tolist()
            flmt_dp = flmt_df['Dst Port'].tolist()
            flmt_pr = flmt_df['Protocol'].tolist()
            flmt_flow_num = len(flmt_sa)
            
 
            record = connection.Record()
            record['ID'] = ID
            record['joy_flow_num'] = joy_flow_num
            record['flmt_flow_num'] = flmt_flow_num
            record['time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            record.save()
            
            #print(joy_df)
            return redirect(
                'results/'+ ID)
        else:
            return render_template(
                'results.html',
                ID=None,
                joy_label=joy_label,
                joy_sa=joy_sa,
                joy_da=joy_da,
                joy_sp=joy_sp,
                joy_dp=joy_dp,
                joy_pr=joy_pr,
                joy_flow_num=joy_flow_num)
    else:
        return render_template(
            'results.html',
            ID=None,
            joy_label=joy_label,
            joy_sa=joy_sa,
            joy_da=joy_da,
            joy_sp=joy_sp,
            joy_dp=joy_dp,
            joy_pr=joy_pr,
            joy_flow_num=joy_flow_num)

# For test now


@server.route('/results')
@server.route('/results/<ID>')
def results(ID=""):
    if not valid_name(ID) or ID == "":
        return "Invalid Query"
    #if ID not in IDSet:
    if connection.Record.find_one({"ID":ID}) is None:
        return "Invalid Query"
    else:
        joy_df = pd.read_json(dir_name + '/' + ID + '_joy', compression = 'gzip')
        flmt_df = pd.read_json(dir_name + '/' + ID + '_flmt', compression = 'gzip')

        joy_label = joy_df['label'].tolist()
        joy_sa = joy_df['sa'].tolist()
        joy_da = joy_df['da'].tolist()
        joy_sp = joy_df['sp'].tolist()
        joy_dp = joy_df['dp'].tolist()
        joy_pr = joy_df['pr'].tolist()
        joy_flow_num = len(joy_label)
        flmt_label = flmt_df['tor label'].round(2).tolist()
        flmt_sa = flmt_df['Src IP'].tolist()
        flmt_da = flmt_df['Dst IP'].tolist()
        flmt_sp = flmt_df['Src Port'].tolist()
        flmt_dp = flmt_df['Dst Port'].tolist()
        flmt_pr = flmt_df['Protocol'].tolist()
        flmt_flow_num = len(flmt_sa)
        return render_template(
            'results.html',
            ID=ID,
            joy_label=joy_label,
            joy_sa=joy_sa,
            joy_da=joy_da,
            joy_sp=joy_sp,
            joy_dp=joy_dp,
            joy_pr=joy_pr,
            joy_flow_num=joy_flow_num,
            flmt_label=flmt_label,
            flmt_sa=flmt_sa,
            flmt_da=flmt_da,
            flmt_sp=flmt_sp,
            flmt_dp=flmt_dp,
            flmt_pr=flmt_pr,
            flmt_flow_num=flmt_flow_num)

    
@server.route('/secret')
def secret():
    a = ""
    for ID in IDSet:
        a += ID + '\n'
    return a

@server.route('/secret2')
def secret2():
    return str(list(connection.Record.find()))


@server.route('/history')
def history():
    query = list(connection.Record.find())
    print(query)
    if len(query) is not 0:
        df = pd.DataFrame(query)
        ID = df['ID'].tolist()
        joy_flow_num = df['joy_flow_num'].tolist()
        flmt_flow_num = df['flmt_flow_num'].tolist()
        time = df['time'].tolist()
        history_num = len(ID)
        return render_template('history.html',ID=ID,joy_flow_num=joy_flow_num,flmt_flow_num=flmt_flow_num,time = time,history_num=history_num)
    else:
        return render_template('history.html',ID=[],joy_flow_num=[],flmt_flow_num=[],time = [],history_num=0)
        


def flowmeter_result(file_dir_name, ID,model,model2):
    p = subprocess.Popen('java -Djava.library.path=CICFlowMeter-Command/jnetpcap-1.4.r1425 -jar CICFlowMeter-Command/CICFlowMeter.jar -pcappath ' +
                         file_dir_name + ' -outdir ' + dir_name + '/', shell=True)
    p.wait()
    df = pd.read_csv(dir_name + '/' + ID + '.pcap_Flow.csv')
    df = predict(df,model,model2)
    #df = df[[,'Src IP','Dst IP','Src Port','Dst Port','Protocol']]
    #print(df['Flow ID'])
    return df


#server.run(port=5000, debug=True)
server.run(host="192.168.21.2", port=5000, debug=True)
