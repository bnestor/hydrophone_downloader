from supported_classes.base_class import BaseDownloadClass

# import requests
import os
import glob
# from urllib.parse import urljoin
import boto3
from botocore import UNSIGNED
from botocore.config import Config


# from bs4 import BeautifulSoup
import json
import re
from copy import deepcopy
from tqdm import tqdm

#async
import asyncio
import concurrent.futures
import tqdm.asyncio

# import pandas as pd
import polars as pl
from datetime import datetime, timedelta, timezone
import obspy

class OrcasoundDownloadClass(BaseDownloadClass):
    def __init__(self, ):
        super().__init__()

        self.url_to_raw_data = "https://rawdata-west.oceanobservatories.org/files/"

        self.S3_STREAM_URLS = {
            "bush_point": "https://s3-us-west-2.amazonaws.com/audio-orcasound-net/rpi_bush_point",
            "mast_center": "https://s3-us-west-2.amazonaws.com/audio-orcasound-net/rpi_mast_center",
            "north_sjc": "https://s3-us-west-2.amazonaws.com/audio-orcasound-net/rpi_north_sjc",
            "orcasound_lab": "https://s3-us-west-2.amazonaws.com/audio-orcasound-net/rpi_orcasound_lab",
            "point_robinson": "https://s3-us-west-2.amazonaws.com/audio-orcasound-net/rpi_point_robinson",
            "port_townsend": "https://s3-us-west-2.amazonaws.com/audio-orcasound-net/rpi_port_townsend",
            "sunset_bay": "https://s3-us-west-2.amazonaws.com/audio-orcasound-net/rpi_sunset_bay",
            "archive": "https://s3-us-west-2.amazonaws.com/archive-orcasound-net/rpi_port_townsend"
        }

        # self.s3 = boto3.resource('s3')
        self.s3 = boto3.resource('s3', config=Config(signature_version=UNSIGNED))
        self.s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))


        

        # locations are approximate based off of orcasound map        
        
        self.metadata = {'bush_point': {'latitude': 48.0334, 'longitude': -122.6053, 'depth': 1, },
                         'mast_center': {'latitude': 47.3489, 'longitude':  -122.3247, 'depth': 5 , },
                        'north_sjc': {'latitude': 48.5897, 'longitude': -123.0651, 'depth': 10, },
                        'orcasound_lab': {'latitude': 48.5602, 'longitude': -123.1761, 'depth': 5, },
                        'point_robinson': {'latitude': 47.3880, 'longitude': -122.3738, 'depth': 5, },
                        'port_townsend': {'latitude': 48.1356, 'longitude': -122.7606, 'depth': 7,},
                        'sunset_bay': {'latitude': 47.8654,  'longitude': -122.3339, 'depth': 5, },
        }



                         

        self.__post_init__()

    def get_deployments(self, ):
        """
        a list of deployments, each deployment is a day of data, containing a dict of the following:
        {
            'date': 'YYYY-MM-DD',
            'latitude': float,
            'longitude': float,
            'depth': float,
            'license': str,
            'source': str,
            # any other information that is useful to save
        }

from orcasound_class import OrcasoundDownloadClass
odc = OrcasoundDownloadClass()
odc.download_data(min_lat=40, max_lat=50, min_lon=-129, max_lon=-124, min_depth=0, max_depth=1000, start_time='2016-01-01',end_time='2016-12-31', license=None, save_dir='data/')

        
        """
        deployments = []

        for stream in self.S3_STREAM_URLS.keys():
            # list the s3 bucket
            bucket = self.s3.Bucket(self.S3_STREAM_URLS[stream].split('/')[-2])
            # for prefix in self.metadata.keys():
            objs = bucket.objects.filter(Prefix=os.path.basename(self.S3_STREAM_URLS[stream])+'/flac')
            for obj in objs: #objs: #bucket.objects.all()
                if obj.key.endswith('.flac'):
                    # typical filename is 2023-01-23_02-03-10_rpi_port_townsend-48000-2.flac
                    # first is date (UTC, then deployment, then sample rate, then number of channels)
                    # use regex to extract the datetime
                    date = re.search(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', obj.key).group(0)
                    #convert to datetime
                    date = datetime.strptime(date, '%Y-%m-%d_%H-%M-%S')

                    if date.tzinfo is None:
                        date = date.replace(tzinfo=timezone.utc)
                    
                    

                    # get the correct self.metadata key
                    k = [d for d in self.metadata.keys() if d in obj.key]
                    assert len(k)!=0, f'No key found for {obj.key}'

                    tmp = deepcopy(self.metadata[k[0]])
                    source = self.S3_STREAM_URLS[stream]
                    tmp.update({'date': date, 'license': 'CC BY-NC-SA 4.0', 'source': source, 'link': obj.key, })


                    deployments.append(tmp)



        print(f'There are {len(deployments)} files available from Orcasound')
        self.deployments = deployments

        return deployments



    
    def download_data(self, min_lat, max_lat, min_lon, max_lon, min_depth, max_depth, license, start_time, end_time, save_dir):
        """
        Download data from Orcasound
        """

        # check for overlap in deployments
        deployments = self.filter_deployments(min_lat, max_lat, min_lon, max_lon, min_depth, max_depth, license, start_time, end_time, verbose=False)
        if len(deployments)==0:
            print("No data from Orcasound is available for the specified parameters.")
            return
        
        # otherwise, iterate through and download each deployment
        print(f"Downloading {len(deployments)} deployments from Orcasound")
        # for deployment in deployments:
        #     self.download_deployment(deployment, save_dir, start_time=start_time, end_time=end_time)

        asyncio.run(self.async_download_deployments([d["link"] for d in deployments], save_dir, start_time=start_time, end_time=end_time))



    def download_deployment(self, deployment, save_dir, start_time=None, end_time=None):
        """
        Download data for a single deployment
        """

        # get the deployment URL
        if isinstance(deployment, dict):
            url = deployment['link']
        elif isinstance(deployment, str):
            # if deployment is a string, then it is the URL
            url = deployment
        else:
            raise ValueError("Deployment must be a string or a dictionary")

        # i.e. s3_client.download_file('audio-orcasound-net', 'rpi_port_townsend/flac/2025-05-21_00-00-14_rpi_port_townsend-48000-1.flac', f'{save_dir}/2025-05-21_00-00-14_rpi_port_townsend-48000-1.flac')

        if os.path.exists(os.path.join(save_dir, os.path.basename(url))):
            return
        
        
        # get the date from the filename using regex
        file_date = re.search(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', url).group(0)
        file_date = datetime.strptime(file_date, '%Y-%m-%d_%H-%M-%S')

        if file_date.tzinfo is None:
            file_date = file_date.replace(tzinfo=timezone.utc)

        
        if start_time is not None:
            start_time = datetime.fromisoformat(start_time) if isinstance(start_time, str) else start_time
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if file_date < start_time:
                return
        if end_time is not None:
            end_time = datetime.fromisoformat(end_time) if isinstance(end_time, str) else end_time
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            if file_date > end_time:
                return
            
        # print(f"Downloading {url} to {os.path.join(save_dir, os.path.basename(url))}")


        
        self.s3_client.download_file("audio-orcasound-net", # bucket name
                            url, # object name
                            os.path.join(save_dir, os.path.basename(url)), # file name
                            )
        
        return
    
    async def async_download_deployments(self, deployments, save_dir, start_time=None, end_time=None):
        """
        Download data for a single deployment
        """   

        loop = asyncio.get_event_loop()
        num_cpus = os.cpu_count()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=max(1, num_cpus - 1))
        blocking_tasks = [
            loop.run_in_executor(executor, self.download_deployment, deployment, save_dir, start_time, end_time)
            for deployment in deployments
        ]
        results = []
        # Note: tqdm.asyncio.tqdm.as_completed returns a *generator*, not an *async generator*
        for fut in tqdm.asyncio.tqdm.as_completed(blocking_tasks, total=len(blocking_tasks)):
            res = await fut  # Await each as they complete
            results.append(res)
        return
    





def mseed2flac(filenames):
    # resolve wildcard characters
    print(filenames)
    if type(filenames)==str:
        if '*' in filenames:
            filenames = glob.glob(filenames, recursive=True)
    else:
        if len(filenames)==1:
            if '*' in filenames[0]:
                filenames = glob.glob(filenames[0], recursive=True)

    print(filenames)
    for filename in filenames:
        if not(filename.endswith('mseed')):continue
        try:
            st = obspy.read(filename, format='mseed')
            st.merge(fill_value=0)
            sample_rate = st[0].stats['sampling_rate']
            st.write(filename.replace('mseed','wav'), format='WAV', framerate=sample_rate)
            # by default say no to overwrite
            os.system('ffmpeg -n -i '+filename.replace(' ', '\ ').replace('mseed','wav')+' -c:a flac '+filename.replace(' ', '\ ').replace('mseed','flac'))
            os.system('rm '+filename.replace(' ', '\ ').replace('mseed','wav'))
            os.system('rm '+filename.replace(' ', '\ ')) # also remove mseed file

        except:
            print('Failed to convert '+filename)
            continue





# #####
# demo

# import asyncio
# import concurrent.futures
# import tqdm.asyncio
# import time

# def subtask(string1, string2):
#     print(string1 + ' ' + string2)
#     time.sleep(1)

# async def process_concurrent_loop(filenames):
#     loop = asyncio.get_event_loop()
#     executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
#     blocking_tasks = [
#         loop.run_in_executor(executor, subtask, filename1, filename2)
#         for filename1, filename2 in zip(filenames, reversed(filenames))
#     ]
#     results = []
#     # Note: tqdm.asyncio.tqdm.as_completed returns a *generator*, not an *async generator*
#     for fut in tqdm.asyncio.tqdm.as_completed(blocking_tasks, total=len(blocking_tasks)):
#         res = await fut  # Await each as they complete
#         results.append(res)
#     print(results)
#     return

# def main():
#     asyncio.run(process_concurrent_loop(list('abcdefghijklmnopqrstuvwxyz')))

# main()

