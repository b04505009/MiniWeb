import numpy as np
import sys
import pandas as pd
from keras.models import Sequential, load_model
from keras.layers import Dense, Dropout, Flatten, Convolution1D, Convolution2D, MaxPooling2D, MaxPooling1D, ZeroPadding2D, AveragePooling2D, Activation
from keras.layers.normalization import BatchNormalization
from sklearn import preprocessing
import keras.backend as K
import tensorflow as tf
import subprocess

dir_name = "CSV"

def flowmeter_result(file_dir_name, ID,model1, model2, graph1, graph2, scaler):
    p = subprocess.Popen('java -Djava.library.path=CICFlowMeter-Command/jnetpcap-1.4.r1425 -jar CICFlowMeter-Command/CICFlowMeter.jar -pcappath ' +
                         file_dir_name + ' -outdir ' + dir_name + '/', shell=True)
    p.wait()
    data = pd.read_csv(dir_name + '/' + ID + '.pcap_Flow.csv')
    print(data.shape)
    df = pd.DataFrame(data)
    data = data.drop(['Flow ID', 'Src IP', 'Dst IP','Timestamp', 'Label', 'Src Port', 'Dst Port'], axis=1)
    data = scaler.transform(data)
    data = np.expand_dims(data, axis=2)
    pred = 0.0
    with graph1.as_default():
        pred += model1.predict(data)
    with graph2.as_default():
        pred += model2.predict(data)
    pred = pred/2
    pred = pd.DataFrame(pred)
    pred.columns = ['tor label']
    result = pd.concat([pred, df], axis=1)
    return result


    
    
