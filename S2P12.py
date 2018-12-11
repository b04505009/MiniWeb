#import keras
import numpy as np
import pandas as pd
import sys
from toTest12 import toTest12
from Table_Generator12 import Generator
#from sklearn.externals import joblib
import argparse
import os
import subprocess
import xgboost as xgb

def S2P12(path):
    Generator(path)
    toTest12()
    y = Predict12()
    df = pd.DataFrame(y)
    print(df)
    return df[0]
def P2P12(path):
    if(not os.path.exists('./tmp')):
        os.mkdir('./tmp')
    else:
        if(os.path.exists('./tmp/table12.csv')):
           os.remove('./tmp/table12.csv')
        if(os.path.exists('./tmp/test12.csv')):
            os.remove('./tmp/test12.csv')
    
    filename1 = "./tmp/joy.gz"       
    filename2 = "./tmp/sleuth.json"
    #p = subprocess.Popen("../joy/bin/joy classify=1 tls=1 dns=1 http=1 bidir=1 idp=16 dist=1 entropy=1 {0} > {1}".format(path, filename1),shell = True)
    #p.wait()
    #p = subprocess.Popen("../joy/sleuth {0} > {1}".format(filename1, filename2), shell=True)
    #p.wait()
        ###Sleuth2Predict
    y = S2P12(filename2)
    df = pd.read_csv("./tmp/table12.csv")
    df['sp'] = df['sp'].fillna(0).astype(int)
    df['dp'] = df['dp'].fillna(0).astype(int)
    df['label'] = y;
    #print('Score:')
    #print(y)
    return df


def Predict12():
    bst = xgb.Booster({'nthread':4})
    bst.load_model('model/model12.bin')
    df = pd.read_csv('tmp/test12.csv')
    X_test = df.values
    dtest = xgb.DMatrix(X_test)
    print('Predicting...')
    y_test = bst.predict(dtest)
    y_test = np.argmax(y_test, axis=1)
    #print(y_test)
    return y_test


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Making Traffic Table')
    parser.add_argument('--source_data_path', type=str,
                        default='sample.pcap', dest='source_data_path',
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

    #y = S2P(opts.source_data_path)
    y = P2P12(opts.source_data_path)
    #df = pd.DataFrame(y)
    #print(df[1])
    #print(y[1:5][])
    print(y)
    print(y.label)
