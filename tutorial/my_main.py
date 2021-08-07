# -*- coding: utf-8 -*-
"""
Main File to run the analysis.
"""

from datetime import datetime

import site
site.addsitedir("../python")

from capital_analyzer.analyze_trades import run_analyze

from trades import get_trades, get_dividends
from share_data import get_share_data_dict, get_split_list


def analyze_trades_demo():
    """
    Main function to run the analysis.
    """

    # set some configuration files
    dir_path_out_html = r"./html"
    dir_name_images = "images"
    f_name_html = "index.html"
    
    lin_thresh = 3000
    currency = "€"
    
    # 1. get data
    list_trades = get_trades()
    list_dividends = get_dividends()
    share_data_dict = get_share_data_dict()
    split_list = get_split_list()

    #-------------------------------------------------------------------------#
    # create a list of all categories to compare
    # each entry is a dictionary with the following keys:
    #    - 'category_list': list of categories to include. Can also be 'all'
    #      include every share
    #    - 'displayname': Displayname of the selection
    #    - 'color: color of the line. Use a matplotlib compatible color
    #      (see https://matplotlib.org/stable/gallery/color/named_colors.html)
    # This list will be used to plot the evolution of each selection (in the
    # section 'Capital Estimator')
    category_compare_list1 = []
    category_compare_list1.append({'category_list': ['A'],
                                   'displayname': "Conservative",
                                   'color': "tab:blue"})
    category_compare_list1.append({'category_list': ['crypto'],
                                   'displayname': "Crypto Currencies",
                                   'color': "tab:orange"})
    category_compare_list1.append({'category_list': "all",
                                   'displayname': "All",
                                   'color': "tab:green"})

    #-------------------------------------------------------------------------#
    # create a list of all categories to compare
    # entries are the same as above
    # This list will be used to compare an index-based performance. This
    # enables a comparison of the performance to the market performance.
    # See section 'Personal Index'
    category_compare_list2 = category_compare_list1

    #-------------------------------------------------------------------------#
    # Define some reference configurations to compare your performance
    # again a theoretical performance. If you are above the theoretical
    # performance, then you can predict your final outcome
    # the model of the theoretical evolution is quite simple. Define a
    # start capital, a monthly payment and a yearly interest rate. It
    # is assumed, that the capital will grow with this interest rate every
    # year. If taking an average interest rate (e.g. 7%), this will give
    # reasonable results.
    start_date_reference_config = datetime(2021, 3, 1)
    end_date_reference_config_table = datetime(2062, 2, 17)

    reference_config_list = []
    reference_config_list.append({
        'args': {
            'start_capital' : 0,
            'monthly_payment' : 25,
            'interest' : 1.07,
            'start_date' : start_date_reference_config
        },
        'color': (197 / 255, 90 / 255, 17 / 255)
    })
    reference_config_list.append({
        'args': {
            'start_capital' : 0,
            'monthly_payment' : 25,
            'interest' : 1.10,
            'start_date' : start_date_reference_config
        },
        'color': (244 / 255, 177 / 255, 131 / 255)
    })

    #-------------------------------------------------------------------------#
    # Create a list for the groups of which to compute the realtive amounts.
    # has the same structure as above, the key 'color' can be ommited here.
    categories_rel_amount_list = category_compare_list1

    #-------------------------------------------------------------------------#
    # create configuration dictionary
    
    config = {}
    config['share_data_dict'] = share_data_dict
    config['list_trades'] = list_trades
    config['list_dividends'] = list_dividends
    config['split_list'] = split_list
    
    
    config['dir_path_out_html'] = dir_path_out_html
    config['dir_name_images'] = dir_name_images
    config['f_name_html'] = f_name_html
    config['lin_thresh'] = lin_thresh
    config['currency'] = currency
    
    config['category_compare_list1'] = category_compare_list1
    config['category_compare_list2'] = category_compare_list2
    config['reference_config_list'] = reference_config_list
    config['end_date_reference_config_table'] = end_date_reference_config_table
    #config['end_date_reference_config_plot'] = end_date_reference_config_plot
    config['categories_rel_amount_list'] = categories_rel_amount_list
    
    # 3. analyze data
    run_analyze(config)


if __name__ == "__main__":
    analyze_trades_demo()
