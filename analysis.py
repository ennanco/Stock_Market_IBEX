import os
import re
import sys
import math
import datetime
import time
import requests

import pandas as pd
import numpy as np

yahoo_stock_url = "https://finance.yahoo.com/quote/%s/?p=%s" 
yahoo_data_url =  "https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%s&period2=%s&interval=1d&events=history&crumb=%s"

####################################
#########Utility funcions###########
####################################

def if_not_create_folder(name):
    """check the existance of a folder and if  it is needed, the folder is created""" 
    if not os.path.exists(name):
        os.makedirs(name)


def datestring_to_timestamp(s, default=0):
    """ This function transforms an string with a date into a linux-format timestamp"""
    if s is None:
        return default
    else: 
        return int(time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d").timetuple())) 


#####################################
### Functions to download the data###
#####################################

def split_crumb_store(v):
    return v.split(':')[2].strip('"')


def find_crumb_store(lines):
    # Looking for
    # ,"CrumbStore":{"crumb":"9q.A4D1c.b9
    for l in lines:
        if re.findall(r'CrumbStore', l):
            return l
    print("Did not find CrumbStore")


def get_cookie_value(r):
    return {'B': r.cookies['B']}

def get_page_data(symbol):
    url = yahoo_stock_url % (symbol, symbol)
    r = requests.get(url)
    cookie = get_cookie_value(r)

    # Code to replace possible \u002F value
    # ,"CrumbStore":{"crumb":"FWP\u002F5EFll3U"
    # FWP\u002F5EFll3U
    lines = r.content.decode('unicode-escape').strip(). replace('}', '\n')
    return cookie, lines.split('\n')


def get_cookie_crumb(symbol):
    cookie, lines = get_page_data(symbol)
    crumb = split_crumb_store(find_crumb_store(lines))
    return cookie, crumb


def get_data(symbol, start_date, end_date,filename, cookie, crumb):
    url = yahoo_data_url % (symbol, start_date, end_date, crumb)
    response = requests.get(url, cookies=cookie)
    with open (filename, 'wb') as handle:
        for block in response.iter_content(1024):
            handle.write(block)


def download_symbol_if_need(symbol, start_date, end_date, folder):
    filename = '%s/%s.csv' % (folder,symbol)
    if not os.path.exists(filename):
        print('---------------------------------')
        print('Downloading...  %s' % symbol)
        print('---------------------------------')

        cookie, crumb = get_cookie_crumb(symbol)
        get_data(symbol, start_date, end_date, filename, cookie, crumb)

def download_symbols(symbols, start_date_str=None, end_date_str=None):
    start_date = datestring_to_timestamp(start_date_str, default= 0)
    end_date = datestring_to_timestamp(end_date_str, default= int(time.time()))
    folder_name = start_date_str+"_"+end_date_str
    if_not_create_folder(folder_name)
    for symbol in symbols:
        download_symbol_if_need(symbol, start_date, end_date, folder_name)

####################################
### Prepare the data into pandas ###
####################################


def read_stock(name, prefix='.', suffix='csv'):
    stock_path = "%s/%s.%s" % (prefix, name, suffix)
    tmp_df = pd.read_csv(stock_path,index_col="Date", parse_dates=True,
                           usecols= ['Date', 'Adj Close'], na_values = ['nan'])
    tmp_df = tmp_df.rename(columns={'Adj Close':name})
    return tmp_df

def get_stocks_data(index_name, stocks_name_list, start_date_str= None, end_date_str=None):
    folder = start_date_str+'_'+end_date_str
    dates = pd.date_range(start_date_str, end_date_str)
    df_stocks = pd.DataFrame(index=dates)

    
    df_stocks = df_stocks.join(read_stock(index_name, prefix=folder), how='inner')
    df_stocks = df_stocks.dropna()

    for symbol in stocks_name_list:
        df_stocks = df_stocks.join(read_stock(symbol, prefix=folder), how='left') 

    df_stocks.fillna(method='ffill', inplace=True)
    df_stocks.fillna(method='bfill', inplace=True)

    return df_stocks




if __name__ == '__main__':
    # If we have at least one parameter go ahead and loop overa all the parameters assuming they are symbols
    index = '^IBEX'
    symbols = ['ANA.MC', 'ACX.MC', 'ACS.MC', 'AENA.MC', 'AMS.MC', 'MTS.MC', 'SAB.MC',
               'SAN.MC', 'BKIA.MC', 'BKT.MC', 'BBVA.MC', 'CABK.MC', 'CLNX.MC', 'CIE.MC', 
               'ENG.MC', 'ENC.MC', 'ELE.MC', 'FER.MC', 'GRF.MC', 'IAG.MC', 'IBE.MC',
               'ITX.MC', 'IDR.MC', 'COL.MC', 'MAP.MC', 'TL5.MC', 'MEL.MC', 'MRL.MC',
               'NTGY.MC', 'REE.MC', 'REP.MC', 'SGRE.MC', 'TRE.MC', 'TEF.MC', 'VIS.MC' ] 

    if len(sys.argv) > 2:
        start_date_string = sys.argv[1]
        end_date_string = sys.argv[2]
    elif len(sys.argv) >1:
        start_date_string = sys.argv[1]
        end_date_string = None
    else:
        start_date_string = None
        end_date_string = None
   
    download_symbols([index]+symbols, start_date_string, end_date_string)
    df_stocks_history = get_stocks_data(index, symbols, start_date_string, end_date_string).apply(pd.to_numeric, errors='coerce')
    df_stocks_history.to_csv('IBEX_2018.csv')

    #df_stocks_history['Mio'] = np.sum(wallet * df_stocks_history, axis=1)

    #######################################################################
    ############ Perform Analysis of the historical data###################
    #######################################################################

    daily = (df_stocks_history/ df_stocks_history.shift(1) -1)
    daily = daily.dropna()

    


    results = pd.DataFrame()
    results['Rent. Anual'] = ((df_stocks_history.ix[-1, :]/df_stocks_history.ix[0,:]) - 1)*100
    results['Rent. Media Diaria'] = daily.mean()*100 
    results['Rent. Varianza Diaria'] = daily.std()*100
    results['Sharp'] = np.sqrt(daily.shape[0])*results['Rent. Media Diaria']/results['Rent. Varianza Diaria']
    results['Beta'] = np.nan

    for s in results.index: 
       tmp = np.cov(daily[s],daily['^IBEX']) 
       results['Beta'][s]=tmp[0,1]/tmp[1,1]
 
    results['Alpha'] = results['Rent. Media Diaria'] - results['Beta']*results['Rent. Media Diaria']['^IBEX']
    print(results) 
