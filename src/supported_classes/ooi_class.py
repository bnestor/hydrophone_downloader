from supported_classes.base_class import BaseDownloadClass

import requests
import os
import obspy
import glob
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import json
import re

# import pandas as pd
import polars as pl
from datetime import datetime, timedelta, timezone

from typing import Union

class OOIDownloadClass(BaseDownloadClass):
    def __init__(self, ):
        super().__init__()

        self.url_to_raw_data = "https://rawdata-west.oceanobservatories.org/files/"

        self.hydrophone_directories = ['CE02SHBP', 'CE04OSBP', 'RS01SBPS', 'RS01SLBS', 'RS03AXBS', 'RS03AXPS','CE02SHBP','CE04OSBP', 'RS01SBPS', 'RS01SLBS', 'RS03AXBS', 'RS03AXPS']
        self.source = 'OOI'
        self.license = None
        
        self.metadata = {'CE02SHBP': {'latitude': 44.6371, 'longitude': -124.306, 'depth': 79, 'reference_designator':'CE02SHBP-LJ01D-06-CTDBPN106'},
                         'CE04OSBP': {'latitude': 44.3695, 'longitude': -124.954, 'depth': 579 , 'reference_designator':'CE04OSBP-LJ01C-06-DOSTAD108'},
                        'RS01SBPS': {'latitude': 44.529, 'longitude': -125.3893, 'depth': 2906, 'reference_designator':'RS01SBPS-PC01A-4C-FLORDD103'},
                        'RS01SLBS': {'latitude': 44.5153, 'longitude': -125.3898, 'depth': 2901, 'reference_designator':'RS01SLBS-LJ01A-12-DOSTAD101'},
                        'RS03AXBS': {'latitude': 45.8168, 'longitude': -129.7543, 'depth': 2906, 'reference_designator':'RS03AXBS-LJ03A-12-CTDPFB301'},
                        'RS03AXPS': {'latitude': 45.8305, 'longitude': -129.7535, 'depth': 2607, 'reference_designator':'RS03AXPS-PC03A-4A-CTDPFA303'},
        }

                         

        self.__post_init__()

    def get_deployments(self, ):
        """
        OOI deployments are located at the following URL:
        
        https://rawdata-west.oceanobservatories.org/files/
        a list of deployments, each deployment is a day of data, containing a dict of the following:
        {
            'date': datetime.datetime (utc timezone),
            'latitude': float,
            'longitude': float,
            'depth': float,
            'license': str,
            'source': str,
            # any other information that is useful to save
        }

from ooi_class import OOIDownloadClass
ooi = OOIDownloadClass()
ooi.download_data(min_lat=40, max_lat=50, min_lon=-129, max_lon=-124, min_depth=0, max_depth=1000, start_time='2016-01-01',end_time='2016-12-31', license=None, save_dir='data/')

        
        
        
        """


        deployments = []
        # now = pd.Timestamp.now()
        # now = pl.datetime.now()
        now = datetime.now().strftime('%Y-%m-%d')
        for link in ['https://rawdata.oceanobservatories.org/files/CE02SHBP/LJ01D/HYDBBA106/',
                'https://rawdata.oceanobservatories.org/files/CE04OSBP/LJ01C/HYDBBA105/',
                'https://rawdata.oceanobservatories.org/files/RS01SBPS/PC01A/HYDBBA103/',
                'https://rawdata.oceanobservatories.org/files/RS01SLBS/LJ01A/HYDBBA102/',
                'https://rawdata.oceanobservatories.org/files/RS03AXBS/LJ03A/HYDBBA302/',
                'https://rawdata.oceanobservatories.org/files/RS03AXPS/PC03A/HYDBBA303/']:
            item_key = [d for d in self.metadata.keys() if d in link][0]
            # for date in pd.date_range(start='2015-09-01', end=now, freq='D'):

            from_date = datetime.strptime('2015-09-01', '%Y-%m-%d')
            to_date = datetime.strptime(now, '%Y-%m-%d')
            for date in pl.date_range(start=from_date, end=to_date, interval='1d', eager=True).alias('date').to_frame().to_dict()['date']:

                if type(date) is not datetime:
                    date = datetime.combine(date, datetime.min.time())  # ensure date is a datetime object

                # check if the date has timezone information, if not, add UTC timezone
                if date.tzinfo is None:
                    date_iso = date.replace(tzinfo=timezone.utc)


                new_link = os.path.join(link, date.strftime('%Y/%m/%d/')) # add the extensions to download the files from this date
                deployments.append({'date': date_iso, 'latitude': self.metadata[item_key]['latitude'], 'longitude': self.metadata[item_key]['longitude'], 'depth': self.metadata[item_key]['depth'], 'license': self.license, 'source': self.source, 'link': new_link, 'reference_designator': self.metadata[item_key]['reference_designator'],})

        print(f'There are {len(deployments)} days of deployments available from OOI')
        self.deployments = deployments

        return deployments



    
    def download_data(self, min_lat, max_lat, min_lon, max_lon, min_depth, max_depth, license, start_time, end_time, save_dir):
        """
        Download data from OOI
        """

        print(self.deployments[:10])

        # check for overlap in deployments
        deployments = self.filter_deployments(min_lat, max_lat, min_lon, max_lon, min_depth, max_depth, license, start_time, end_time)
        if len(deployments)==0:
            print("No data from OOI is available for the specified parameters.")
            return
        
        # otherwise, iterate through and download each deployment
        print(f"Downloading {len(deployments)} deployments from OOI")
        for deployment in deployments:

            # first, make sure that the data are not already downloaded
            self.download_deployment(deployment, save_dir, start_time, end_time)

            

    def download_deployment(self,
                            deployment: dict,
                            save_dir: str,
                            start_time: Union[None, str]=None,
                            end_time: Union[None, str]=None
                            ):
        """
        Download data for a single deployment
        """

        # get the deployment URL
        url = deployment['link']
        print(f"Downloading data from {url}")

        # get the directory name
        directory = url.split('files/')[-1]
        # print(directory)
        # get the base directory
        base_dir = os.path.join(save_dir, directory)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            for link in reversed(soup.find_all('a')):
                href = link.get('href')
                if href.endswith('.mseed'):
                    # for example href is ./OO-HYEA2--YDH-2018-01-01T00:00:00.000000.mseed
                    # and url is https://rawdata-west.oceanobservatories.org/files/CE02SHBP/LJ01D/11-HYDBBA106/2018/01/01/
                    # we want to save the file to os.path.join(base_dir, 'CE02SHBP/LJ01D/11-HYDBBA106/2018/01/01/OO-HYEA2--YDH-2018-01-01T00:00:00.000000.mseed')
                    absolute_url = urljoin(url, href)

                    
                    # absolute_url example: https://rawdata.oceanobservatories.org/files/CE02SHBP/LJ01D/HYDBBA106/2025/05/24/OO-HYEA2--YDH-2025-05-24T23:55:00.000000Z.mseed
                    # filter using regex to extract the filename with timestamp
                    filename_timestamp = datetime.fromisoformat(re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z', absolute_url).group(0))
                    if start_time is not None:
                        if type(start_time) is str:
                            start_time = datetime.fromisoformat(start_time)
                            if start_time.tzinfo is None:
                                start_time = start_time.replace(tzinfo=timezone.utc)
                        if type(end_time) is str:
                            end_time = datetime.fromisoformat(end_time)
                            if end_time.tzinfo is None:
                                end_time = end_time.replace(tzinfo=timezone.utc)
                        if filename_timestamp < start_time:
                            continue
                    if end_time is not None:
                        if filename_timestamp > end_time:
                            continue

                    d = requests.get(absolute_url)
                    if int(d.headers['Content-Length'])<1000000:
                        continue

                    print('absolute_url:',absolute_url)

                    local_path = os.path.join(base_dir, os.path.basename(absolute_url)).replace(':','')
                    # print('local_path:',local_path)

                    
                    
                    

                    # Ensure the directory structure exists
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)

                    # Download the file
                    if not(os.path.exists(local_path) or os.path.exists(local_path.replace('.mseed','.flac'))):
                        # use wget silently and non blocking
                        # print(f'wget -q  {absolute_url} -O '+ local_path.replace(" ", "\ "))
                        os.system(f'wget -q  {absolute_url} -O '+local_path.replace(" ", "\ "))

        # also save a metadata file
        hash = self.get_git_hash()
        deployment.update({'git_version': hash})
        # get current date
        deployment.update({'download_date': datetime.now().strftime('%Y-%m-%d')})
        # deployment.update({'date': deployment['date'].strftime('%Y-%m-%d')})
        #date in ISO format
        deployment.update({'date': deployment['date'].strftime('%Y%m%dT%H%M%SZ')})

        # save to the base directory
        with open(os.path.join(base_dir, 'metadata.json'), 'w') as f:
            json.dump(deployment, f)


        # bibtex
        # NSF Ocean Observatories Initiative. (date or year published). Instrument and/or data product(s) (reference designator, if applicable) data (from Platform, optional if providing reference designator) (at Array, optional if providing reference designator) from (start date) to (end date). (Repository). (URL). Accessed on (date accessed).
        bibtex=f"""@misc{{{deployment['reference_designator']}_{deployment['date']},
    'title': 'NSF Ocean Observatories Initiative',
    'year': {datetime.now().strftime('%Y')},
    'howpublished': 'Instrument and/or data product(s) {deployment['reference_designator']} data from {datetime.fromisoformat(deployment["date"]).strftime("%Y-%m-%d")} to {(datetime.fromisoformat(deployment["date"])+timedelta(days=1) ).strftime("%Y-%m-%d")}',
    'publisher': 'Raw Data Archive',
    'url': {url},
    'accessed': {datetime.now().strftime("%Y-%m-%d")},}}"""
        
        with open(os.path.join(base_dir, 'bibtex.txt'), 'w') as f:
            f.write(bibtex)
        

        all_mseed_files = glob.glob(os.path.join(base_dir, '*.mseed'))
        mseed2flac(all_mseed_files)





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
    print('here')
    for filename in filenames:
        print(filename)
        if not(filename.endswith('mseed')):continue
        print(filename)
        try:
            st = obspy.read(filename, format='mseed')
            st.merge(fill_value=0)
            sample_rate = st[0].stats['sampling_rate']
            st.write(filename.replace('mseed','wav'), format='WAV', framerate=sample_rate)
            # by default say no to overwrite
            os.system('ffmpeg -n -i '+filename.replace(' ', '\ ').replace('mseed','wav')+' -c:a flac '+filename.replace(' ', '\ ').replace('mseed','flac')+"&& rm "+filename.replace(' ', '\ ').replace('mseed','wav'))
            # os.system('rm '+filename.replace(' ', '\ ').replace('mseed','wav'))
            os.system('rm '+filename.replace(' ', '\ ')) # also remove mseed file

        except:
            print('Failed to convert '+filename)
            continue




