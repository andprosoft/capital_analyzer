# -*- coding: utf-8 -*-
"""
Main Downloader module.
"""

from capital_analyzer.download_data import download_data

from demo_share_data import get_share_data_dict


def demo_download_data():
    """
    Method to download the historical share data.
    """
    
    share_data_dict = get_share_data_dict()
    
    download_data(share_data_dict)
    
    
if __name__ == "__main__":
    demo_download_data()
    


