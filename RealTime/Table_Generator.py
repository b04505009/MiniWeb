
# coding: utf-8

# In[48]:


from pandas.io.json import json_normalize
import pandas as pd
import numpy as np
import json
import time
#import matplotlib.pyplot as plt
import sys
import os.path
import argparse

def read_json_fun(file):
    data = []
    temp = []
    data_str = open(file).read()
    temp = data_str.splitlines()
    num = len(temp)
    for i in range(num):
        str = temp[i]
        data.append(json.loads(str))
    return data

def Generator(path):
    #df = pd.read_excel('Markov.xlsx')
    col = ['file_name','label','type','sa','da','sp','dp','pr','tls_scs','tls_ext_server_name','tls_c_key_length','http_content_type','http_user_agent','http_accept_language','http_server','http_code','dns_domain_name','dns_ttl','dns_num_ip','dns_domain_rank']
    for i in range(20):
        for j in range(20):
            splt_str = 'splt_' + str(i) + '_' + str(j) 
            col.append(splt_str)

    for i in range(256):
        dist_str = 'dist_' + str(i)
        col.append(dist_str)
    col.append('entropy')

   # df = pd.DataFrame(columns = col)

    #print(df.columns)
    inputfile=path
    #print('python input:',inputfile)
    data = read_json_fun(inputfile)
    fn=os.path.basename(inputfile)
    title=os.path.splitext(fn)[0]
    #print('file = ',title)
    
    Type = Catgo(title)
    #print('type = ',Type)
    NumIter = len(data)
    for i in range(0,len(data)):
        df = pd.DataFrame(columns = col)
        Basic_Info(data, i, df, Type, title)
        Marcov(data, i, df)
        TLS(data, i, df)
        http(data, i ,df)
        dns(data, i ,df)
        Byte_dist(data, i, df)
        """
        if(i%5 == 0):
            print('Processing:{}/{}'.format(i,NumIter))
        """
    #Saving Dataframe into csv
        out_file = './tmp/table.csv'
        if(os.path.isfile(out_file)):
            df.to_csv(out_file, mode = 'a',header = False)
        else:
            df.to_csv(out_file, header = col)

def Byte_dist(data, i, df):
    bdlist = []
    su = 0
    if data[i].__contains__('byte_dist'):
        pakpd=data[i]['byte_dist']
        for n in pakpd:
            bdlist.append(n)
            su += n
        if su <= 0:
            bdlist = np.zeros(256)
        else:
            bdlist = np.array(bdlist) / su
    else:
        bdlist = np.zeros(256)

    for q in range(256):
        dist_str = 'dist_' + str(q)
        df.loc[i,dist_str] = bdlist[q]
    if data[i].__contains__('entropy'):
        df.loc[i,'entropy'] = data[i]['entropy']
    else:
        df.loc[i,'entropy'] = -1
def http(data, i, df):
    http_col = ['http_content_type','http_user_agent','http_accept_language','http_server','http_code']
    if data.__contains__("http"):
        http = data['http'][0]
        if http.__contains__('in'):
            code = False
            server = False
            content = False
            for element in http['in']:
                if element.__contains__("code"):
                    df.loc[i,'http_code'] = element['code']
                    code = True
                if element.__contains__("Server"):
                    df.loc[i,'http_server'] = element["Server"]
                    server = True
                if element.__contains__("Content-Type"):
                    df.loc[i,'http_content_type'] = element['Content-Type']
                    content = True
            if not code:
                df.loc[i,'http_code'] = 'http_code_NULL'
            if not server:
                df.loc[i,'http_server'] = 'http_server_NULL'
            if not content:
                df.loc[i,'http_content_type'] = 'http_content_type_NULL'

        else:
            in_col = ['http_content_type','http_server','http_code']
            df.loc[i,in_col] = [k+'NULL' for k in in_col]
        if http.__contains__('out'):
            agent = False
            lang = False
            for element in http['out']:
                if element.__contains__("User-Agent"):
                    df.loc[i,'http_user_agent'] = element["User-Agent"]
                    agent = True
                if element.__contains__("Accept-Language"):
                    df.loc[i,'http_accept_language'] = element["Accept-Language"]
                    lang = True
            if not agent:
                df.loc[i,'http_user_agent'] = 'http_user_agent_NULL'
            if not lang:
                df.loc[i,'http_accept_language'] = 'http_accept_language_NULL'
        else:
            out_col = ['http_user_agent','http_accept_language']
            df.loc[i,out_col] = [k+'NULL' for k in out_col]
    else:
        df.loc[i,http_col] = [k+'NULL' for k in http_col]
    return 

def dns(data, i, df):
    dns_col = ['dns_domain_name','dns_ttl','dns_num_ip','dns_domain_rank']
    if data.__contains__("linked_dns"):
        dns = data['linked_dns']
        num_ip = 0

        if dns.__contains__('dns'):
            if dns['dns'][0].__contains__('rn'):
                df.loc[i,'dns_domain_name'] = dns['dns'][0]['rn']
            else:
                df.loc[i,'dns_domain_name'] = 'dns_domain_name_NULL'
            if dns['dns'][0].__contains__('rr'):
                lis = dns['dns'][0]['rr']
                ttl = -1
                for element in lis:
                    if ttl == -1 and element.__contains__('cname'):
                        ttl = element['ttl']
                    if element.__contains__('a'):
                        num_ip+=1
                if ttl == -1:
                    df.loc[i,'dns_ttl'] = 'dns_ttl_NULL'
                else:
                    df.loc[i,'dns_ttl'] = ttl
                    
                df.loc[i,'dns_num_ip'] = num_ip
                df.loc[i,'dns_domain_rank'] = 'dns_domain_rank_NULL'
            else:
                dns_col = ['dns_ttl','dns_num_ip','dns_domain_rank']
                df.loc[i,dns_col] = [k+'NULL' for k in dns_col]
        else:
            #df.loc[i,dns_col] = 'NULL'
            df.loc[i,dns_col] = [k+'NULL' for k in dns_col]
    else:
        #df.loc[i,dns_col] = 'NULL'
        df.loc[i,dns_col] = [k+'NULL' for k in dns_col]
    return 
def TLS(data, i, df):

    scs_str = 'scs_str_NULL'
    server_name_str = 'server_name_str_NULL'
    c_key_len = '0'

    if data[i].__contains__('tls'):

        tls = data[i]['tls']
        if tls.__contains__('scs'):
            scs_str = tls['scs']
        if tls.__contains__('c_key_length'):
            c_key_len = tls['c_key_length'] 
        if tls.__contains__('c_extensions'):
            tls_ext = tls['c_extensions']
            if(tls_ext[0].__contains__('server_name')):
                server_name_str = tls_ext[0]['server_name']

    df.loc[i,'tls_scs'] = scs_str
    df.loc[i,'tls_ext_server_name'] = server_name_str
    df.loc[i,'tls_c_key_length'] = c_key_len

def Basic_Info(data, i, df, Type, file_name):

    if data[i].__contains__('sa'):
        df.loc[i,'sa'] = data[i]['sa']
    else:    
        df.loc[i,'sa'] = 'NULL'

    if data[i].__contains__('da'):
        df.loc[i,'da'] = data[i]['da']
    else:    
        df.loc[i,'da'] = 'NULL'
    
    if data[i].__contains__('sp'):
        df.loc[i,'sp'] = data[i]['sp']
    else:    
        df.loc[i,'sp'] = 'NULL'
    
    if data[i].__contains__('dp'):
        df.loc[i,'dp'] = data[i]['dp']
    else:    
        df.loc[i,'dp'] = 'NULL'
    
    if data[i].__contains__('pr'):
        df.loc[i,'pr'] = data[i]['pr']
    else:    
        df.loc[i,'pr'] = 'NULL'
    
    df.loc[i,'type'] = Type
    df.loc[i,'file_name'] = file_name

def Catgo(t):
    """
    if(opts.is_malware==1):
        return 'malware'
    """
    t = t.lower()
    #print('t=',t)
    if (t.find('email') !=  -1):
        return 'email'
    elif(t.find('chat') !=  -1):
        return 'chat'
    elif(t.find('youtube')!=-1 or t.find('vimeo')!=-1 or t.find('video')!=-1 or t.find('netflix')!=-1 or t.find('spotify')!=-1 ):
        return 'stream'
    elif(t.find('ftp')!=-1 or t.find('scp')!=-1 or t.find('file')!=-1):
        return 'file_trans'
    elif(t.find('audio')!=-1 or t.find('voip')!=-1):
        return 'voip'
    elif(t.find('torrent')!=-1):
        return 'trap2p'
    else:
        #print('browsing?')
        return 'browsing'


def Marcov(data, i, df):

    d=json.dumps(data[i], indent=4)
    #print(d)
    if data[i].__contains__('packets'):
        #print(1)
        packets = data[i]['packets']
        clas = []
        count = [[0]*20 for i in range(20)]
        matrix = [[0]*20 for i in range(20)]
        #print(len(packets))
        if len(packets) > 1:
            #print(len(packets))
            for j in range(len(packets)):
                if packets[j].__contains__('b'):
                    byte = packets[j]['b']
                    if packets[j]['dir'] == '>':
                        if byte == 1500:
                            clas.append(9)
                        elif byte < 1500:
                            clas.append(int(byte/150))
                    else:
                        if byte == 1500:
                            clas.append(19)
                        elif byte < 1500:
                            clas.append(int(byte/150)+10)
            for j in range(len(clas)-1):
                count[clas[j+1]][clas[j]] += 1
            total = 0
            for j in range(20):
                for k in range(20):
                    total = total + count[j][k]
            for j in range(20):
                for k in range(20):
                    if total > 0:
                        matrix[j][k] = count[j][k]/total
    else:
        matrix = np.zeros([20,20])
            
            
            
    for j in range(20):
        for k in range(20):
            splt_str = 'splt_' + str(j) + '_' + str(k) 
            df.loc[i,[splt_str]] = matrix[j][k]
    

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Making Traffic Table')
    parser.add_argument('--source_data_path', type=str,
                        default='../LinksToPCAP/youtube1.pcap', dest='source_data_path',
                        help='Path to source data')
    parser.add_argument('--output_path', type=str,
                        default='./tmp/table.csv', dest='output_path',
                        help='Path to output')
    """
    parser.add_argument('--is_malware', type=int,
                        default=0, dest='is_malware',
                        help='Label it if it is malware')
    """
    opts = parser.parse_args()

    #inputfile=opts.source_data_path
    #print('python input:',inputfile)
    Generator(opts.source_data_path)

