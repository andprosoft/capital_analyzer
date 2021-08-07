# -*- coding: utf-8 -*-

import scipy.stats
import numpy as np

from datetime import datetime

def test_func1():
    f_path_new = r"N:\total_val_new.txt"
    f_path_old = r"N:\total_val_old.txt"
    
    total_val_new = np.loadtxt(f_path_new)
    total_val_old = np.loadtxt(f_path_old)
    
    global diff
    diff = total_val_new - total_val_old
    
    
def test_func2():
    split_list = []
    split_list.append(("A12GS7", datetime(2020,  5, 11), 2.0, "A2P4EC"))
    split_list.append(("A2P4EC", datetime(2020,  6, 11), 3.0, "A2P4EB"))
    split_list.append(("A2N6DH", datetime(2020, 12, 16), 1.0/20.0, "A2QJD4"))
    
    wkn = "A12GS7"
    trade_date = datetime(2020, 1, 14)
    
    wkn_tmp, fac = get_id_fac_from_split_for_amount(split_list, wkn, trade_date)
    print(wkn_tmp, fac)
    wkn_tmp, fac = get_id_fac_from_split_for_value(split_list, wkn)
    print(wkn_tmp, fac)
    
    
def get_id_fac_from_split_for_amount(split_list, id_share, trade_date):
    """
    Fancy documentation.
    """
    
    return get_id_fac_from_split(split_list, id_share, trade_date)
    
def get_id_fac_from_split_for_value(split_list, id_share):
    """
    Fancy documentation.
    """
    
    return get_id_fac_from_split(split_list, id_share, trade_date=None)
    
def get_id_fac_from_split(split_list, id_share, trade_date=None):
    """
    Fancy documentation.
    """
    
    split_found = True
    fac = 1.0
    id_new = id_share
    
    while(split_found):
        split_found = False
        
        for split_data in split_list:
            id_split_old = split_data[0]
            split_date = split_data[1]
            split_fac = split_data[2]
            id_split_new = split_data[3]
            
            if((trade_date is None or trade_date.date() >= split_date.date())
                and id_new == id_split_old):
                fac = fac * split_fac
                id_new = id_split_new
                split_found = True
                
    return id_new, fac
    
    
    
if __name__ == "__main__":
    #test_func1()
    test_func2()
