import numpy as np
import sys
import pandas as pd
from keras.models import Sequential, load_model
from keras.layers import Dense, Dropout, Flatten, Convolution1D, Convolution2D, MaxPooling2D, MaxPooling1D, ZeroPadding2D, AveragePooling2D, Activation
from keras.layers.normalization import BatchNormalization
from sklearn import preprocessing
from sklearn.externals import joblib
import keras.backend as K
import tensorflow as tf

def predict(data,model,model2):
    scaler = joblib.load('scaler.pkl')
    print(data.shape)
    df = pd.DataFrame(data)
    data = data.drop(['Flow ID', 'Src IP', 'Dst IP','Timestamp', 'Label', 'Src Port', 'Dst Port'], axis=1)
    #data = data.astype('float32')
    #data = np.array(data,dtype=np.long)
    data = scaler.transform(data)
    #print(data.shape)
    data = np.expand_dims(data, axis=2)
    #print(data.shape)
    #model = load_model("./model/model-00002-0.98101-0.06041.h5")
    #model2 = load_model("./model/model-00001-0.98077-0.06064.h5")
    #model3 = load_model("./model/1/model-00203-0.98244-0.05789.h5")
    #model4 = load_model("./model/1/model-00203-0.98244-0.05789.h5")
    pred = 0.0
    pred += model.predict(data)
    pred += model2.predict(data)
    #pred += model3.predict(data)
    #pred += model4.predict(data)
    pred = pred/2
    #pred = np.around(pred)
    #print(pred.shape)
    #print(pred)
    pred = pd.DataFrame(pred)
    pred.columns = ['tor label']
    #print(pred)
    result = pd.concat([pred, df], axis=1)
    #print(result)
    return result
    
    
