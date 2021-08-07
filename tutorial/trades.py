# -*- coding: utf-8 -*-
"""
File containing the list of trades and dividends.
"""

from datetime import datetime


def get_trades():
    """
    Returns a list of trades.
    """
    list_trades = []
    
    list_trades.append((datetime(2021,  3,  15), "870747",       0.12470,    25.00,   0.44))  # buy
    list_trades.append((datetime(2021,  4,   1),    "BTC",    0.00030281,    15.00,   0.00))  # buy
    list_trades.append((datetime(2021,  4,  15), "870747",       0.11332,    25.00,   0.44))  # buy
    list_trades.append((datetime(2021,  5,   1),    "BTC",    0.00031381,    15.00,   0.00))  # buy
    list_trades.append((datetime(2021,  5,  17), "870747",       0.12181,    25.00,   0.44))  # buy
    list_trades.append((datetime(2021,  6,   1),    "BTC",    0.00050002,    15.00,   0.00))  # buy
    list_trades.append((datetime(2021,  6,  15), "870747",       0.11515,    25.00,   0.44))  # buy
    list_trades.append((datetime(2021,  6,  30), "870747",      -0.10000,   -22.45,   0.40))  # sell
    list_trades.append((datetime(2021,  7,   1),    "BTC",    0.00048418,    15.00,   0.00))  # buy
    list_trades.append((datetime(2021,  7,  15), "870747",       0.10323,    25.00,   0.44))  # buy
    
    return list_trades
    
def get_dividends():
    """
    Returns a list of dividends.
    """
    
    #dividends
    list_dividends = []
    
    return list_dividends
