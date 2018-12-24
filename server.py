from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import time
from werkzeug.utils import secure_filename
import hashlib
import string
import sys
import subprocess
from collections import Counter
import pandas as pd
import datetime
import threading
from S2P import P2P
from S2P12 import P2P12
from flmt_predict import flowmeter_result
from keras.models import load_model
import tensorflow as tf
from sklearn.externals import joblib
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.transform import cumsum
from bokeh.palettes import Category20
from math import pi
import xgboost as xgb


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
scaler = joblib.load('./model/scaler.pkl')
joy_model = joblib.load('model/RF.pkl')
bst = xgb.Booster({'nthread':4})
joy12_model =  bst.load_model('model/model12.bin')


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
"""
for csv in os.listdir("./CSV"):
    if csv.endswith("flmt.csv"):
        ID = csv.split('_', 1)[0];
        flmt_df = pd.read_csv("./CSV/" + csv)
        flmt_flow_num = flmt_df.shape[0]
        joy_df = pd.read_csv("./CSV/" + ID + "_joy.csv")
        joy_flow_num = joy_df.shape[0]
        
        record.insert(ID, joy_flow_num, flmt_flow_num, "Unknown")
print(record.findall())
"""
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
    error = ""
    global exporting_threads
    global thread_id
    thread_id = (thread_id + 1)%100
    exporting_threads[thread_id] = ExportingThread()
    exporting_threads[thread_id].start()
    if 'error' in request.args:
        error = request.args['error']
    return render_template('upload.html',thread_id = thread_id, error = error)

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
        else:
            ID = hashlib.sha256(content).hexdigest()
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
    global exporting_threads
    ID = exporting_threads[thread_id].get_ID()
    if record.find(ID):
        return redirect('results/'+ ID)
    try:
        file_dir_name = dir_name + '/' + ID + '.pcap'
        flmt_df = flowmeter_result(file_dir_name, ID ,model1 ,model2, graph1, graph2, scaler)
        flmt_df.to_csv(dir_name + '/' + ID + '_flmt.csv',sep=',', encoding='utf-8',index = False)
        print("flowmeter good")
        exporting_threads[thread_id].update("flmt")
        #joy_df = P2P(file_dir_name, joy_model)
        #joy_df.to_csv(dir_name + '/' + ID + '_joy.csv',sep=',', encoding='utf-8',index = False)
        #print("joy good")
        #exporting_threads[thread_id].update("joy")
        app_df = P2P12(file_dir_name, joy12_model, bst)
        app_df.to_csv(dir_name + '/' + ID + '_app.csv',sep=',', encoding='utf-8',index = False)
        print("app good")
        exporting_threads[thread_id].update("app")
    except Exception as e:
        print(e)
        if os.path.exists(dir_name + '/' + ID + '.pcap'):
            os.remove(dir_name + '/' + ID + '.pcap')
        if os.path.exists(dir_name + '/' + ID + '.pcap_Flow.csv'):
            os.remove(dir_name + '/' + ID + '.pcap_Flow.csv')
        if os.path.exists(dir_name + '/' + ID + '_flmt.csv'):
            os.remove(dir_name + '/' + ID + '_flmt.csv')
        if os.path.exists(dir_name + '/' + ID + '_joy.csv'):
            os.remove(dir_name + '/' + ID + '_joy.csv')   
        exporting_threads[thread_id].update("error")
        return redirect(url_for('upload', error = "Some protocols in your file are not supported by our service!"))

    os.remove(dir_name + '/' + ID + '.pcap')
    os.remove(dir_name + '/' + ID + '.pcap_Flow.csv')

    app_flow_num = app_df.shape[0]
    flmt_flow_num = flmt_df.shape[0]
    
    record.insert(ID, app_flow_num, flmt_flow_num, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
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
        #joy_dict = pd.read_csv(dir_name + '/' + ID + '_joy.csv')[['label','sa','da','sp','dp','pr']].reset_index().to_dict(orient='list')
        flmt_dict = pd.read_csv(dir_name + '/' + ID + '_flmt.csv')[['tor label','Src IP','Dst IP','Src Port','Dst Port','Protocol']].reset_index().to_dict(orient='list')
        app_dict = pd.read_csv(dir_name + '/' + ID + '_app.csv')[['label','sa','da','sp','dp','pr']].reset_index().to_dict(orient='list')
        #joy_dict['label'] = [round(l,2) for l in joy_dict['label']]
        flmt_dict['tor label'] = [round(l,2) for l in flmt_dict['tor label']]
        app_dict['label'] = [round(l,2) for l in app_dict['label']]
        #joy_flow_num = len(joy_dict['label'])
        flmt_flow_num = len(flmt_dict['tor label'])
        app_flow_num = len(app_dict['label'])
        LABEL2DIG = {'chat':0, 'voip':1, 'trap2p':2, 'stream':3, 'file_trans':4, 'email':5, 'vpn_chat':6, 'vpn_voip':7, 'vpn_trap2p':8, 'vpn_stream':9, 'vpn_file_trans':10, 'vpn_email':11}
        DIG2LABEL = {v: k for k, v in LABEL2DIG.items()}
        app_dict['label'] = [DIG2LABEL[d] for d in app_dict['label'] ]
        """
        # joy pie chart
        joy_m = len([i for i in joy_dict['label'] if i > 0.8])
        joy_b = joy_flow_num - joy_m
        data = pd.Series([joy_b, joy_m], index=['benign', 'malign']).reset_index(name='value').rename(columns={'index': 'class'})
        data['angle'] = data['value']/data['value'].sum() * 2 * pi
        data['color'] = ['#336699', '#CC3333']

        p = figure(plot_height=350, plot_width=500, title="Malicious flows identified by Joy features", toolbar_location=None,
                   tools="hover", tooltips="@class: @value",  x_range = (-0.5, 1.0))
        p.wedge(x=0, y=1, radius=0.4, direction="clock",
                start_angle=cumsum('angle'), end_angle=cumsum('angle', include_zero=True),
                line_color="white", fill_color='color', legend='class', source=data)
        p.axis.axis_label = None
        p.axis.visible = False
        p.grid.grid_line_color = None
        p.title.text_font_size = '18pt'
        p.title.align = 'center'
        p.outline_line_color = None
        p.outline_line_width = 0
        joy_js_resources = INLINE.render_js()
        joy_css_resources = INLINE.render_css()
        joy_script, joy_div = components(p)
        """
        # flmt pie chart
        flmt_t = len([i for i in flmt_dict['tor label'] if i > 0.5])
        flmt_nt = flmt_flow_num - flmt_t
        data = pd.Series([flmt_nt, flmt_t], index=['Non tor', 'tor']).reset_index(name='value').rename(columns={'index': 'class'})
        data['angle'] = data['value']/data['value'].sum() * 2 * pi
        data['color'] = ['#FFFFCC', '#663366']

        p = figure(plot_height=350, plot_width=500, title="Tor flows identified by Flowmeter features", toolbar_location=None,
                   tools="hover", tooltips="@class: @value",  x_range = (-0.5, 1.0))
        p.wedge(x=0, y=1, radius=0.4, direction="clock",
                start_angle=cumsum('angle'), end_angle=cumsum('angle', include_zero=True),
                line_color="white", fill_color='color', legend='class', source=data)
        p.axis.axis_label = None
        p.axis.visible = False
        p.grid.grid_line_color = None
        p.title.text_font_size = '18pt'
        p.title.align = 'center'
        p.outline_line_color = None
        p.outline_line_width = 0
        flmt_js_resources = INLINE.render_js()
        flmt_css_resources = INLINE.render_css()
        flmt_script, flmt_div = components(p)
        
        # app pie chart
        data = pd.Series([app_dict['label'].count(l) for l in list(LABEL2DIG)], index=list(LABEL2DIG)).reset_index(name='value').rename(columns={'index': 'class'})
        
        data['angle'] = data['value']/data['value'].sum() * 2 * pi
        data['color'] = Category20[12]

        p = figure(plot_height=350, plot_width=500, title="Application Classification", toolbar_location=None,
                   tools="hover", tooltips="@class: @value",  x_range = (-0.5, 1.0))
        p.wedge(x=0, y=1, radius=0.4, direction="clock",
                start_angle=cumsum('angle'), end_angle=cumsum('angle',include_zero=True),
                line_color="white", fill_color='color', legend='class', source=data)
        p.axis.axis_label = None
        p.axis.visible = False
        p.grid.grid_line_color = None
        p.title.text_font_size = '18pt'
        p.title.align = 'center'
        p.outline_line_color = None
        p.outline_line_width = 0
        app_js_resources = INLINE.render_js()
        app_css_resources = INLINE.render_css()
        app_script, app_div = components(p)
         
        return render_template(
            'results.html',
            ID=ID,
            #joy_dict = joy_dict,
            #joy_flow_num=joy_flow_num,
            flmt_dict = flmt_dict,
            flmt_flow_num=flmt_flow_num,
            app_dict=app_dict,
            app_flow_num=app_flow_num,
            #joy_js_resources = joy_js_resources,
            #joy_css_resources = joy_css_resources,
            #joy_script = joy_script,
            #joy_div = joy_div,
            flmt_js_resources = flmt_js_resources,
            flmt_css_resources = flmt_css_resources,
            flmt_script = flmt_script,
            flmt_div = flmt_div,
            app_js_resources = app_js_resources,
            app_css_resources = app_css_resources,
            app_script = app_script,
            app_div = app_div
        )


@server.route('/history')
def history():
    query = record.findall()
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
    
@server.route('/download/<tab>/<ID>', methods=['GET', 'POST'])
def download(tab,ID):
    return send_from_directory(directory=os.path.join(server.root_path, "CSV/"), filename=ID+"_"+tab+".csv",as_attachment=True)
        

#server.run(port=5000, debug=True)
server.run(host="0.0.0.0", debug=True)
