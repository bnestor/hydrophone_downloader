"""
download_class.py

 a super class with some useful methods for downloading data from each source. This ensures standardisation between subclasses for the API and the CLI.

"""

import os

# from datetime import datetime
import datetime
import git

from typing import Union
import re




class BaseDownloadClass:
    def __init__(self, ):
        pass

    def __post_init__(self):
        self.deployments = self.get_deployments()

    def get_deployments(self,):
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
        """
        raise NotImplementedError("Subclasses must implement this method")
    

    def download_data(self, min_lat, max_lat, min_lon, max_lon, min_depth, max_depth, license, start_time, end_time, save_dir):
        raise NotImplementedError("Derived classes must implement this method.")
    
    
    def filter_deployments(self, 
                            min_lat: float,
                            max_lat: float,
                            min_lon: float,
                            max_lon: float,
                            min_depth: float,
                            max_depth: float,
                            license: str,
                            start_time: Union[datetime.datetime, datetime.date, str],
                            end_time: Union[datetime.datetime, datetime.date, str],
                            verbose=True) -> list:
        """
        Filter deployments based on the specified parameters
        """

        if isinstance(start_time, str):
            start_time = datetime.datetime.fromisoformat(start_time) #string must be in ISO 8601 format
        if isinstance(end_time, str):
            end_time = datetime.datetime.fromisoformat(end_time)

        # localize to UTC if tz is None
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=datetime.timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=datetime.timezone.utc)


        # deployments_out = [d for d in self.deployments if ((d['latitude']>=min_lat and d['latitude']<=max_lat) and (d['longitude']>=min_lon and d['longitude']<=max_lon)) and (d['depth']>=min_depth and d['depth']<=max_depth) ]
        # latitude_range
        if verbose: print("num deployments before filter:", len(self.deployments))
        deployments_out = [d for d in self.deployments if d['latitude']>=min_lat and d['latitude']<=max_lat]
        if verbose: print("num deployments after latitude filter:", len(deployments_out))
        # longitude_range
        deployments_out = [d for d in deployments_out if d['longitude']>=min_lon and d['longitude']<=max_lon]
        if verbose: print("num deployments after longitude filter:", len(deployments_out))
        # depth_range
        deployments_out = [d for d in deployments_out if d['depth']>=min_depth and d['depth']<=max_depth]
        if verbose: print("num deployments after depth filter:", len(deployments_out))
    
        if len(deployments_out)==0:
            print("No deployments found for the specified location.")
            return deployments_out
        
        print(deployments_out[0]['date'], type(deployments_out[0]['date']), start_time, type(start_time), end_time, type(end_time))


        if type(deployments_out[0]['date']) is datetime.date:
            deployments_out = [d for d in deployments_out if d['date']>=start_time.date() and d['date']<=end_time.date()] # option with no timestamps
        elif type(deployments_out[0]['date']) is datetime.datetime:
            assert type(deployments_out[0]['date']) is type(start_time), f"deployments_out date type {type(deployments_out[0]['date'])} does not match start_time type {type(start_time)}"
            assert type(deployments_out[0]['date']) is type(end_time), f"deployments_out date type {type(deployments_out[0]['date'])} does not match end_time type {type(end_time)}"


            start_time_date_only = datetime.datetime.combine(start_time.date(), datetime.time.min, tzinfo=start_time.tzinfo)
            deployments_out = [d for d in deployments_out if d['date']>=start_time_date_only and d['date']<=end_time] # option with timestamps
        else:
            raise ValueError(f"deployment is not a datetime or date object. It is a {type(deployments_out[0]['date'])}")

        if verbose: print("num deployments after time filter:", len(deployments_out))

        if len(deployments_out)==0:
            print("No deployments found for the specified time range.")
            return deployments_out

        if license is not None:
            deployments_out = [d for d in deployments_out if d['license']==license]
            if verbose: print("num deployments after license filter:", len(deployments_out))

        if len(deployments_out)==0:
            print("No deployments found for the specified license.")
            return deployments_out
        
        # for d in deployments_out:
        #     print(d)
        #     print(d['latitude'], min_lat, max_lat, d['latitude']>=min_lat and d['latitude']<=max_lat)
        #     print(d['longitude'], min_lon, max_lon, d['longitude']>=min_lon and d['longitude']<=max_lon)
        #     print(d['depth'], min_depth, max_depth, d['depth']>=min_depth and d['depth']<=max_depth)

        
        return deployments_out
    
    def get_git_hash(self):
        this_file_path = os.path.abspath(__file__)
        return git.Repo(this_file_path, search_parent_directories=True).head.object.hexsha
    
    
    def log(self, message):
        print(message)

    def read_log(self):
        with open('log.txt', 'r') as f:
            return f.read()