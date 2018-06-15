#import keras
import numpy as np
import pandas as pd
import sys
from toTest import toTest
from Table_Generator import Generator
from sklearn.externals import joblib
import argparse
import os

def S2P(opts):
    if(not os.path.exists('./tmp')):
        os.mkdir('./tmp')
    else:
        if(os.path.exists('./tmp/table.csv')):
            os.remove('./tmp/table.csv')
        if(os.path.exists('./tmp/test.csv')):
            os.remove('./tmp/test.csv')
    Generator(opts)
    toTest()
    y = Predict()
    df = pd.DataFrame(y)
    #print(df[1])
    return df[1]

def Predict():
    model = joblib.load('model/RF.pkl')
    df = pd.read_csv('tmp/test.csv')
    X_test = df.values
    print('Predicting...')
    y_test = model.predict_proba(X_test)
    #print(y_test)
    return y_test


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Making Traffic Table')
    parser.add_argument('--source_data_path', type=str,
                        default='youtube1.pcap', dest='source_data_path',
                        help='Path to source data')
    parser.add_argument('--output_path', type=str,
                        default='./tmp/table.csv', dest='output_path',
                        help='Path to output')
    """
    parser.add_argument('--model', type=int,
                        default='RF', dest='model',
                        help='RF or DNN')
    """

    opts = parser.parse_args()

    y = S2P(opts.source_data_path)
    #df = pd.DataFrame(y)
    #print(df[1])
    #print(y[1:5][])
    print(y)
