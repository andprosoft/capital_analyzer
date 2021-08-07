# -*- coding: utf-8 -*-
"""
Module to define the share data.
"""

def get_share_data_dict():
    """
    Returns the dictionary containing the share data.
    """

    share_data_dict = {}

    share_data_dict["870747"] = {
        "displayname": "Microsoft",
        "color": "b",
        "category": [
            "A"
        ],
        "download_dict": {
            "data_service": "wo",
            "download": 1,
            "instId": "10301",
            "marketId": "21"
        }
    }
    
    share_data_dict["BTC"] = {
        "displayname": "Bitcoin",
        "color": "darkorange",
        "category": [
            "crypto"
        ],
        "download_dict": {
            "data_service": "ariva",
            "download": 1,
            "secu": "111697700",
            "boerse_id": "163"
        }
    }
    
    share_data_dict["msci_world"] = {
        "displayname": "MSCI World",
        "color": "lightblue",
        "category": [
            "X"
        ],
        "download_dict": {
            "data_service": "ariva",
            "download": 1,
            "secu" : 226974,
            "boerse_id": "173"
        }
    }

    return share_data_dict


def get_split_list():
    """
    Returns the data for the share splits.
    """
    
    split_list = []
    
    return split_list




