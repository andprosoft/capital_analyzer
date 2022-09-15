# -*- coding: utf-8 -*-
"""
Downloads and updates the price data of the shares.
"""

import requests
from datetime import datetime, timedelta
from time import sleep
import os
import numpy as np

from capital_analyzer.my_prop import dir_path_out_data, f_name_out_format


url_raw_wo = "https://www.wallstreet-online.de/_rpc/json/instrument/history/getHistoricalDataAsCSV?instId={}&marketId={}&fromDate={}&toDate={}&order=time,ASC&csv=true"
"""
Url to download the data from wallstreet-online.de
"""

#url_raw_ariva = "https://www.ariva.de/quote/historic/historic.csv?secu={}&boerse_id={}&clean_split=1&clean_payout=0&clean_bezug=1&min_time={}&max_time={}&trenner=%3B&go=Download"
url_raw_ariva = "https://www.ariva.de/quote/historic/historic.csv?{}&clean_split=1&clean_payout=0&clean_bezug=1&min_time={}&max_time={}&trenner=%3B&go=Download"
"""
Url to download the data from ariva.de
"""

min_date_global1 = datetime(2017, 1, 1)
"""
Startdate of the data, if a file is not existing. Should be before the
first trade.
"""


def download_data(share_data_dict):
    """
    Downloads and updates the price data of the shares.
    
    If for a given wnk the file is not present, the entire dataset starting
    from the date defined by ``min_date_global1`` will be downloaded. If the
    file is already present, then the data starting from 14 days ago (or
    from the last entry, whichever is earlier) will be downloaded. This 
    ensures, that the data is complete and up to date.
    """
    
    # 1. make parent directory
    os.makedirs(dir_path_out_data, exist_ok=True)
    
    # 2. format min and max date
    today = datetime.now()
    
    s_max_date = "{:02d}.{:02d}.{:04d}".format(today.day, today.month, today.year)
    min_date_global2 = today - timedelta(days=14)
    """
    Download at least last 14 days. Just in case, to ensure that the data is
    up to date.
    """
    
    # 3. iterate over each key
    key_list = share_data_dict.keys()
    
    for i_key, key in enumerate(key_list):
        print("current key ({} of {}): {}".format(i_key+1, len(key_list), key))
        
        download_dict = share_data_dict[key]['download_dict']
        
        # 3.1. check, if data shall be downloaded
        if(download_dict['download'] == 0):
            continue
        
        # 3.2. get the path of the output file
        f_name_out = f_name_out_format.format(key)
        f_path_out = os.path.join(dir_path_out_data, f_name_out)
        
        # 3.3. read existing data
        share_data_existing = read_share_data_from_csv(f_path_out)
        
        
        # 3.4. get start date to download
        if(len(share_data_existing) == 0):
            # no data available yet, start with first date defined
            min_date = min_date_global1
            
        else:
            # data already present
            # get last date
            # start from last date or date which was 14 days ago, whichever
            # is lower
            last_date = share_data_existing[-1]['share_date']
            
            if(last_date < min_date_global2):
                min_date = last_date - timedelta(days=2)  
                # download also 2 previous days, just in case
            else:
                min_date = min_date_global2
        
        # 3.5. format string for minimum date
        s_min_date = "{:02d}.{:02d}.{:04d}".format(min_date.day, min_date.month, min_date.year)
            
        # 3.6. configure url for the download
        
        # check, which service
        if(download_dict['data_service'] == "ariva"):
            s_list = []
            for key, item in download_dict.items():
                if(key in ["data_service", "download"]):
                    continue
                
                s_list.append("{}={}".format(key, item))
            
            s_params = "&".join(s_list)
            
            url = url_raw_ariva.format(s_params, s_min_date, s_max_date)
            read_routine = read_share_data_from_ariva
        elif(download_dict['data_service'] == "wo"):
            #raise ValueError("Wallstreet Online is not supported anymore! Use ariva istead!")
            print("Wallstreet Online is not supported anymore! Use ariva istead!")
            
            instId = download_dict['instId']
            marketId = download_dict['marketId']
            
            url = url_raw_wo.format(instId, marketId, s_min_date, s_max_date)
            read_routine = read_share_data_from_wo
        
        #print(url)
        # 3.7. download data and save it
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}
        page = requests.get(url, headers=headers)
        
        f_path_out_tmp = f_path_out + "_tmp"
        
        with open(f_path_out_tmp, 'w') as f:
            f.write(page.content.decode('utf-8'))
            
        # 3.8. read new data and merge it with the old data and write to file
        share_data_new = read_routine(f_path_out_tmp)
        
        share_data_merged = merge_share_data(share_data_existing, share_data_new)
        
        write_share_data_to_file(f_path_out, share_data_merged)
        
        # 3.9. remove temporary files
        os.remove(f_path_out_tmp)
        
        # 3.10 sleep for a random period to hide the crawler
        sleep(np.random.randint(1, 6))


def read_share_data_from_csv(f_path_in):
    share_data = []

    if(not os.path.exists(f_path_in)):
        return share_data
    
    with open(f_path_in, 'r') as f:
        lines = f.readlines()
        
    for line in lines[1:]:
        lp = line[:-1].split(";")
        
        # get rid of spaces
        for i_lp, lp_tmp in enumerate(lp):
            lp[i_lp] = lp_tmp.strip()
        
        share_date = datetime.strptime(lp[0], "%d.%m.%Y")
        share_open = lp[1]
        share_high = lp[2]
        share_low = lp[3]
        share_close = lp[4]
        
        sd = {}
        sd['share_date'] = share_date
        sd['share_open'] = share_open
        sd['share_high'] = share_high
        sd['share_low'] = share_low
        sd['share_close'] = share_close
        
        share_data.append(sd)
        
    share_data = sorted(share_data, key=lambda x: x['share_date'])
        
    return share_data
        
def read_share_data_from_wo(f_path_in):
    share_data = []
    
    with open(f_path_in, 'r') as f:
        lines = f.readlines()
        
    for line in lines[1:]:
        line_parts = line[:-1].split(';')
        
        for i_line_part, line_part in enumerate(line_parts):
            if(line_part.startswith('"""')):
                line_part = line_part[3:-3]
                
            if(i_line_part > 0):
                line_part = line_part.replace('.', '').replace(',', '.')
                
            line_parts[i_line_part] = line_part
            
        line_part = line_parts[0]
        lp_parts = line_part.split('.')
        
        year = int(lp_parts[2]) + 2000
        month = int(lp_parts[1])
        day = int(lp_parts[0])
        
        date = datetime(year=year, month=month, day=day)
        share_date = date
        
        share_open = line_parts[1]
        share_high = line_parts[2]
        share_low = line_parts[3]
        share_close = line_parts[4]
        
        sd = {}
        sd['share_date'] = share_date
        sd['share_open'] = share_open
        sd['share_high'] = share_high
        sd['share_low'] = share_low
        sd['share_close'] = share_close
        
        share_data.append(sd)
        
    share_data = sorted(share_data, key=lambda x: x['share_date'])
    
    return share_data

def read_share_data_from_ariva(f_path_in):
    share_data = []
    
    with open(f_path_in, 'r') as f:
        lines = f.readlines()
        
    for line in lines[1:]:
        line_parts = line[:-1].split(';')
        
        if(len(line_parts) <= 1):
            continue
        
        for i_line_part, line_part in enumerate(line_parts):
            if(i_line_part > 0):
                line_part = line_part.replace('.', '').replace(',', '.')
                
            line_parts[i_line_part] = line_part
    
        share_date = datetime.strptime(line_parts[0], "%Y-%m-%d")
        share_open = line_parts[1]
        share_high = line_parts[2]
        share_low = line_parts[3]
        share_close = line_parts[4]
        
        sd = {}
        sd['share_date'] = share_date
        sd['share_open'] = share_open
        sd['share_high'] = share_high
        sd['share_low'] = share_low
        sd['share_close'] = share_close
        
        share_data.append(sd)
        
    share_data = sorted(share_data, key=lambda x: x['share_date'])
    
    return share_data

def merge_share_data(share_data1, share_data2):
    share_data_new = []
    
    for sd1 in share_data1:
        share_data_new.append(sd1)
        
    for sd2 in share_data2:
        i_sd = -1
        
        for i_sd_new, sd_new in enumerate(share_data_new):
            if(sd_new['share_date'] == sd2['share_date']):
                i_sd = i_sd_new
                break
                
        if(i_sd == -1):
            share_data_new.append(sd2)
        else:
            share_data_new[i_sd] = sd2
                
    share_data_new = sorted(share_data_new, key=lambda x: x['share_date'])
    
    return share_data_new

def write_share_data_to_file(f_path_out, share_data):
    lines = []
    
    lines.append("Datum;Eroeffnung;Hoch;Tief;Schluss\n")
    
    for sd in share_data:
        share_date = sd['share_date']
        share_open = sd['share_open']
        share_high = sd['share_high']
        share_low = sd['share_low']
        share_close = sd['share_close']
        
        s_date = datetime.strftime(share_date, "%d.%m.%Y")
        
        s = "{}; {}; {}; {}; {}\n".format(s_date, share_open, share_high, share_low, share_close)
        lines.append(s)
    
    with open(f_path_out, 'w') as f:
        f.writelines(lines)
    


if __name__ == "__main__":
    download_data()

    print("done :)")
