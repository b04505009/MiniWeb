from flask import Flask, render_template, request
from os.path import join, dirname
from werkzeug.utils import secure_filename
import tempfile
import hashlib
import string
import sys
import subprocess
import pandas as pd

IDSet = set()
dir_name = tempfile.mkdtemp()
csv_dir = tempfile.mkdtemp()

server = Flask(__name__)


def valid_name(name):
    return all(c in string.hexdigits for c in name)


@server.route('/')
@server.route('/home')
def home():
    return render_template('home.html')


@server.route('/upload')
def test():
    return render_template('upload.html')


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
    joy_pkt_in = []
    joy_pkt_out = []
    joy_label = [0, 1, 2]
    joy_sa = [0, 1, 2]
    joy_da = [0, 1, 2]
    joy_sp = [0, 1, 2]
    joy_dp = [0, 1, 2]
    joy_pr = [0, 1, 2]
    joy_pkt_in = [0, 1, 2]
    joy_pkt_out = [0, 1, 2]
    joy_flow_num = len(joy_label)
    if request.method == 'POST':
        print(request.files.get('upload'))
        print(dir_name)
        if request.files.get('upload') != None:
            upload = request.files.get('upload')
            content = upload.read()
            filename = hashlib.sha256(content).hexdigest()
            IDSet.add(filename)
            ID = filename
            #upload.save(dir_name + '/' + ID)
            with open(dir_name + '/' + ID + '.pcap', 'wb') as file:
                file.write(content)
            file_dir_name = str(dir_name + '/' +
                                ID+'.pcap')
            print(file_dir_name)
            flowmeter_result(file_dir_name, ID)
            # TODO : use joy controller
            return render_template(
                'result.html',
                ID=ID,
                joy_label=joy_label,
                joy_sa=joy_sa,
                joy_da=joy_da,
                joy_sp=joy_sp,
                joy_dp=joy_dp,
                joy_pr=joy_pr,
                joy_pkt_in=joy_pkt_in,
                joy_pkt_out=joy_pkt_out,
                joy_flow_num=joy_flow_num)
        else:
            return render_template(
                'result.html',
                ID=None,
                joy_label=joy_label,
                joy_sa=joy_sa,
                joy_da=joy_da,
                joy_sp=joy_sp,
                joy_dp=joy_dp,
                joy_pr=joy_pr,
                joy_pkt_in=joy_pkt_in,
                joy_pkt_out=joy_pkt_out,
                joy_flow_num=joy_flow_num)
    else:
        return render_template(
            'result.html',
            ID=None,
            joy_label=joy_label,
            joy_sa=joy_sa,
            joy_da=joy_da,
            joy_sp=joy_sp,
            joy_dp=joy_dp,
            joy_pr=joy_pr,
            joy_pkt_in=joy_pkt_in,
            joy_pkt_out=joy_pkt_out,
            joy_flow_num=joy_flow_num)

# For test now


@server.route('/results')
@server.route('/results/<ID>')
def results(ID=""):
    if not valid_name(ID) or ID == "":
        return "Invalid Query"
    if ID not in IDSet:
        return "Invalid Query"
    else:
        joy_label = [0, 1, 2, 3]
        joy_sa = [0, 1, 2, 3]
        joy_da = [0, 1, 2, 3]
        joy_sp = [0, 1, 2, 3]
        joy_dp = [0, 1, 2, 3]
        joy_pr = [0, 1, 2, 3]
        joy_pkt_in = [0, 1, 2, 3]
        joy_pkt_out = [0, 1, 2, 3]
        joy_flow_num = len(joy_label)
        return render_template(
            'results.html',
            ID=ID,
            joy_label=joy_label,
            joy_sa=joy_sa,
            joy_da=joy_da,
            joy_sp=joy_sp,
            joy_dp=joy_dp,
            joy_pr=joy_pr,
            joy_pkt_in=joy_pkt_in,
            joy_pkt_out=joy_pkt_out,
            joy_flow_num=joy_flow_num)


@server.route('/secret')
def secret():
    a = ""
    for ID in IDSet:
        a += ID + '\n'
    return a


def joy_result():
    return


def flowmeter_result(file_dir_name, ID):
    p = subprocess.Popen('java -Djava.library.path=CICFlowMeter-Command/jnetpcap-1.4.r1425 -jar CICFlowMeter-Command/CICFlowMeter.jar -pcappath ' +
                         file_dir_name + ' -outdir ' + csv_dir + '/', shell=True)
    p.wait()
    df = pd.read_csv(csv_dir + '/' + ID + '.pcap_Flow.csv')
    print(df['Flow ID'])
    return


server.run(port=5000, debug=True)
#server.run(host="192.168.0.1",port=5000, debug=True)
