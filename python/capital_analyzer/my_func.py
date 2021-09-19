# -*- coding: utf-8 -*-
"""
Module with helper functions.
"""

import os

from capital_analyzer.my_prop import dir_path_out_data, f_name_out_format


def get_f_path_chart_data(wnk):
    """
    Raturns the path of the chart data file to the given identifier.
    
    
    Parameters
    ----------
    wnk : string
        Identifier of the share, of which to obtain the path.
        
    
    Returns
    -------
    f_path_chart : string
        Path to the chart data file.
    """

    f_path_chart = os.path.join(dir_path_out_data, f_name_out_format.format(wnk))
    
    return f_path_chart


def format_capital(capital, currency="€", add_plus_sign=False):
    """
    Formats the capital in a human friendly format.
    
    Inserts a space as the separator for thousands.
    """
    
    s_format = "{:,.2f}"
    if(add_plus_sign):
        s_format = "{:+,.2f}"
    
    # 1. format value
    s_capital = s_format.format(capital).replace(",", " ")
     
    # 2. add  currency
    s = "{} {}".format(s_capital, currency)
    
    # 3. return result
    return s
    
