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
from flmt_predict import flowmeter_result
from keras.models import load_model
import tensorflow as tf

class ExportingThread(threading.Thread):
    def __init__(self):
        self.status = "nothing"
        self.ID = ""
        super().__init__()

    def run(self):
        pass
    def update(self,status):
        self.status = status
    def setID(self,ID):
        self.ID = ID
    def get_status(self):
        return self.status
    def get_ID(self):
        return self.ID

exporting_threads = {}
thread_id = 0


model1 = load_model("./model/model-00002-0.98101-0.06041.h5")
graph1 = tf.get_default_graph()
model2 = load_model("./model/model-00001-0.98077-0.06064.h5")
graph2 = tf.get_default_graph()

# create the little application object
server = Flask(__name__)
server.config.from_object(__name__)

class Record:
    def __init__(self):
        self.history_list = []
    def insert(self, ID, joy_flow_num, flmt_flow_num, time):
        self.history_list.append({'ID': ID, 'joy_flow_num': joy_flow_num, 'flmt_flow_num': flmt_flow_num, 'time': time})
    def find(self, ID):
        if list(filter(lambda h: h['ID'] == ID, self.history_list)) != []:
            return True
        else:
            return False
    def findall(self):
        return self.history_list
    
dir_name = "CSV"
if not os.path.exists("./CSV"):
    os.makedirs("./CSV")
record = Record()

server = Flask(__name__)
            
def valid_name(name):
    return all(c in string.hexdigits for c in name)

# magic_number of pcap : b'\xa1\xb2\xc3\xd4'
# magic_number of pcap : b'\xa1\xb2\x3c\x4d'


def check_magic_number(file_content, magic):
    return file_content[:len(magic)] == magic or file_content[:len(magic)] == magic[::-1]

def Check_Valid(file_content):
    restrict = 20*1024*1024 # 20MB
    if len(file_content)>restrict:
        print("out of size")
        return False
    if  not check_magic_number(file_content,b'\xa1\xb2\x3c\x4d') and not check_magic_number(file_content,b'\xa1\xb2\xc3\xd4'):
        # print(file_content[:len(b'\x4d\x3c\xb2\xa1')])
        print(check_magic_number(file_content,b'\xa1\xb2\x3c\x4d'))
        print(check_magic_number(file_content,b'\xa1\xb2\xc3\xd4'))
        print("not valid file syntax")
        return False
    return True



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
    return str(exporting_threads[thread_id].get_status())

@server.route('/ID/<int:thread_id>')
def ID(thread_id):
    global exporting_threads
    return str(exporting_threads[thread_id].ID())

@server.route('/checkvalid/<int:thread_id>',methods=['POST'])
def checkvalid(thread_id):
    global exporting_threads
    upload = request.files.get('upload')
    print("file")
    print(upload)
    if upload != None:
        content = upload.read()
        if not Check_Valid(content):
            print("file not valid")
            exporting_threads[thread_id].update('file not valid')
            return "file not valid"
            #return str(exporting_threads[thread_id].get_status())
        else:
            ID = hashlib.sha256(content).hexdigest()
            #print(connection.Record.find())
            exporting_threads[thread_id].update('file valid')
            with open(dir_name + '/' + ID + '.pcap', 'wb') as file:
                file.write(content)
            file_dir_name = str(dir_name + '/' + ID + '.pcap')
            exporting_threads[thread_id].setID(ID)
            return "file valid"
    else:
        print("file is None")
        exporting_threads[thread_id].update('file not valid')
        return "file not valid"
            #return str(exporting_threads[thread_id].status)
    

@server.route('/result/<int:thread_id>', methods=['GET'])
def result(thread_id):
    classifier_names = [
        'label(score)', 'sa', 'da', 'sp', 'dp', 'pr', 'pkt_in', 'pkt_out'
    ]
    joy_label = []
    joy_sa = []
    joy_da = []
    joy_sp = []
    joy_dp = []
    joy_pr = []
    joy_flow_num = len(joy_label)

    global exporting_threads
    ID = exporting_threads[thread_id].get_ID()
    if record.find(ID):
        return redirect('results/'+ ID)
    file_dir_name = dir_name + '/' + ID + '.pcap'
    flmt_df = flowmeter_result(file_dir_name, ID ,model1 ,model2, graph1, graph2)
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
    
    record.insert(ID, joy_flow_num, flmt_flow_num, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
    #print(joy_df)
    return redirect('results/'+ ID)

# For test now


@server.route('/results')
@server.route('/results/<ID>')
def results(ID=""):
    if not valid_name(ID) or ID == "":
        return "Invalid Query"
    #if ID not in IDSet:
    if not record.find(ID):
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

# should be delete  
@server.route('/secret')
def secret():
    a = ""
    for ID in IDSet:
        a += ID + '\n'
    return a


@server.route('/history')
def history():
    query = record.findall()
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
        

#server.run(port=5000, debug=True)
server.run(host="0.0.0.0", debug=True)
