#!/usr/bin/env python

"""
get-yahoo-quotes.py:  Script to download Yahoo historical quotes using the new cookie authenticated site.
 Usage: get-yahoo-quotes SYMBOL
 History
"""

import re
import sys
import time
import datetime
import requests


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
    url = "https://finance.yahoo.com/quote/%s/?p=%s" % (symbol, symbol)
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


def get_data(symbol, start_date, end_date, cookie, crumb):
    filename = '%s.csv' % (symbol)
    url = "https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%s&period2=%s&interval=1d&events=history&crumb=%s" % (symbol, start_date, end_date, crumb)
    response = requests.get(url, cookies=cookie)
    with open (filename, 'wb') as handle:
        for block in response.iter_content(1024):
            handle.write(block)


def get_now_epoch():
    # @see https://www.linuxquestions.org/questions/programming-9/python-datetime-to-epoch-4175520007/#post5244109
    return int(time.time())

def datestring_to_timestamp(s):
    return int(time.mktime(datetime.datetime.strptime(s, "%d/%m/%Y").timetuple()))


def download_quotes(symbol, start_date_string=None, end_date_string=None):
    if start_date_string is None:
        start_date = 0
    else:
        start_date = datestring_to_timestamp(start_date_string)
    
    if end_date_string is None:
        end_date = get_now_epoch()
    else:
        end_date = datestring_to_timestamp(end_date_string)
    
    cookie, crumb = get_cookie_crumb(symbol)
    get_data(symbol, start_date, end_date, cookie, crumb)


if __name__ == '__main__':
    # If we have at least one parameter go ahead and loop overa all the parameters assuming they are symbols
    symbols = ['^IBEX','SAN.MC', 'BBVA.MC', 'MTS.MC', 'ITX.MC'] 
    if len(sys.argv) > 2:
        start_date_string = sys.argv[1]
        end_date_string = sys.argv[2]
    elif len(sys.argv) >1:
        start_date_string = sys.argv[1]
        end_date_string = None
    else:
        start_date_string = None
        end_date_string = None

    for symbol in symbols:
            print("--------------------------------------------------")
            print("Downloading %s to %s.csv" % (symbol, symbol))
            download_quotes(symbol, start_date_string=start_date_string, end_date_string=end_date_string)
    print("--------------------------------------------------")
