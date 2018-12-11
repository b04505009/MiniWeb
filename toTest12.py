import pandas as pd
import numpy as np
import sys


LABEL2DIG = {'chat':0, 'voip':1, 'trap2p':2, 'stream':3, 'file_trans':4, 'email':5}
DIG2LABEL = {v: k for k, v in LABEL2DIG.items()}


def toTest12():    
    #filepath = sys.argv[1]
    filepath = './tmp/table.csv'
    #targetpath = sys.argv[2]
    targetpath = './tmp/test12.csv'


    Col = pd.read_csv('ColSample12.csv')
    #Col.drop(['label'],axis = 1) 
    columns = Col.columns
    #print('ColSample:', columns)
    df = pd.read_csv(filepath)
    df = df.drop(df.columns[0], axis=1)
    
    df['vpn'] = df.file_name.str.contains('vpn').astype(int)
    
    df = df[(df.type!='browsing')&(df.file_name!='skype_audio1a_test')]
    # Broadcast and Multicast
    df = df[~(df.da.str.contains('224.0.'))]
    df = df[~(df.da.str.contains('239.255.'))]
    df = df[~(df.da.str.contains('255.255.'))]
    # Zzro packet size flow
    df = df[(df.formean!=0)|(df.backmean!=0)]
    # file transfer should not use udp
    df = df[~((df.type=='file_trans')&(df.pr==17))]
    # clean icmp
    df = df[df.pr!=1]
    # clean NetBIOS
    df = df[(df.sp>139)|(df.sp<137)]
    # one packet flow
    df = df[(df.tot_forpkts + df.tot_backpkts) > 1]

    #print('df shape: ',df.shape)
    df_drop = df.drop(['sp','dp','sa','da','pr','type','file_name','vpn'], axis = 1)
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
    toTest12()
