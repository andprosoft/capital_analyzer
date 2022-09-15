# -*- coding: utf-8 -*-
"""
Created on Wed Jul 21 23:14:37 2021

@author: andri
"""

from datetime import datetime
from dateutil.rrule import rrule, DAILY

from demo_share_data import get_share_data_dict
from capital_analyzer.analyze_trades import get_chart_data

def create_demo(f_path_out):
    """
    Fancy documentation.
    """
    
    first_date = datetime(2019,  1, 1)
    last_date = datetime.now()
    
    config_list = []
    
    # Microsoft
    config_list.append({
        "key" : "870747",
        "dom" : 15,
        "monthly_payment" : 25,
        "start_date": datetime(2019,  1, 1),
        "comission_rate": 0.0175
    })
    
    # Amazon
    config_list.append({
        "key" : "906866",
        "dom" : 15,
        "monthly_payment" : 25,
        "start_date": datetime(2019,  1, 1),
        "comission_rate": 0.0175
    })
    
    # Apple
    config_list.append({
        "key" : "865985",
        "dom" : 15,
        "monthly_payment" : 25,
        "start_date": datetime(2019,  1, 1),
        "comission_rate": 0.0175
    })

    # Airbus
    config_list.append({
        "key" : "938914",
        "dom" : 1,
        "monthly_payment" : 25,
        "start_date": datetime(2019,  6, 1),
        "comission_rate": 0.0175
    })

    # Boeing
    config_list.append({
        "key" : "850471",
        "dom" : 1,
        "monthly_payment" : 25,
        "start_date": datetime(2019,  6, 1),
        "comission_rate": 0.0175
    })

    # Allianz
    config_list.append({
        "key" : "840400",
        "dom" : 1,
        "monthly_payment" : 25,
        "start_date": datetime(2019,  6, 1),
        "comission_rate": 0.0175
    })

    # Nel
    config_list.append({
        "key" : "A0B733",
        "dom" : 1,
        "monthly_payment" : 25,
        "start_date": datetime(2020,  1, 1),
        "comission_rate": 0.0175
    })
    
    # Ballard Power
    config_list.append({
        "key" : "A0RENB",
        "dom" : 1,
        "monthly_payment" : 25,
        "start_date": datetime(2020,  1, 1),
        "comission_rate": 0.0175
    })
    
    # BTC
    config_list.append({
        "key" : "BTC",
        "dom" : 1,
        "monthly_payment" : 15,
        "start_date": datetime(2019,  3, 1),
        "comission_rate": 0.0000
    })
    
    # ETH
    config_list.append({
        "key" : "ETH",
        "dom" : 1,
        "monthly_payment" : 15,
        "start_date": datetime(2019,  9, 1),
        "comission_rate": 0.0000
    })
    
    global chart_data
    share_data_dict = get_share_data_dict()
    chart_data = get_chart_data(share_data_dict)


    lines = []
    
    lines.append("# -*- coding: utf-8 -*-")
    lines.append('"""')
    lines.append('Demo file containing the list of trades.')
    lines.append('"""')
    lines.append("")
    lines.append("from datetime import datetime")
    lines.append("")
    lines.append("def get_trades():")
    lines.append("")
    lines.append("    split_list = []")
    lines.append("")
    lines.append("    list_trades = []")
    lines.append("")

    for current_date in rrule(DAILY, dtstart=first_date, until=last_date):
        for config in config_list:
            key = config['key']
            dom = config['dom']
            monthly_payment = config['monthly_payment']
            start_date = config['start_date']
            comission_rate = config['comission_rate']
            
            comission = monthly_payment * comission_rate
            
            if(current_date < start_date or current_date.day != dom):
                continue
            
            date_list_chart = chart_data[key]['date_list']
            close_values_list = chart_data[key]['close_values_list']
            
            for i_date_chart, date_chart in enumerate(date_list_chart):
                if(date_chart >= current_date):
                    close_value = close_values_list[i_date_chart]
                    
                    amount = (monthly_payment - comission) / close_value
                    
                    s_format = '    list_trades.append((datetime({:4d}, {:2d},  {:2d}), {:>8}, {:13.5f}, {:8.2f}, {:6.2f}))'
                    if(key in ["BTC", "ETH"]):
                        s_format = '    list_trades.append((datetime({:4d}, {:2d},  {:2d}), {:>8}, {:13.8f}, {:8.2f}, {:6.2f}))'
                    
                    lines.append(s_format
                        .format(date_chart.year, date_chart.month, date_chart.day,
                                '"{}"'.format(key), amount, monthly_payment, comission))
                    break
            else:
                print("Tenemos un problema!", key, current_date)
            
            
            #print()

    lines.append("")



    lines.append("    return list_trades")
    
    lines.append("")
    lines.append("")
    lines.append("def get_dividends():")
    lines.append("    ")
    lines.append("    # dividends")
    lines.append("    list_dividends = []")
    lines.append("    ")
    lines.append("    return list_dividends")
                 
    
    for i_line, line in enumerate(lines):
        lines[i_line] = line + "\n"
    
    with open(f_path_out, 'w') as f:
        f.writelines(lines)
    
    
if __name__ == "__main__":
    f_path_out = "demo_trades.py"
    create_demo(f_path_out)
