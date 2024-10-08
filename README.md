# hydrophone_downloader
A command line tool to query data from various hydrophone sources. Each ffolder will also download a bibtex entry for dataset citation, and a metadata.json so that the download query is fully reproducible.
Data is automatically converted to FLAC format for lossless compression. 

## Installation
Requirements: python 3 environment

```pip install git+https://github.com/bnestor/hydrophone_downloader.git```

To edit or add your own data sources:

```
git clone https://github.com/bnestor/hydrophone_downloader.git
cd hydrophone_downloader
pip install -e .
```


## Usage
You may need to get a token from Ocean Networks Canada if you wish to download data from their servers. According to [the documentation](https://wiki.oceannetworks.ca/display/O2A/API+Reference), users should generate the token by "logging in at [http://data.oceannetworks.ca/Profile](http://data.oceannetworks.ca/Profile). Click the "Web Services" tab, then click "Generate Token" "

Then you may set your token by running the command:
```
hydrophone-downloader-set-token ONC_token=<your_token_here> # this only needs to be done once
```



Open up a terminal or command prompt and type:
```
hydrophone-downloader min_latitude=40 max_latitude=50 min_longitude=-129 max_longitude=-123 min_depth=0 max_depth=1000 start_time="2015-01-01" end_time="2020-12-31" save_dir="/path/to/large/storage"
```

## Supported Hydrophone Sources
- Ocean Networks Canada: [https://www.oceannetworks.ca/](https://www.oceannetworks.ca/)
- Ocean Observatories Initiative: [https://oceanobservatories.org/](https://oceanobservatories.org/)

## Coming Soon
- Log to avoid redundant downloads

## Contributing
If you have a hydrophone source, create a custom class that inherits from `src/configs/base_class.py`. If token-access is required, you may need to modify the `src/configs/token_config.yaml` as well.

