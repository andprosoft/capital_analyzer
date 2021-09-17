# -*- coding: utf-8 -*-
"""
Analyzes and evaluates the traded. The respective html site will be
updated.
"""

from __future__ import print_function, division
from datetime import datetime, timedelta
from dateutil.rrule import rrule, DAILY
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
import numpy as np
from matplotlib import colors
import calendar
import os
from bs4 import BeautifulSoup

from capital_analyzer.my_func import get_f_path_chart_data, format_capital

SHOW_PLOTS_IN_CONSOLE = False
FIGWIDTH = 12
FIGHEIGHT = 8
DPI = 300


def run_analyze(config):
    """
    Analyzes the trades, creates the respective images and updates the html.
    """
    
    share_data_dict = config['share_data_dict']
    list_trades = config['list_trades']
    list_dividends = config['list_dividends']
    split_list = config['split_list']
    
    dir_path_out_html = config['dir_path_out_html']
    f_name_html = config['f_name_html']
    dir_name_images = config['dir_name_images']
    f_name_template = config.get('f_name_template', "index_template.html")
    
    f_path_template = os.path.join(dir_path_out_html, f_name_template)
    f_path_html = os.path.join(dir_path_out_html, f_name_html)

    dir_path_out_images = os.path.join(dir_path_out_html, dir_name_images)
    os.makedirs(dir_path_out_images, exist_ok=True)

    list_trades.sort(key=lambda x: x[0])
    list_dividends.sort(key=lambda x: x[0])

    ###########################################################################
    # 0. create some helper variables to enable or disable some plots
    # this is helpful for debugging or when testing new plots. With these
    # variables, all the plots except the new one can be disabled except the
    # new one, which saves a lot of time.
    
    # master variable. if set to True, then all plots will be created,
    # matter of the values of the other variables. Also, only then will
    # the html file be updated.
    do_all = True

    # variables to enable or disable each plot
    show_chart_share_evolution = False
    
    print_total_value_end_of_month = False

    show_chart_share_rel_amount = False
    chart_share_gain_abs_rel = False
    
    show_chart_personal_index = True
    
    is_calculate_best_worst_days = True
    
    is_update_html = True
    is_update_html = do_all == True

    ## show_chart_total_value_expenses = False
    ## show_chart_total_gain = False
    
    category_compare_list1 = config['category_compare_list1']
    category_compare_list2 = config['category_compare_list2']
    reference_config_list = config['reference_config_list'] 
    end_date_reference_config_table = config['end_date_reference_config_table'] 
    end_date_reference_config_plot = config.get('end_date_reference_config_plot', None)
    categories_rel_amount_list = config['categories_rel_amount_list']
    lin_thresh = config['lin_thresh']
    currency = config['currency']

    ###########################################################################
    # 1. Find first date of trade and find all traded shares
    
    list_trade_dates = sorted(set([trade_data[0] for trade_data in list_trades]))
    #list_shares = sorted(set([trade_data[1] for trade_data in list_trades]))
    list_shares = sorted(share_data_dict.keys())
    
    first_date = list_trade_dates[0]
    
    # configure start and end dates
    # start date is the first day of the month of the first trade
    # last date is the day before today (because the provided data does not
    # have an entry for today)
    first_date_it = datetime(first_date.year, first_date.month, 1)
    last_date_it = datetime(datetime.now().year, datetime.now().month, datetime.now().day) - timedelta(days=1)

    # using close values is the default in the community.
    # when false, use open value
    use_close_value = True
    
    
    ###########################################################################
    # 2. calculate the total amount of each share at every day between 
    # start and end.
    
    
    global share_amount_data_list, share_amount_dates, share_amount_data, total_expenses_list
     # a list containing the amount of share at the given day
     # (stored in a dictionary)
    share_amount_data_list = []
    # a list of the corresponding dates
    share_amount_dates = []
    # list of the total expenses at the given day
    total_expenses_list = []
    
    # iterate over each day
    for current_date in rrule(DAILY, dtstart=first_date_it, until=last_date_it):
        ### print(current_date.date())
        
        # 2.1. create empty dictionary for this day
        # it will store the share amount at the given date
        share_amount_data = dict((el, 0) for el in list_shares)
        total_expenses = 0.0
        
        # 2.2. iterate over each trade
        for trade_data in list_trades:
            if(current_date.date() >= trade_data[0].date()):
                wkn = trade_data[1]
                amount = trade_data[2]
                expenses = trade_data[3]

                '''
                share_amount_data[wnk] = share_amount_data[wnk] + amount
                total_expenses += expenses
                '''
                
                wkn_new, fac = get_id_fac_from_split_for_amount(split_list, wkn, current_date)
                share_amount_data[wkn_new] = share_amount_data[wkn_new] + fac*amount
                total_expenses += expenses
                
                
            else:
                # list is sorted
                break
        
        # 2.3. save data
        share_amount_dates.append(current_date)
        share_amount_data_list.append(share_amount_data)
        total_expenses_list.append(total_expenses)
        
    ###########################################################################
    # 3. read chart data

    chart_data = get_chart_data(share_data_dict)
    
    ###########################################################################
    # 4. convert share amounts into a value with respect to the close date
    
    # 4.1. create resulting dictionary
    # values will be stored for each share separately in a list
    global share_depot_values
    share_depot_values = dict((key, len(share_amount_dates)*[None]) for key in list_shares)
    
    # 4.2. iterate over each date
    for i, share_amount_data in enumerate(share_amount_data_list):
        share_amount_date = share_amount_dates[i]
        
        # 4.2.1. iterate over each keay
        for key in share_amount_data:
            chart_date_list = chart_data[key]['date_list']
            open_values_list = chart_data[key]['open_values_list']
            close_values_list = chart_data[key]['close_values_list']
            
            # 4.2.1.1. if amout is (near to) zero, then just enter ``None``
            # as value. Do not check for equality since rounding error
            # can occur
            if(share_amount_data[key] < 1e-5):
                continue
            
            # find close value
            # for this, iterate over each entry in the chart data
            for i_date, date in enumerate(chart_date_list):
                
                # we need to find the largest date in the chart data that is
                # equal or lower the current date
                # for example, if the current date is a sunday, we
                # need the closing value of the previous friday
                # for this, update the share price after each iteration
                # if the date is lower equal the current date
                if(date <= share_amount_date):
                    if(use_close_value):
                        share_price = close_values_list[i_date]
                    else:
                        share_price = open_values_list[i_date]
                    
                # we have now come to a date in the chart data, that is larger
                # than the current date
                # or we have come to an end of the list
                if(date > share_amount_date 
                   or i_date == len(chart_date_list) - 1):
                    # calculate value = price * amount
                    price_in_depot = share_price * share_amount_data[key]
                    
                    #  check again for numerical inaccuracies
                    if(price_in_depot < 0.1):
                        price_in_depot = None
                        
                    key_new, fac = get_id_fac_from_split_for_value(split_list, key)
                        
                    # save value
                    share_depot_values[key_new][i] = price_in_depot
                    
                    
                    # break loop
                    break
            else:
                # one should never enter this branch
                share_depot_values[key].append(share_depot_values[key][-1])
                raise ValueError("Share price not found!")

                
    ###########################################################################
    # 5. calculat ethe total value and the total gain
    
    # 5.1. create resulting arrays
    global total_value_list
    total_value_list = []
    total_gain_abs = []
    
    # 5.2. iterate over each date
    for i_date in range(len(share_amount_dates)):
        
        # sum all values
        val = 0
        for key in share_depot_values.keys():
            if share_depot_values[key][i_date] is not None:
                val = val + share_depot_values[key][i_date]
        
        # save data
        total_value_list.append(val)
        
        # absolute gain = total value - expenses
        total_gain_abs.append(val - total_expenses_list[i_date])
        
        # a relative gain should not be computet here, because the total
        # expenses might be negative (e.g. shares sold with a gain)
        
    ###########################################################################
    # 6. create diagrams
    
    # 6.1. share evolution
    if(do_all or show_chart_share_evolution):
        config_tmp = {}
        config_tmp['share_amount_dates'] = share_amount_dates
        config_tmp['share_depot_values'] = share_depot_values
        config_tmp['share_data_dict'] = share_data_dict
        config_tmp['lin_thresh'] = lin_thresh
        config_tmp['currency'] = currency
        config_tmp['dir_path_out_images'] = dir_path_out_images
        
        create_chart_share_evolution(config_tmp)
        
    # 6.2. plot total value at the end of each month

    if(do_all or print_total_value_end_of_month):
        
        # 6.2.1. evolution between first trade and today (for plot)
        config_tmp = {}
        config_tmp['share_amount_dates'] = share_amount_dates
        config_tmp['share_depot_values'] = share_depot_values
        config_tmp['share_data_dict'] = share_data_dict
        config_tmp['category_compare_list'] = category_compare_list1
        config_tmp['reference_config_list'] = reference_config_list
        config_tmp['end_date'] = end_date_reference_config_plot
        config_tmp['currency'] = currency
        config_tmp['dir_path_out_images'] = dir_path_out_images
        
        res = evaluate_categories_total_and_reference(config_tmp)
        
        date_list_month = res['date_list_month']
        amount_list_month = res['amount_list_month']
        category_list_names = [cll['displayname'] for cll in category_compare_list1]
        
        # 6.2.2. evolution of the reference configuration (for table)
        config_tmp = {}
        config_tmp['reference_config_list'] = reference_config_list
        config_tmp['end_date'] = end_date_reference_config_table

        reference_evolution_res_list = get_value_reference_evolution(
            config_tmp)
        
    else:
        # create empty list, so that update_html does not throw an error
        date_list_month = []
        amount_list_month = []
        category_list_names = []
        reference_config_list = []
        reference_evolution_res_list = []

    
    # 6.3. create diagrams showing the distribution of the shares for
    # different category selections

    if(do_all or show_chart_share_rel_amount):
        res_list_share_rel_amount = []
        
        for cra in categories_rel_amount_list:
            config_tmp = {}
            config_tmp['share_depot_values'] = share_depot_values
            config_tmp['share_data_dict'] = share_data_dict
            config_tmp['category_config'] = cra
            config_tmp['currency'] = currency
            config_tmp['dir_path_out_images'] = dir_path_out_images
            
            res = create_chart_share_rel_amount(config_tmp)
            res_list_share_rel_amount.append(res)
    else:
        res_list_share_rel_amount = []


    if(do_all or chart_share_gain_abs_rel):
        config_tmp = {}
        config_tmp['share_data_dict'] = share_data_dict
        config_tmp['list_trades'] = list_trades
        config_tmp['share_amount_dates'] = share_amount_dates
        config_tmp['share_depot_values'] = share_depot_values
        config_tmp['split_list'] = split_list
        config_tmp['currency'] = currency
        config_tmp['dir_path_out_images'] = dir_path_out_images

        create_chart_share_gain_abs_rel_single(config_tmp)
        

    if(do_all or show_chart_personal_index):
        if(SHOW_PLOTS_IN_CONSOLE):
            print("Performance comparison")
        
        config_tmp = {}
        config_tmp['share_data_dict'] = share_data_dict
        config_tmp['share_amount_dates'] = share_amount_dates
        config_tmp['share_depot_values'] = share_depot_values
        config_tmp['list_trades'] = list_trades
        config_tmp['chart_data'] = chart_data
        config_tmp['category_compare_list'] = category_compare_list2
        config_tmp['dir_path_out_images'] = dir_path_out_images
        
        create_chart_personal_index(config_tmp)

    if(do_all or is_calculate_best_worst_days):
        config_tmp = {}
        config_tmp['share_data_dict'] = share_data_dict
        config_tmp['share_amount_dates'] = share_amount_dates
        config_tmp['share_depot_values'] = share_depot_values
        config_tmp['list_trades'] = list_trades
        config_tmp['category_compare_list'] = category_compare_list1
        
        res_best_worst_days = calculate_best_worst_days(config_tmp)
    else:
        res_best_worst_days = []
    
    if(is_update_html):
        config_tmp = {}
        config_tmp['date_list_month'] = date_list_month
        config_tmp['amount_list_month'] = amount_list_month
        config_tmp['category_list_names'] = category_list_names
        config_tmp['reference_evolution_res_list'] = reference_evolution_res_list
        config_tmp['reference_config_list'] = reference_config_list
        config_tmp['res_list_share_rel_amount'] = res_list_share_rel_amount
        config_tmp['res_best_worst_days'] = res_best_worst_days
        config_tmp['f_path_template'] = f_path_template
        config_tmp['f_path_html'] = f_path_html
        config_tmp['dir_name_images'] = dir_name_images
        
        update_html(config_tmp)
    

def create_chart_share_evolution(config):
    """
    Fancy documentation.
    
    Creates the chart where the evolution of each share is shown separately.
    """
    
    share_amount_dates = config['share_amount_dates']
    share_depot_values = config['share_depot_values']
    share_data_dict = config['share_data_dict']
    lin_thresh = config['lin_thresh']
    currency = config['currency']
    dir_path_out_images = config['dir_path_out_images']
    
    # 1. create figure and axis
    fig = plt.figure()
    ax = fig.gca()
    
    # 2. sort the keys by the name of the share
    key_data_list = []
    for key in share_depot_values.keys():
        key_data_list.append(
            (key, share_data_dict[key]['displayname'], 
             share_data_dict[key]['color']))
        
    key_data_list = sorted(key_data_list, key=lambda x: x[1].lower())
    
    xmin = np.inf
    xmax = -np.inf
    
    # 3. plot evolution for each share
    for key_label in key_data_list:
        key = key_label[0]
        displayname = key_label[1]
        color = key_label[2]
        vals = share_depot_values[key]
        
        if(vals.count(None) == len(vals)):
            continue
        
        ax.plot(share_amount_dates, share_depot_values[key], 
                label=displayname, color=color, alpha=1.0)
        
        # get dates where value is not none --> value is existing
        i_date_list = [i for i, v in enumerate(share_depot_values[key]) 
                       if v is not None]
        
        # get xmin and xmax --> use date2num to convert to a mpl compatible
        # format
        xmin = min(xmin, date2num(share_amount_dates[i_date_list[0]]))
        xmax = max(xmax, date2num(share_amount_dates[i_date_list[-1]]))
    
    # set limits of x-axis
    ax.set_xlim([xmin, xmax])
    
    # 4. configure figure
    fig.set_figwidth(FIGWIDTH)
    fig.set_figheight(FIGHEIGHT)
    
    ax.legend(loc="upper left", ncol=3)
    ax.grid()
    
    # set lower limit of y axis to 0
    ax.set_ylim([0, ax.get_ylim()[1]])
    
    ax.set_xlabel("Date")
    ax.set_ylabel("Share Value ({})".format(currency))
    
    #ax.set_yscale('log')
    ax.set_yscale('symlog', linthresh=lin_thresh)
    
    # 5. set custom y ticks
    # TODO: check, what is actually going on
    ylim = ax.get_ylim()
    
    yticks = []
    yticklabels = []
    current_power = 3
    current_tick = 0
    
    while(current_tick < ylim[1]):
        for i in range(0, 10):
            current_tick = (i + 1) * 10**current_power
            
            lbl = "{:,.0f}".format(current_tick).replace(",", " ")
            
            if(current_tick < ylim[1]):
                yticks.append(current_tick)
                yticklabels.append(lbl)
            
        current_power += 1

    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels)
    
    # 6. pad layout of figure and save it
    fig.tight_layout()
    
    f_path_out = os.path.join(dir_path_out_images, "share_evolution_all.{}")
    fig.savefig(f_path_out.format("png"), dpi=DPI)
    fig.savefig(f_path_out.format("pdf"), dpi=DPI)
    
    if(SHOW_PLOTS_IN_CONSOLE):
        plt.show()
    else:
        plt.close()


def create_chart_share_rel_amount(config):
    """
    Creates a chart showing the realitve distribution of the shares
    for the given category selection.
    """
    share_depot_values = config['share_depot_values']
    share_data_dict = config['share_data_dict']
    category_list = config['category_config']['category_list']
    displayname = config['category_config']['displayname']
    currency = config['currency']
    dir_path_out_images = config['dir_path_out_images']
    
    # 0. define lists that will be used for plotting
    label_list = []  # list of the names of the shares
    value_list = []  # list of the current value
    color_list = []  # list of the colors
    
    # 1. get all shares that belong the selected categories
    key_list_valid = get_keys_from_category_list(
        share_data_dict, category_list)
    
    # 2. iterate over each valid key
    for key in key_list_valid:
        # check, value of the share is larger than 0.1
        if(share_depot_values[key][-1] is not None
           and share_depot_values[key][-1] > 0.1):
            label_list.append(share_data_dict[key]['displayname'])
            value_list.append(share_depot_values[key][-1])
            color_list.append(share_data_dict[key]['color'])
            
    # 3. calculate relative amounts
    # +convert lists to arrays (for easier sorting)
    value_list_abs = np.asarray(value_list)
    value_list_rel = value_list_abs / np.sum(value_list)
    label_list = np.asarray(label_list)
    color_list = np.asarray(color_list)
    
    # 4. sort shares according to their current value
    val_args = value_list_abs.argsort().astype(int)
    
    # sort the respective lists
    value_list_abs = value_list_abs[val_args]
    value_list_rel = value_list_rel[val_args]
    label_list = label_list[val_args]
    color_list = color_list[val_args]
    
    # 5. plot results
    
    # calculate delta_x of the label for each share, with respect
    # to the maximum relative amount
    # this ensures, that for each selection, the text is approximately
    # at the same x-position
    max_val_rel = np.max(value_list_rel)
    dx_text = 0.005*max_val_rel * 100
    
    # 5.1. create figure
    fig = plt.figure()
    ax = fig.gca()
    
    # 5.2. plot bars
    ypos = np.arange(value_list_rel.shape[0])
    ax.barh(ypos, value_list_rel*100, color=color_list)
    
    # 5.3. plot value for each share
    for i in range(value_list_rel.shape[0]):
        # check, if text is to be plotted onto the bar or right to the bar
        val_rel = value_list_rel[i]
        val_abs = value_list_abs[i]
        
        frac = value_list_rel[i] / max_val_rel
        
        if(frac < 0.15):
            # bar is too small, plot text right to the bar, color is black
            text_color = (0, 0, 0, 1)
            x = value_list_rel[i]*100 + dx_text
        else:
            # bar is big enough, plot text onto the bar, select color
            # based on the color of the bar
            x = dx_text
            text_color = get_text_color(color_list[i])

        # plot text
        s = "{:.2f} % ({})".format(
            val_rel*100, format_capital(val_abs, currency))
        ax.text(x, i, s, color=text_color, ha='left', va='center')
    
    # 5.3. plot share names
    ax.set_yticks(ypos)
    ax.set_yticklabels(label_list)
    
    # 5.4. decorate axis
    ax.set_xlabel("Relative amount (%)")

    ylim = [-0.75, value_list_rel.shape[0] - 1 + 0.75]
    ax.set_ylim(ylim)
    
    # 5.5. set size of figure
    figwidth = FIGWIDTH
    axheight = (ylim[1] - ylim[0]) / 3
    
    set_size(fig, figwidth=figwidth, axheight=axheight, pad=1.08)
    
    # 5.6. save figure
    
    f_name_out = "share_rel_amount_{}.{}"
    f_path_out = os.path.join(dir_path_out_images, f_name_out)
    
    file_tag = displayname.replace(" ", "_").lower()
    
    fig.savefig(f_path_out.format(file_tag, "png"), dpi=DPI)
    fig.savefig(f_path_out.format(file_tag, "pdf"), dpi=DPI)
    
    if(SHOW_PLOTS_IN_CONSOLE):
        plt.show()
    else:
        plt.close()
        
    # 6. return result for html file
    res = {}
    
    res['displayname'] = displayname
    res['f_name_png'] = f_name_out.format(file_tag, "png")
    res['f_name_pdf'] = f_name_out.format(file_tag, "pdf")
    
    return res

def create_chart_share_gain_abs_rel_single(config):
    """
    Calculates the absolute and relative gain of each share.
    """
    
    share_data_dict = config['share_data_dict']
    list_trades = config['list_trades']
    share_amount_dates = config['share_amount_dates']
    share_depot_values = config['share_depot_values']
    split_list = config['split_list']
    currency = config['currency']
    dir_path_out_images = config['dir_path_out_images']
    
    # 0. initialize variables
    
    # all shares
    list_shares = sorted(share_data_dict.keys())

    label_list = []  # displaynames
    value_list_abs = []  # list of respective absolute gains
    value_list_rel = []  # list of respective relative gains
    color_list = []  # list of colors

    # 1. iterate over each share
    for key in list_shares:
        # 1.1 collect all trades for thies share
        list_trades_share = []
        
        # 1.1.1 iterate over each trade
        for trade in list_trades:
            if(trade[0] > share_amount_dates[-1]):
                # trade is in the future
                continue
        
            key_trade, fac = get_id_fac_from_split_for_value(split_list, trade[1])
        
            if(key_trade != key):
                # key does not match
                continue
        
            if(trade[2] == 0.0): 
                # itgnore dividends
                continue
            
            if(trade[3] > 0.0):
                # if buying of shares:
                # save amount of shares and average share price
                list_trades_share.append([fac*trade[2], trade[3]/(fac*trade[2])])
            else:
                # shares sold
                # adjust previous trades according to the FIFO principle:
                # first bought shares will also be sold first
                
                # iteratively reduce sold amount until it is zero
                # (the FIFO principle can be effect multiple trades)
                amount_sold = -fac*trade[2]
                
                for t in list_trades_share:
                    if(amount_sold <= 0): 
                        # amount_sold successfully reduced to 0
                        break
                    
                    if(t[0] >= amount_sold): 
                        # FIFO can be applied completely to this trade, 
                        # abort loop
                        t[0] = t[0] - amount_sold
                        break
                    else:
                        # FIFO cannot be completely applied to this trade
                        # reduce amount_sold, set amount of this trade to 0
                        amount_sold = amount_sold - t[0]
                        t[0] = 0.0
                        
        # 1.2. calculate the total amount of shares and the resulting
        # buying price of the remaining shares (according to the FIFO
        # principle)
        amount_share = 0.0
        buy_price_share = 0.0
        for t in list_trades_share:
            amount_share += t[0]
            buy_price_share += t[0]*t[1]  # buy price = amout * average_price
            
        # 1.3. calculate realtive and absolute gain
        if(amount_share > 0.0):
            value = share_depot_values[key][-1]
            
            label_list.append(share_data_dict[key]['displayname'])
            color_list.append(share_data_dict[key]['color'])
            
            # for relative gain: consider only shares, where buy_price is
            # positive
            # e.g., when spin-offs are created and existing shareholders
            # get shares of the new company, the buy_price of this share is
            # zero.
            if(buy_price_share > 0):
                value_list_rel.append((value - buy_price_share) / buy_price_share)
            else:
                value_list_rel.append(1.0)
                
            # absolute gain can always be calculated
            value_list_abs.append((value - buy_price_share))
            
    # 2. convert lists to arrays
    value_list_abs = np.asarray(value_list_abs)
    value_list_rel = np.asarray(value_list_rel)
    label_list = np.asarray(label_list)
    color_list = np.asarray(color_list)
    
    #-------------------------------------------------------------------------#
    # 3. plot relative gains
    
    # 3.1. sort lists with respect to the relative gains
    val_args = value_list_rel.argsort().astype(int)
    
    # important: sort also value_list_abs, since the other variables
    # (label_list, color_list) will be overwritten with the new order
    value_list_abs = value_list_abs[val_args]
    value_list_rel = value_list_rel[val_args]
    label_list = label_list[val_args]
    color_list = color_list[val_args]
    
    # 3.2. get spacing of text with respect to the difference between
    # maximum and minimum
    max_val_rel = np.max(value_list_rel)
    min_val_rel = np.min(value_list_rel)
    
    dx_text = 0.005*(max_val_rel - min_val_rel) * 100
    
    # 3.3. create figure
    fig = plt.figure()
    ax = fig.gca()
    
    # 3.4. plot bars
    ypos = np.arange(len(value_list_rel))
    ax.barh(ypos, value_list_rel*100, color=color_list)
    
    # 3.5 plot realtive gains as text
    for i in range(value_list_rel.shape[0]):
        val_rel = value_list_rel[i]
        frac = val_rel / max_val_rel
        
        if(frac < 0):
            # share has negative gain (= loss), plot value right to the
            # y=0 axis
            text_color = (0, 0, 0, 1)
            x = dx_text
        elif(frac < 0.125):
            # share has low gain, plot value right to the bar
            text_color = (0, 0, 0, 1)
            x = value_list_rel[i]*100 + dx_text
        else:
            # plot value on the bar
            x = dx_text
            text_color = get_text_color(color_list[i])
        
        ax.text(x, i, "{:+.2f} %".format(value_list_rel[i]*100), 
                color=text_color, ha='left', va='center')
    
    # 3.6. plot share names
    ax.set_yticks(ypos)
    ax.set_yticklabels(label_list)
    
    # 3.7. decorate axis
    ax.set_xlabel("Relative Gain (%)")
    
    ylim = [-0.75, value_list_rel.shape[0] - 1 + 0.75]
    ax.set_ylim(ylim)
    
    # 3.8. set figure size    
    figwidth = FIGWIDTH
    axheight= (ylim[1] - ylim[0]) / 3
    
    set_size(fig, figwidth=figwidth, axheight=axheight, pad=1.08)

    # 3.9. save figure
    f_path_out = os.path.join(dir_path_out_images, "rel_gain_{}.{}")
    
    fig.savefig(f_path_out.format("all", "png"), dpi=DPI)
    fig.savefig(f_path_out.format("all", "pdf"), dpi=DPI)
    
    if(SHOW_PLOTS_IN_CONSOLE):
        plt.show()
    else:
        plt.close()
    
    #-------------------------------------------------------------------------#
    # 4. plot absolute gains
    
    # 4.1. sort arrays with respect to the absolute gain
    val_args = value_list_abs.argsort().astype(int)
    
    value_list_abs = value_list_abs[val_args]
    value_list_rel = value_list_rel[val_args]
    label_list = label_list[val_args]
    color_list = color_list[val_args]
    
    # 4.2. get spacing of text with respect to the difference between
    # maximum and minimum
    max_val_abs = np.max(value_list_abs)
    min_val_abs = np.min(value_list_abs)
    
    dx_text = 0.005 * (max_val_abs - min_val_abs)
    
    # 4.3. create figure
    fig = plt.figure()
    ax = fig.gca()
    
    # 4.4. plot bars
    ypos = np.arange(len(value_list_rel))
    ax.barh(ypos, value_list_abs, color=color_list)
    
    # 4.5 plot absolute gains as text
    for i in range(value_list_rel.shape[0]):
        val_abs = value_list_abs[i]
        frac = val_abs / max_val_abs
        
        if(frac < 0):
            # share has negative gain (= loss), plot value right to the
            # y=0 axis
            text_color = (0, 0, 0, 1)
            x = dx_text
        elif(frac < 0.125):
            # share has low gain, plot value right to the bar
            text_color = (0, 0, 0, 1)
            x = value_list_abs[i] + dx_text
        else:
            # plot value on the bar
            x = dx_text
            text_color = get_text_color(color_list[i])

        ax.text(
            x, i, format_capital(value_list_abs[i], currency),
            color=text_color, ha='left', va='center')
    
    # 4.6. plot share names
    ax.set_yticks(ypos)
    ax.set_yticklabels(label_list)
    
    # 3.7. decorate axis
    ax.set_xlabel("Absolute Gain ({})".format(currency))
    
    ylim = [-0.75, value_list_rel.shape[0] - 1 + 0.75]
    ax.set_ylim(ylim)
    
    # 4.8. set figure size    
    figwidth = FIGWIDTH
    axheight= (ylim[1] - ylim[0]) / 3
    
    set_size(fig, figwidth=figwidth, axheight=axheight, pad=1.08)

    # 4.9. save figure
    f_path_out = os.path.join(dir_path_out_images, "abs_gain_{}.{}")
    
    fig.savefig(f_path_out.format("all", "png"), dpi=DPI)
    fig.savefig(f_path_out.format("all", "pdf"), dpi=DPI)
    
    if(SHOW_PLOTS_IN_CONSOLE):
        plt.show()
    else:
        plt.close()


def evaluate_categories_total_and_reference(config):
    """
    Calculates the total value based on the predefined categories. In this
    plot, also some reference configurations will be ploted to compare
    the performance and make a prediction about the future result.
    """
    
    share_amount_dates = config['share_amount_dates']
    share_depot_values = config['share_depot_values']
    share_data_dict = config['share_data_dict']
    category_compare_list = config['category_compare_list']
    reference_config_list = config['reference_config_list']
    end_date = config['end_date']
    currency = config['currency']
    dir_path_out_images = config['dir_path_out_images']
    
    if(end_date is None):
        # evolution is calculated to the last day of the previous year
        # always plot evolution of this year and next year
        end_date = datetime(datetime.now().year + 2, 1, 1)
        
    # 0. If output to the console: print headers = category names
    if(SHOW_PLOTS_IN_CONSOLE):
        s_format = "{:>11} " + len(category_compare_list)*"{:>20} "
        s = s_format.format(
            "", *[ccl['displayname'] for ccl in category_compare_list])
        print(s)
    
    # format string for each line
    # first entry: date (last day of each month)
    # following entries: values
    s_format = "{}: " + len(category_compare_list)*"{:18.2f} € "
    
    # 1. define resulting arrays
    # for plots
    date_list = []
    amount_list = []
    
    # for table (will contain values at the last day of the month)
    date_list_month = []
    amount_list_month = []
    
    # 2. Process each day
    for i_date in range(len(share_amount_dates)):
        
        # list, that will contain the total values for the given
        # day for the different category selections
        total_value_list = []
        
        # 2.1. iterate over each category
        for ccl in category_compare_list:
            total_value = 0

            # 2.1.1. get categories
            category_list = ccl['category_list']
            
            # 2.1.2. get all shares which belong to the categories in the
            # current list
            key_list_valid = get_keys_from_category_list(
                share_data_dict, category_list)
            
            # 2.1.3. calculate total sum (only of valid keys)
            for key in key_list_valid:
                val = share_depot_values[key][i_date]
                
                if(val is not None and val > 1e-5):
                    total_value += share_depot_values[key][i_date]
                    
            # 2.1.4. save total value of the current category selection
            total_value_list.append(total_value)
            
        # 2.2. save date and the list of total values
        date_list.append(share_amount_dates[i_date])
        amount_list.append(total_value_list)
        
        # 2.3. if last day of month or last day in list: save value separately
        if(is_last_day_of_month(share_amount_dates[i_date]) 
           or i_date == len(share_amount_dates) - 1):
            if(SHOW_PLOTS_IN_CONSOLE):
                print(s_format.format(
                        share_amount_dates[i_date].strftime("%d.%m.%Y"), 
                        *amount_list[i_date]))
            
            date_list_month.append(share_amount_dates[i_date])
            amount_list_month.append(amount_list[i_date])
    
    # 3. convert amount list to array
    amount_list = np.asarray(amount_list)
        
    # 4. create figure
    fig = plt.figure()
    ax = fig.gca()
    
    xmin = np.inf
    xmax = -np.inf
    
    # 4.1. print evolution for each category selection
    for i_config, ccl in enumerate(category_compare_list):
        lbl = ccl['displayname']
        color = ccl['color']
        ax.plot(date_list, amount_list[:, i_config], label=lbl, c=color)
        
        xmin = min(xmin, date2num(date_list[0]))
        xmax = max(xmin, date2num(date_list[-1]))
        
    # 4.2. print evolution of reference configuration
    for i_config, reference_config in enumerate(reference_config_list):
        # calculate reference configuration
        args = reference_config['args']
        date_list, amount_list = get_reference_evolution(
            **args, end_date=end_date)
        
        # collect data for label
        start_capital = args['start_capital']
        monthly_payment = args['monthly_payment']
        yearly_rise = args['interest']
        
        lbl = "Start: {}, Monthly payment: {}, Interest: {:.2f} %".format(
            format_capital(start_capital, currency), 
            format_capital(monthly_payment,  currency), (yearly_rise-1)*100)
        c = np.asarray(reference_config['color'])
        
        ax.plot(date_list, amount_list, label=lbl, c=c)
    
        xmin = min(xmin, date2num(date_list[0]))
        xmax = max(xmin, date2num(date_list[-1]))
        
    # 4.3. layout figure
    ax.grid()
    ax.legend()
    
    ax.set_xlabel("Date")
    ax.set_ylabel("Value ({})".format(currency))
    ax.set_xlim([xmin, xmax])
    
    fig.set_figwidth(FIGWIDTH)
    fig.set_figheight(FIGHEIGHT)
    fig.tight_layout(pad=1.08)
    
    # 4.4. save figure
    f_path_out = os.path.join(dir_path_out_images, "capital_estimator.{}")
    
    fig.savefig(f_path_out.format("png"), dpi=DPI)
    fig.savefig(f_path_out.format("pdf"), dpi=DPI)
    
    if(SHOW_PLOTS_IN_CONSOLE):
        plt.show()
    else:
        plt.close()
    
    # 4.5. return the values at the end of each month
    res = {}
    res['date_list_month'] = date_list_month
    res['amount_list_month'] = amount_list_month
    
    return res

def is_last_day_of_month(date):
    """
    Checks if a given day is the last day of the month
    """
    
    # 1. get range for the given month
    m_range = calendar.monthrange(date.year, date.month)
    
    # compare day with the range
    if(date.day == m_range[1]):
        return True
    else:
        return False

def calculate_personal_index(config):
    """
    Calculates a personal performance index for better comparison to other
    indices. 
    
    The total value is not a measure of performance, because it can
    increase or decrease due to trades. Hence, a personal index will be 
    calculated, where gains from trades are considered, but not the
    resulting rise or fall of the value.
    
    
    To calculate the personal index, the following approach is used:
        
        - The first day, where a trade occured, will be assigned 1000 Points
        - For each following day, the realtive change of the value is calulated
          in the follwoing way:

            - the start value of the day is the total value of the previous
              day plus the expenses for new trades
            - the end value of the day is the total value
              
    With this approach the real performance is measured. The order charges
    will also be accounted for, since they are included in the total expense
    of each trade, but the total value at the end of the day is calculated
    with the amount of shared multiplied by the close value.
    
    """
    
    share_data_dict = config['share_data_dict']
    share_amount_dates = config['share_amount_dates']
    share_depot_values = config['share_depot_values']
    list_trades = config['list_trades']
    category_list = config['category_list']
    
    # 0. initialize variables
    performance_start = 1000  # arbitrary value
    
    date_list = []  # list of dates at which the personal index is calculated
    performance_list = []  # personal index value
    total_value_list = []  # total value
    
    current_performance = performance_start  # variable for the personal index
    
    # 1. get valid shares
    key_list_valid = get_keys_from_category_list(
        share_data_dict, category_list)
    
    # 2. calculate personal index for each date
    for i_date in range(len(share_amount_dates)):
        # 2.1. calculate total value at the end of the day
        total_value = 0.0
        
        for key in key_list_valid:
            if(share_depot_values[key][i_date] is not None):
                total_value += share_depot_values[key][i_date]
        
        if(total_value < 0.1):
            continue

        # 2.2. save date
        current_date = share_amount_dates[i_date]
        date_list.append(current_date)
        total_value_list.append(total_value)
        
        # 2.3. if first day to calculate or total value is zero, then
        # save the current value
        if(len(performance_list) == 0 or total_value < 0.1):
            performance_list.append(current_performance)
            continue
        
        # 2.4. calculate performance of day
        total_value_previous_day = total_value_list[-2]
        total_value_day_end_tmp = total_value_list[-1]
        
        # collect all trades
        list_trades_buy = [
            ld for ld in list_trades 
            if ld[0] == current_date and ld[1] in key_list_valid and ld[3] > 0]
        list_trades_sell = [
            ld for ld in list_trades 
            if ld[0] == current_date and ld[1] in key_list_valid and ld[3] < 0]
        
        # collect the total sum for buys and sells
        sum_buy = 0
        sum_sell = 0
        for ld in list_trades_buy:
            sum_buy += ld[3]
        for ld in list_trades_sell:
            sum_sell += ld[3]
            
        # add buys to the total value at the start of the day
        total_value_day_start = total_value_previous_day + sum_buy
        # add sells to the total value at the end of the day
        # attention: sells are entered with the negative
        # amount, therefore it needs to be subtracted!
        total_value_day_end = total_value_day_end_tmp - sum_sell
        
        # 2.5. save performance
        if(total_value_day_start < 0.1 and False):
            # avoid division by zero
            performance_list.append(current_performance)
        else:
            # calculate relative gain/loss
            fac = (total_value_day_end / total_value_day_start)
            current_performance = fac * current_performance
            performance_list.append(current_performance)
    
    # 3. create resulting dictionary
    res = {}
    res['date_list'] = date_list
    res['close_values_list'] = performance_list

    # ensures, that the dictionary has the same structure as the
    # dictionaries obtaines by reading the chart data
    res['open_values_list'] = None  
    
    
    return res
       
def create_chart_personal_index(config):
    """
    Evaluates the personal index.
    """
    
    share_data_dict = config['share_data_dict']
    share_amount_dates = config['share_amount_dates']
    share_depot_values = config['share_depot_values']
    list_trades = config['list_trades']
    chart_data = config['chart_data']
    category_compare_list = config['category_compare_list']
    dir_path_out_images = config['dir_path_out_images']
    
    # 0. initialize variables
    # will contain the evolution of personal index and indices to compare
    index_chart_data_compare = {}
    
    # name and color are stored in a different dictionary
    style_dict = {}
    
    # 1. read personal index data
    for i_ccl, ccl in enumerate(category_compare_list):
        # create unique key
        key = "my_index_{}".format(i_ccl)
        
        category_list = ccl['category_list']
        lbl = ccl['displayname']
        color = ccl['color']

        # calculate personal index
        category_list = ccl['category_list']
        config_tmp = {}
        config_tmp['share_data_dict'] = share_data_dict
        config_tmp['share_amount_dates'] = share_amount_dates
        config_tmp['share_depot_values'] = share_depot_values
        config_tmp['list_trades'] = list_trades
        config_tmp['category_list'] = category_list

        index_chart_data_compare[key] = calculate_personal_index(
            config_tmp)
        
        style_dict[key] = {}
        style_dict[key]['displayname'] = lbl
        style_dict[key]['color'] = color
    
    # 2. get data of reference indices
    for key in chart_data.keys():
        
        # read only shares with category x
        if(not "X" in share_data_dict[key]['category']):
            continue
        
        # save data
        index_chart_data_compare[key] = chart_data[key]
    
        style_dict[key] = {}
        style_dict[key]['displayname'] = share_data_dict[key]['displayname']
        style_dict[key]['color'] = share_data_dict[key]['color']
        
    
    # 3. evaluate performance
    today = datetime.now()
    
    #-------------------------------------------------------------------------#
    # evaluation by month / year delta
    # TODO: magic number / variable
    
    timespan_config_list = []
    timespan_config_list.append([monthdelta(today, -1), today, "1 Month"])
    timespan_config_list.append([monthdelta(today, -6), today, "6 Months"])
    timespan_config_list.append([yeardelta(today, -1),  today, "1 Year"])
    timespan_config_list.append([yeardelta(today, -3),  today, "3 Years"])
    timespan_config_list.append([yeardelta(today, -5),  today, "5 Years"])
    
    base_filename = "index_comparison_bar_timespan.{}"
    
    config_tmp = {}
    config_tmp['index_chart_data_compare'] = index_chart_data_compare
    config_tmp['style_dict'] = style_dict
    config_tmp['timespan_config_list'] = timespan_config_list
    config_tmp['base_filename'] = base_filename
    config_tmp['dir_path_out_images'] = dir_path_out_images
    
    create_index_comparison_bar_chart(config_tmp)
    

    #-------------------------------------------------------------------------#
    # evaluation by years
    num_years = 5
    timespan_config_list = []
    
    # get start and end dates for the last 5 years
    for i_year in range(num_years):
        year = today.year - i_year
        lbl = "{:d}".format(year)
        
        if(i_year == 0):
            # current year is not finished yet
            timespan_config_list.append(
                [datetime(year,  1,  1), today, lbl])
        else:
            timespan_config_list.append(
                [datetime(year,  1,  1), datetime(year, 12,  31), lbl])

    base_filename = "index_comparison_bar_year.{}"
    config_tmp['timespan_config_list'] = timespan_config_list
    config_tmp['base_filename'] = base_filename
    
    create_index_comparison_bar_chart(config_tmp)

def create_index_comparison_bar_chart(config):    
    """
    Shows the performance of the personal index and the reference
    indices in bars.
    """
    
    index_chart_data_compare = config['index_chart_data_compare']
    style_dict = config['style_dict']
    timespan_config_list = config['timespan_config_list']
    base_filename = config['base_filename']
    dir_path_out_images = config['dir_path_out_images']
    
    # 1. rearange data, so that it will be easier to plot
    performance_dict = {}
    
    # calculate the relative change of the indices for the selected
    # timespans
    
    # 1.1 iterate over each index
    for key in index_chart_data_compare.keys():
        res = []
        
        date_list_raw = index_chart_data_compare[key]['date_list']
        close_values_list_raw = index_chart_data_compare[key]['close_values_list']
        
        # skip, if no data is available
        if(len(date_list_raw) == 0):
            continue
        
        # 1.1. iterate over each time span
        for timespan_config in timespan_config_list:
            
            # 1.1.1 get start and end date
            date_start = timespan_config[0]
            date_end = timespan_config[1]
            
            # 1.1.2. get values at the start and end date
            val_start = None
            val_end = None
            
            for i_date, date in enumerate(date_list_raw):
                close_val = close_values_list_raw[i_date]
                
                # do not save close value if it is None 
                # (e. g. no data available)
                if(close_val is None):
                    continue
                
                # save value if it is None or date <= date_start
                # the first check ensured, that val_start will be set
                # order of checks is important
                # check first if date <= date_start
                # if this is not true, save value only when no value was assigned yet
                if(date <= date_start or val_start is None):
                    val_start = close_val
                
                if(date <= date_end or val_end is None):
                    val_end = close_val
                  
            
            # 1.1.3. check for errors, this should not happen
            if(val_start is None):
                print(date, timespan_config, key, date_list_raw)
                raise ValueError("Start value not found!")
            
            if(val_end is None):
                raise ValueError("End value not found!")
              
            if(val_start < 0.1):
                raise ValueError(f"Invalid value for val_start: {val_start}")

            # 1.1.4. calculate performance between the selected time spans
            performance = (val_end - val_start) / val_start
            
            # 1.1.5. save performance
            res.append(performance)
            
        # 1.2. save results
        performance_dict[key] = np.asarray(res)
        
    # 2. plot data
    
    # 2.1. create figure
    fig = plt.figure()
    ax = fig.gca()
    
    # 2.2. get configuration
    x = np.arange(len(timespan_config_list))  # base x-positions
    width = 0.80
    num_keys = len(performance_dict.keys())
    
    # 2.3. print bar for each key
    for i_key, key in enumerate(performance_dict.keys()):
        # adjust x position
        x_tmp = x + width/num_keys*i_key
        
        # shift reference indices a little bit more to the right
        if(not key.startswith("my_index")):
            x_tmp += 0.025
        
        # plot bars
        ax.bar(x_tmp, 
               performance_dict[key]*100, width/num_keys, 
               label=style_dict[key]['displayname'], color=style_dict[key]['color'])
        
        # plot relative change as text (for each bar separate)
        for i_x in range(x_tmp.shape[0]):
            x0 = x_tmp[i_x]
            y0 = performance_dict[key][i_x]*100
            if(y0 < 0):
                # if loss, then print it on top of the x-axis
                y0 = 0
            val = performance_dict[key][i_x]*100
            
            # green for gain, red for loss
            if(val > 0):
                c = 'darkgreen'
            else:
                c = 'darkred'
            
            # plot text
            ax.text(x0, y0 + 2.5, 
                    "{:+.2f} %".format(val), color=c, 
                    ha='center', va='bottom',
                    rotation=90)
            
    # 2.4. decorate axis
    ref_date_labels = [
        timespan_config[2] for timespan_config in timespan_config_list]
    ax.set_xticks(x + width/2)
    ax.set_xticklabels(ref_date_labels)
    
    # create extra space on top to ensure, that text is visible on the axis
    ax.set_ylim(ax.get_ylim()[0], ax.get_ylim()[1] + 25)
    
    ax.set_ylabel("Relative Performance")
    
    ax.legend()
    ax.grid(axis='y')
    
    # 2.5. resize figure and save it
    fig.set_figwidth(FIGWIDTH)
    fig.set_figheight(FIGHEIGHT)
    fig.tight_layout()
    
    f_path_out = os.path.join(dir_path_out_images, base_filename)
    
    fig.savefig(f_path_out.format("png"), dpi=300)
    fig.savefig(f_path_out.format("pdf"), dpi=300)
    
    if(SHOW_PLOTS_IN_CONSOLE):
        plt.show()
    else:
        plt.close()

def get_value_reference_evolution(config):
    """
    Calculates the evolution of the reference configuration. Cannot be done
    in :func:``evaluate_categories_total_and_reference``, since the data
    is for the table and has therefore a different end date.
    """
    
    reference_config_list = config['reference_config_list']
    end_date = config['end_date']
    
    # 1. define result variable
    res_list = []
    
    # 2. get evolution of each reference configuration
    for reference_config in reference_config_list:
        args = reference_config['args']
        
        # calculate evolution
        date_list, money_list = get_reference_evolution(
            **args, end_date=end_date)
        
        # save result
        res_list.append([date_list, money_list])

    # 3. return result
    return res_list


   
def get_chart_data(share_data_dict):
    """
    Reads the chart data of each share.
    """
    
    # 1. create resulting dictionary
    chart_data = {}
    
    # 2. iterate over each key (= wnk = identifier)
    for key in share_data_dict.keys():
        
        # 2.1. get path to the chart data file
        f_path_in = get_f_path_chart_data(key)
        
        # 2.2. read file
        with open(f_path_in, 'r') as f:
            lines = f.readlines()
            
        # 2.3. get dates, open, and close values
        date_list = []
        open_values_list = []
        close_values_list = []
        
        for line in lines[1:]:
            line_parts = line.split(';')
            
            try:
                try:
                    f_open_value = float(line_parts[1])
                except Exception:
                    f_open_value = None
                
                f_close_value = float(line_parts[4])

                date_parts = line_parts[0].split('.')
                year = int(date_parts[2])
                month = int(date_parts[1])
                day = int(date_parts[0])
                
                date_value = datetime(year, month, day)
                date_list.append(date_value)
                open_values_list.append(f_open_value)
                close_values_list.append(f_close_value)
            except:
                # possibly empty line
                pass
        
        # 2.4. save data for the given key
        chart_data[key] = {'date_list' : date_list, 
                           'open_values_list' : open_values_list, 
                           'close_values_list' : close_values_list}

    return chart_data

def get_reference_evolution(
        start_capital, monthly_payment, interest, start_date, end_date):
    """
    Calculates a hypthetical reference evolution of the capital.
    
    Here, a simple model is applied. At the given date ``start_date``, it 
    is assumed, that the capital is ``start_capital``. Then, each month,
    a payment of ``monthly_payment`` is made. The capital at the start
    of the year is assumed to rise with ``interest``. A typical value would
    be a rise of 7%, in this case ``interest=1.07``. This calculation will
    be performed until the last full year before the given date ``end_date``.
    
    Obviously, this is a very simple model and it could be done more detailed.
    But the main goal of this calculation is to show the potential of
    investing. For this, this simple model is sufficient.
    """
    
    # 0. initialize variables
    today = start_date
    
    date_list = [start_date]  # list of dates
    money_list = [start_capital]  # list of capital at the respective date
    
    # 1. calculate number of months remaining in the start year
    # for the first year, no interest is assumed
    months_this_year = 12 - today.month
    start_capital = start_capital + months_this_year*monthly_payment
    
    date_list.append(datetime(today.year, 12, 31))
    money_list.append(start_capital)
    
    # 2. iterate over each year and calculate the capital at the end of the
    # year
    capital = start_capital
    
    for i_year, year in enumerate(range(today.year + 1, end_date.year)):
        capital = capital*interest + 12*monthly_payment
        
        date_list.append(datetime(year, 12, 31))
        money_list.append(capital)
        
    # 3. return results
    return date_list, money_list

def calculate_best_worst_days(config):
    """
    Calculates the best and the worst dates of the selected categories.
    """
    
    share_data_dict = config['share_data_dict']
    share_amount_dates = config['share_amount_dates']
    share_depot_values = config['share_depot_values']
    list_trades = config['list_trades']
    category_compare_list = config['category_compare_list']
    
    # 0. initialize variables
    res_list = []
    
    # 1. iterate over each category selection
    for cll in category_compare_list:
        
        # 1.1. calculate personal index
        config_tmp = {}
        config_tmp['share_data_dict'] = share_data_dict
        config_tmp['share_amount_dates'] = share_amount_dates
        config_tmp['share_depot_values'] = share_depot_values
        config_tmp['list_trades'] = list_trades
        config_tmp['category_list'] = cll['category_list']

        res = calculate_personal_index(
            config_tmp)
        
        # 1.2. calculate relative change for each day 
        # (skip the first day for this)
        date_list = res['date_list']
        performance_list = np.asarray(res['close_values_list'])
        
        rel_change = ((performance_list[1:] - performance_list[:-1]) 
                      / performance_list[:-1])
        
        # 1.3. save results into one list
        xy_list = zip(date_list[1:], rel_change)
        
        # 1.4. sort this list by the relative performance
        xy_list = sorted(xy_list, key=lambda x: -x[1])
        
        # 1.5. save results
        res = {}
        res['configuration'] = cll
        res['date_performance_list'] = xy_list
        
        res_list.append(res)
        
    # 2. return results
    return res_list

def get_text_color(background_color, with_alpha=True):
    """
    Function to get the text color to use based on the background color, on
    which  the text should be drawn. Calculate the luminance of the R, G and B
    value of the color and decides then, which color to use. Possible return
    colors are black or white.
    
    Source: https://stackoverflow.com/questions/1855884/determine-font-color-based-on-background-color
    
    Parameters
    ----------
        background_color : Color
            Color of the background, on which the text shall be drawn. Must be
            a list or tuple of the format (R, G, B) or (R, G, B, A). Any
            Color gained from the matplotlib library can be provided. The
            values for R, G, and B must be floats between 0 and 1.
            
    Returns
    -------
        text_color : Color
            Text color, which looks best on the provided background color.
            Either black or white, depending on the luminance of the 
            background color.
    """
    if(isinstance(background_color, str)):
        background_color = colors.to_rgba(background_color)
    
    r = background_color[0]
    g = background_color[1]
    b = background_color[2]

    luminance = (0.299*r + 0.587*g + 0.144*b)
    
    if(luminance > 0.5):
        d = 0
    else:
        d = 1
        
    if(with_alpha):
        return (d, d, d, 1.0)
    else:
        return (d, d, d)

def set_size(fig, figwidth=None, axwidth=None, figheight=None, axheight=None, 
             num_iterations=10, pad=1.08, debug=False):
    """
    Function to set the size of a figure, where the desired size of the axis
    provided. For this, the desired width and height of the axis must be
    provided. If the figure has more than one axis, then the first added axis
    will be taken.
    
    
    .. note:: This function already applies the :func:`tight_layout()`-function
              on the axis. It is not necessary to apply it afterwards since
              it can break the sizes of the axis.
    
    Parameters
    ---------
        fig : Figure
            The figure which will be adjusted.
            
        w : float
            Desired width of the (first added) axis (in inches).
            
        h : float
            Desired height of the (first added) axis (in inches).
            
        num_iterations : int, optional
            Number of iterations that will be performed. Default is 10.
            Increase, if the resulting size of the axis does not match the
            desired size. For most cases, 10 should be enough.
            
        pad : float
            ``pad``-Parameter of the :func:`tight_layout`-function. Default is
            1.08.
    """
    
    list_test = [figwidth, axwidth]
    if(list_test.count(None) != len(list_test) - 1):
        raise ValueError("You must either set 'figwidth' or 'axwidth'.")
    
    list_test = [figheight, axheight]
    if(list_test.count(None) != len(list_test) - 1):
        raise ValueError("You must either set 'figheight' or 'axheight'.")
    
    
    for i in range(num_iterations):
        w_old = fig.get_figwidth()
        h_old = fig.get_figheight()
     
        #ax = fig.gca()
        ax = fig.get_axes()[0]
        bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        
        margin_w = w_old - bbox.width
        margin_h = h_old - bbox.height
        
        if(figwidth is not None):
            figw = figwidth
        else:
            figw = axwidth + margin_w
        
        if(figheight is not None):
            figh = figheight
        else:
            figh = axheight + margin_h
    
        fig.set_figwidth(figw)
        fig.set_figheight(figh)
        
        if(debug): print(figw, figh)
        
        fig.tight_layout(pad=pad)
        
        if(debug): 
            fig.savefig("E:\\PythonScripts_output\\test_{}.png".format(i), dpi=300)

def monthdelta(date, delta):
    """
    Source: https://riptutorial.com/python/example/8657/subtracting-months-from-a-date-accurately
    """
    m, y = (date.month+delta) % 12, date.year + ((date.month)+delta-1) // 12
    if not m:
        m = 12
    d = min(date.day, calendar.monthrange(y, m)[1])
    return date.replace(day=d,month=m, year=y)        

def yeardelta(date, delta):
    m = date.month
    y = date.year + delta
    
    d = min(date.day, calendar.monthrange(y, m)[1])
    
    return date.replace(day=d, month=m, year=y)

def update_html(config):
    """
    Updates the html file with the current results.
    """
    
    f_path_template = config['f_path_template']
    f_path_html= config['f_path_html']
    dir_name_images = config['dir_name_images']
    
    ###########################################################################
    # 1. read template
    with open(f_path_template, 'r') as f:
        s = f.read()
        
    root_template = BeautifulSoup(s, 'html.parser')
    
    ###########################################################################
    # 2. update the field "last updated" and the 'static' images
    node_div_last_updated = root_template.find(
        "div", attrs = {"id": "div_last_updated_473721"})
    node_div_last_updated.string = (
        "Last Updated: {}".format(datetime.now().strftime("%d.%m.%Y")))
    
    # image for share evolution
    node_div = root_template.find(
        "div", attrs={"id": "div_share_evolution_5876940"})
    
    caption = "Performance of shares."
    f_name_png = "share_evolution_all.png"
    f_name_pdf = "share_evolution_all.pdf"
    
    insert_figure(root_template, node_div, dir_name_images, f_name_png, 
                  f_name_pdf, caption)
    
    # image for the reference evolution
    node_div = root_template.find(
        "div", attrs={"id": "div_reference_evolution_3422174823"})
    
    caption = "Comparison of performance to different scenarios."
    f_name_png = "capital_estimator.png"
    f_name_pdf = "capital_estimator.pdf"
    
    insert_figure(root_template, node_div, dir_name_images, f_name_png, 
                  f_name_pdf, caption)
    
    # image for relative gain
    node_div = root_template.find(
        "div", attrs={"id": "div_relative_gain_67930"})
    
    caption = "Relative gain of each share."
    f_name_png = "rel_gain_all.png"
    f_name_pdf = "rel_gain_all.pdf"
    
    insert_figure(root_template, node_div, dir_name_images, f_name_png, 
                  f_name_pdf, caption)

    # image for relative gain
    node_div = root_template.find(
        "div", attrs={"id": "div_absolute_gain_74291"})
    
    caption = "Absolute gain of each share."
    f_name_png = "abs_gain_all.png"
    f_name_pdf = "abs_gain_all.pdf"
    
    insert_figure(root_template, node_div, dir_name_images, f_name_png, 
                  f_name_pdf, caption)
    
    # personal index - timespan
    node_div = root_template.find(
        "div", attrs={"id": "div_personal_index_timespan_7214584"})
    
    caption = "Comparison of personal index for different time spans to other indices."
    f_name_png = "index_comparison_bar_timespan.png"
    f_name_pdf = "index_comparison_bar_timespan.pdf"
    
    insert_figure(root_template, node_div, dir_name_images, f_name_png, 
                  f_name_pdf, caption)

    # personal index - year
    node_div = root_template.find(
        "div", attrs={"id": "div_personal_index_year_12457953"})
    
    caption = "Comparison of personal index for different years to other indices."
    f_name_png = "index_comparison_bar_year.png"
    f_name_pdf = "index_comparison_bar_year.pdf"
    
    insert_figure(root_template, node_div, dir_name_images, f_name_png, 
                  f_name_pdf, caption)

    ###########################################################################
    # 3. update the section 'Capital Estimator'
    date_list_month = config['date_list_month']
    amount_list_month = config['amount_list_month']
    category_list_names = config['category_list_names']
    
    num_rows = len(amount_list_month)
    num_configs = len(category_list_names)

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # 3.1. monthly results
    node_div_table = root_template.find(
        "div", attrs = {"id": "table_monthly_results_573892"})
    
    # 3.1.1. create new table
    table = root_template.new_tag(
        'table', attrs={'class': 'table table-striped table-auto-width'})
    node_div_table.append(table)
    
    # 3.1.2. create table head
    thead = root_template.new_tag('thead')
    table.append(thead)
    
    # create row for headings
    tr = root_template.new_tag('tr')
    thead.append(tr)
    
    # cell for the date
    td = root_template.new_tag('td', attrs={'scope': 'col'})
    td.string = "Date"
    tr.append(td)
    
    # filll the other cells with the caption of the categories
    for i in range(num_configs):
        td = root_template.new_tag(
            'td', attrs={'class': 'text-right', 'scope': 'col'})
        td.string = category_list_names[i]
        tr.append(td)
    
    # 3.1.3. create table body
    tbody = root_template.new_tag('tbody')
    table.append(tbody)
    
    # fill every row
    for i_row in range(num_rows):
        # create a new row
        tr = root_template.new_tag('tr')
        tbody.append(tr)

        for i_col in range(1 + num_configs):
            # first column contains the date
            if(i_col == 0):
                s = date_list_month[i_row].strftime("%d.%m.%Y")
            else:
                # second column contains the capital
                s = format_capital(amount_list_month[i_row][i_col - 1])
                
            td = root_template.new_tag('td', attrs={'class': 'text-right'})
            td.string = s
            tr.append(td)
    
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # 3.2. update evolution of the reference configurations
    reference_evolution_res_list = config['reference_evolution_res_list']
    reference_config_list = config['reference_config_list']
    
    node_div_table = root_template.find(
        "div", attrs = {"id": "table_reference_configs_final_results_683432"})
    
    # 3.2.1. create new table
    table = root_template.new_tag(
        'table', attrs={'class': 'table table-striped table-auto-width'})
    node_div_table.append(table)
    
    # 3.2.2. create new table head
    thead = root_template.new_tag('thead')
    table.append(thead)
    
    # create row
    tr = root_template.new_tag('tr')
    thead.append(tr)
    
    # create columns
    td = root_template.new_tag('td', attrs={'scope': 'col'})
    td.string = ""
    tr.append(td)
    
    for i in range(len(reference_config_list)):
        td = root_template.new_tag('td', attrs={'scope': 'col'})
        td.string = "Configuration {}".format(i + 1)
        tr.append(td)
    
    # 3.2.3. create table body
    tbody = root_template.new_tag('tbody')
    table.append(tbody)
    
    # 3.2.3.1. print start capital
    tr = root_template.new_tag('tr')
    tbody.append(tr)
    
    td = root_template.new_tag('td', attrs={'scope': 'col'})
    td.string = "Start Capital"
    tr.append(td)
    
    for i in range(len(reference_config_list)):
        reference_config = reference_config_list[i]
        args = reference_config['args']
        
        start_capital = args['start_capital']

        td = root_template.new_tag('td', attrs={'class': 'text-right'})
        td.string = format_capital(start_capital)
        tr.append(td)
    
    # 3.2.3.2. print monthly payment
    tr = root_template.new_tag('tr')
    tbody.append(tr)

    td = root_template.new_tag('td', attrs={'scope': 'col'})
    td.string = "Monthly Payment"
    tr.append(td)
    
    for i in range(len(reference_config_list)):
        reference_config = reference_config_list[i]
        args = reference_config['args']
        
        monthly_payment = args['monthly_payment']

        td = root_template.new_tag('td', attrs={'class': 'text-right'})
        td.string = format_capital(monthly_payment)
        tr.append(td)
    
    # 3.2.3.3. print interest rate
    tr = root_template.new_tag('tr')
    tbody.append(tr)

    td = root_template.new_tag('td', attrs={'scope': 'col'})
    td.string = "Interest"
    tr.append(td)
    
    for i in range(len(reference_config_list)):
        reference_config = reference_config_list[i]
        args = reference_config['args']
        
        yearly_rise = args['interest']

        td = root_template.new_tag('td', attrs={'class': 'text-right'})
        td.string = "{:.2f} %".format((yearly_rise - 1)*100)
        tr.append(td)
    
    # 3.2.3.4. print evolution of the reference configurations
    # date list is the same for all configurations
    date_list = reference_evolution_res_list[0][0]
    
    # iterate over each date = row
    for i_date in range(len(date_list)):
        # create row
        tr = root_template.new_tag('tr')
        tbody.append(tr)
        
        # first col shows the date
        td = root_template.new_tag('td', attrs={'scope': 'col'})
        td.string = date_list[i_date].strftime("%d.%m.%Y")
        tr.append(td)
        
        # the following columns show the capital for the reference evolution
        for i_config in range(len(reference_config_list)):
            s = format_capital(
                reference_evolution_res_list[i_config][1][i_date])
    
            td = root_template.new_tag('td', attrs={'class': 'text-right'})
            td.string = s
            tr.append(td)
    
            
    ###########################################################################
    # 4. update section distribution of shares
    node_div_distr = root_template.find(
        "div", attrs={"id": "id_distr_share_6740395"})
    
    res_list_share_rel_amount = config['res_list_share_rel_amount']
    
    # 4.1. iterate over each selection
    for res in res_list_share_rel_amount:
        # collect data
        displayname = res['displayname']
        f_name_png = res['f_name_png']
        f_name_pdf = res['f_name_pdf']
        
        # create caption
        h4 = root_template.new_tag('h4')
        h4.string = displayname
        node_div_distr.append(h4)
        
        caption = """
        Relative value of each share for the selection '{}'.
        """.format(displayname).strip()
        
        insert_figure(
            root_template, node_div_distr, dir_name_images, f_name_png, 
            f_name_pdf, caption)
        
    ###########################################################################
    # 5. best and worst days
    
    res_best_worst_days = config['res_best_worst_days']
    div_best_worst = root_template.find(
        "div", attrs = {"id": "div_best_worst_days_6739242"})
    
    # 5.1. iterate over each selection
    for rbwd in res_best_worst_days:
        
        # 5.1.1 read results
        config = rbwd['configuration']
        date_performance_list = rbwd['date_performance_list']
        
        # 5.1.2. create di element
        div = root_template.new_tag(
            "div", attrs={"class": "col-lg-4 col-md-6 col-sm-12"})
        div_best_worst.append(div)
        
        # 5.1.3. create caption
        h4 = root_template.new_tag("h4")
        h4.string = config['displayname']
        div.append(h4)
        
        # 5.1.4. create table
        table = root_template.new_tag(
            'table', attrs={'class': 'table table-striped table-auto-width'})
        div.append(table)
        
        # 5.1.5. create table head
        thead = root_template.new_tag('thead')
        table.append(thead)
        
        tr = root_template.new_tag('tr')
        thead.append(tr)
        
        # first column shows the rank of the day
        td = root_template.new_tag('td', attrs={'scope': 'col'})
        td.string = "#"
        tr.append(td)
        
        # second column shows the date
        td = root_template.new_tag('td', attrs={'scope': 'col'})
        td.string = "Date"
        tr.append(td)
        
        # third column shows the performance at this day
        td = root_template.new_tag('td', attrs={'class': 'text-right', 'scope': 'col'})
        td.string = "Performance"
        tr.append(td)
        
        # 5.1.6. create table body
        tbody = root_template.new_tag('tbody')
        table.append(tbody)
        
        # 5.1.7. print the best 10 days
        for i in range(10):
            i_tmp = i
            
            if(i_tmp > len(date_performance_list) - 1):
                break
            
            # format strings
            s_date = date_performance_list[i_tmp][0].strftime("%d.%m.%Y")
            s_performance = "{:+.2f} %".format(
                date_performance_list[i_tmp][1] * 100)
            
            # create row
            tr = root_template.new_tag('tr')
            tbody.append(tr)
    
            # first cell: rank
            td = root_template.new_tag('td')
            td.string = str(i_tmp + 1)
            tr.append(td)
            
            # second cell: date
            td = root_template.new_tag('td')
            td.string = s_date
            tr.append(td)
            
            # third cell: performance
            td = root_template.new_tag('td', attrs={'class': 'text-right td-day-positive'})
            td.string = s_performance
            tr.append(td)
        
        if(len(date_performance_list) < 10):
            break
        
        # 5.1.8. create intermediate row
        tr = root_template.new_tag('tr')
        tbody.append(tr)

        td = root_template.new_tag('td')
        td.string = "..."
        tr.append(td)

        td = root_template.new_tag('td')
        td.string = "..."
        tr.append(td)

        td = root_template.new_tag('td', attrs={'class': 'text-right'})
        td.string = "..."
        tr.append(td)
        
        # 5.1.9. show 10 worst days
        for i in range(10):
            i_tmp = len(date_performance_list) - 10 + i
            
            # format strings
            s_date = date_performance_list[i_tmp][0].strftime("%d.%m.%Y")
            s_performance = "{:+.2f} %".format(
                date_performance_list[i_tmp][1] * 100)
            
            # create row
            tr = root_template.new_tag('tr')
            tbody.append(tr)
            
            # first cell: rank
            td = root_template.new_tag('td')
            td.string = str(i_tmp + 1)
            tr.append(td)
            
            # second cell: date
            td = root_template.new_tag('td')
            td.string = s_date
            tr.append(td)
            
            # third cell: performance
            td = root_template.new_tag(
                'td', attrs={'class': 'text-right td-day-negative'})
            td.string = s_performance
            tr.append(td)
    
    # 6. prettify document
    s_out = root_template.prettify().encode('UTF-8')
    
    # 7. write output
    with open(f_path_html, 'wb') as f:
        f.write(s_out)



def insert_figure(root_node, node_div, dir_name_images, f_name_png, f_name_pdf,
                  caption):
    # create figure
    node_figure = root_node.new_tag(
        'figure', attrs={"class": "fig-center"})
    node_div.append(node_figure)
    
    # link to image
    node_img = root_node.new_tag(
        "img", attrs={"src": "{}/{}".format(dir_name_images, f_name_png),
                      "class": "img-fluid img-single-col"})
    node_figure.append(node_img)
    
    # create caption
    node_caption = root_node.new_tag(
        "figcaption", attrs={"class": "igure-caption"})
    node_caption.string = caption
    
    
    
    # create link to pdf, add to figure caption
    node_link = root_node.new_tag(
        "a", attrs={"href": "{}/{}".format(dir_name_images, f_name_pdf),
                    "target": "_blank"})
    node_link.string = "Detailed view"
    node_caption.string.insert_after(node_link)
    
    node_figure.append(node_caption)


    
def get_keys_from_category_list(share_data_dict, category_list):
    """
    Get all keys, which are associated to a category, which is also listed
    in ``category_list``. If ``category_list == "all"``, then all
    keys will be returned.
    """
    
    # get a list of all keys
    key_list = share_data_dict.keys()
    
    # 1. create result variable
    key_list_valid = []
    
    # 2. iterate over each key
    for key in key_list:
        # add key if
        #  - (b1) category_list is "all"
        #  - (b2) intersection between categories of the share and 
        #    category_list is not empty
        
        b1 = category_list == "all"
        b2 = (
            len(set(share_data_dict[key]['category'])
                .intersection(category_list)) > 0)
        
        if(b1 or b2):
            key_list_valid.append(key)
    
    # 3. return result
    return key_list_valid


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
    print("Nothing to be done here.")
    
    