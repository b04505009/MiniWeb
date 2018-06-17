import pandas as pd
import numpy as np
import sys




def toTest():    
    #filepath = sys.argv[1]
    filepath = './tmp/table.csv'
    #targetpath = sys.argv[2]
    targetpath = './tmp/test.csv'


    Col = pd.read_csv('ColSample.csv')
    #Col.drop(['label'],axis = 1) 
    columns = Col.columns
    #print('ColSample:', columns)
    df = pd.read_csv(filepath)
    df = df.drop(df.columns[0], axis=1)
    #print('df shape: ',df.shape)
    df_drop = df.drop(['sp','dp','sa','da','pr','type','file_name'], axis = 1)
    #print('df shape: ', df_drop.shape)
    #print(df_drop.columns)
    table = pd.get_dummies(df_drop)
    
    for col in table.columns:
        if(col not in Col.columns):
            table.drop([col], axis = 1)
            print('drop columns:', col)
    #print(table.columns) 
    DF = pd.concat([Col,table], axis = 0,join = 'outer', ignore_index = True)
    DF = DF.drop(DF.index[0])
    DF = DF.fillna(0)

    #print('test shape:', DF.shape)
    #np.save('X_train', X_train)
    DF.to_csv(targetpath, index = False, columns = columns)
    

if __name__=="__main__":
    toTest()
