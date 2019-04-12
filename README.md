# cptv-download

This tool supports bulk downloading of thermal video recordings in
CPTV and MP4 format from a Cacophony API instance. Videos are grouped
into directories by the tagged animal type. Recordings are downloaded
in parallel.

```
usage: cptv-download.py [-h] [-s SERVER] [--start-date START_DATE]
                        [--end-date END_DATE] [-r RECENT] [-t TAG] [-i IGNORE]
                        [-v] [-x] [-l LIMIT] [--mp4] [-m TAG_MODE]
                        out_folder user password

positional arguments:
  out_folder            Root folder to place downloaded files in.
  user                  API server username
  password              API server password

optional arguments:
  -h, --help            show this help message and exit
  -s SERVER, --server SERVER
                        CPTV file server URL
  --start-date START_DATE
                        If specified, only files recorded on or after this
                        date will be downloaded.
  --end-date END_DATE   If specified, only files recorded before or on this
                        date will be downloaded.
  -r RECENT, --recent RECENT
                        Download files only from the previous n days
                        (overwrites start-date and end-date
  -t TAG, --tag TAG     Specific tag to download, of if not specified all non
                        ignored tags will be downloaded - can use multiple
                        times
  -i IGNORE, --ignore IGNORE
                        Tag to ignore - can use multiple times
  -v, --verbose         Print additional information
  -x, --auto-delete     If enabled clips found in sub-folders other than their
                        tag folder will be deleted.
  -l LIMIT, --limit LIMIT
                        Limit number of downloads
  --mp4                 add if you want to download mp4 files
  -m TAG_MODE, --tagmode TAG_MODE
                        Select videos by only a particular tag mode. Default
                        is only selects videos tagged by both humans and
                        automatic
```

# cptv-upload

This tool supports uploading of single audio and thermal video
recordings into a Cacophony API instance. This is particularly useful
for injecting recordings into a developer API server instance.

```
usage: cptv-upload.py [-h] server_url username password devicename filename

positional arguments:
  server_url  Server (base) url to send the CPTV files to
  username    Username to upload as
  password    Password to authenticate with
  devicename  Device to upload on behalf of
  filename    File to upload

optional arguments:
  -h, --help  show this help message and exit
```

## Installation

These tools require Python 3.6 or later.

* Create a virtualenv using your preferred method.
* Install dependencies: `pip install -r requirements.txt`
* Run with: `./cptv-download.py` or `./cptv-upload.py`

## Configuration

Use `--help` to see how to configure program.

## Queries

By default the most recent 100 recordings accessible to the user
account are queried but `API.query()` does support a number of
filtering options. The API server supports arbitrary queries so feel
free to extend `API.query()` if required.
