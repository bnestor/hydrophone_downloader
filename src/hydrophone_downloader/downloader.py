"""
onc_download.py
"""
import os

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

import json
from contextlib import closing
import errno
from copy import deepcopy


import shutil
import glob
import random
import time


from supported_classes.ooi_class import OOIDownloadClass
from supported_classes.onc_class import ONCDownloadClass
from supported_classes.orcasound_class import OrcasoundDownloadClass


def download_data(
        min_lat=0, 
        max_lat=0,
        min_lon=0, 
        max_lon=0, 
        min_depth=0,
        max_depth=0,
        license=None,
        start_time=None,
        end_time=None,
        save_dir="",
    ):
    """
    """

    assert min_lat <= max_lat, "min_lat must be less than or equal to max_lat"
    assert min_lon <= max_lon, "min_lon must be less than or equal to max_lon"
    assert min_depth <= max_depth, "min_depth must be less than or equal to max_depth"

    print("min_lat:", min_lat)
    print("max_lat:", max_lat)
    print("min_lon:", min_lon)
    print("max_lon:", max_lon)
    print("min_depth:", min_depth)
    print("max_depth:", max_depth)
    print("license:", license)
    print("start_time:", start_time)
    print("end_time:", end_time)
    print("save_dir:", save_dir)




    all_classes = [ONCDownloadClass(), OOIDownloadClass(),OrcasoundDownloadClass()]

    for download_class in all_classes:
        download_class.download_data(
            min_lat, 
            max_lat,
            min_lon, 
            max_lon, 
            min_depth,
            max_depth,
            license,
            start_time,
            end_time,
            save_dir,
        )

    return

 
