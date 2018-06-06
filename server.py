from flask import Flask, render_template, request
from os.path import join, dirname
from werkzeug.utils import secure_filename
import tempfile
import sys
import subprocess
import pandas as pd

server = Flask(__name__)


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
        is_upload = False
        if request.files.get('upload') != None:
            upload = request.files.get('upload')
            dir_name = tempfile.mkdtemp()
            upload.save(dir_name + '/' + secure_filename(upload.filename))
            is_upload = True
            file_dir_name = str(dir_name + '/' +
                                secure_filename(upload.filename))
            print(file_dir_name)
            flowmeter_result(dir_name,secure_filename(upload.filename))
            return render_template(
                'result.html',
                file_dir_name=file_dir_name,
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
                file_dir_name=None,
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
            file_dir_name=None,
                joy_label=joy_label,
                joy_sa=joy_sa,
                joy_da=joy_da,
                joy_sp=joy_sp,
                joy_dp=joy_dp,
                joy_pr=joy_pr,
                joy_pkt_in=joy_pkt_in,
                joy_pkt_out=joy_pkt_out,
                joy_flow_num=joy_flow_num)


def joy_result():
    return 

def flowmeter_result(pcapdirpath,filename):
    #檔名要hash
    subprocess.Popen('java -Djava.library.path=/home/esoe/CICFlowMeter-Command/jnetpcap-1.4.r1425 -jar /home/esoe/CICFlowMeter-Command/CICFlowMeter_main.jar -pcapdir ' + pcapdirpath + ' -outdir /home/esoe/csv/', shell=True)
    df = pd.read_csv()
    return


server.run(port=5000, debug=True)
# server.run(host="192.168.0.1",port=5000, debug=True)

