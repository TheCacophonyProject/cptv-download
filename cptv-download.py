#!/usr/bin/python

from pathlib import Path
import os

import json
import datetime

from api import API
from pool import Pool
from dateutil.parser import parse as parsedate

import argparse


class CPTVDownloader:

    def __init__(self):
        self.start_date = None
        self.end_date = None
        self.limit = None

        # list of tags to ignore
        self.ignore_tags = []

        # if specified only these tags will be processed (otherwise all non ignored tags will be processed
        self.only_tags = None

        self.auto_delete = False
        self.verbose = False

        self.user = None
        self.password = None
        self.out_folder = None

        self.workers = 4

        self.include_metadata = True
        self.include_mp4 = False

        # dictionary mapping filename to paths of all files in output folder
        self.file_list = {}

    def log(self, message):
        if self.verbose:
            print(message)

    def process(self, url):
        """ Downloads all requested files from specified server """

        api = API(url, self.user, self.password)

        print("Querying server {0}".format(url))
        rows = api.query(limit=self.limit, startDate=self.start_date, endDate=self.end_date)

        if self.auto_delete:
            self.update_file_locations()

        pool = Pool(self.workers, self._downloader, api, Path(self.out_folder))
        file_count = 0
        for row in rows:
            file_count += 1
            pool.put(row)
        pool.stop()
        print("Finished {0} files.".format(file_count))

    def update_file_locations(self):
        """ Scans output folder building a list of all files. """
        self.file_list = {}

        for root, subdirs, files in os.walk(self.out_folder):
            for file in files:
                if file not in self.file_list:
                    self.file_list[file] = []
                self.file_list[file].append(root)

    def _downloader(self, q, api, out_base):
        """ Worker to handle downloading of files. """
        while True:
            r = q.get()

            if r is None:
                break

            try:
                tag_dir = get_tag_directory(r['Tags'])

                out_dir = os.path.join(out_base, tag_dir)
                dt = parsedate(r['recordingDateTime'])
                file_base = dt.strftime("%Y%m%d-%H%M%S") + "-" + r['Device']['devicename']

                path_base = os.path.join(out_dir, file_base)

                if self.auto_delete:
                    if file_base+'.cptv' in self.file_list:
                        for existing_path in self.file_list[file_base+'.cptv']:
                            if existing_path != out_dir:
                                print("Found {} in {} but should be in {}".format(file_base, existing_path, out_dir))
                                remove_file(os.path.join(existing_path, file_base + '.cptv'))
                                remove_file(os.path.join(existing_path, file_base + '.dat'))
                                remove_file(os.path.join(existing_path, file_base + '.mp4'))

                if tag_dir in self.ignore_tags:
                    continue

                if self.only_tags and tag_dir not in self.only_tags:
                    continue

                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)

                if iter_to_file(path_base + '.cptv', api.download_cptv(r['id'])):
                    print(format_row(r) + '.cptv' + " [{}]".format(tag_dir))

                if self.include_mp4:
                    if iter_to_file(path_base + '.mp4', api.download_mp4(r['id'])):
                        print(format_row(r) + '.mp4' + " [{}]".format(tag_dir))

                if self.include_metadata:
                    if not os.path.exists(path_base+'.txt'):
                        json.dump(r, open(path_base+'.txt', 'w'), indent=4)

            finally:
                q.task_done()


def remove_file(file):
    """ Delete a file (if it exists). """
    if os.path.exists(file):
        try:
            os.remove(file)
        except Exception as e:
            print("Warning, could not remove file {}. Error: {}".format(file, e))


def get_tag_directory(tags):
    """Determine the directory store videos in based on tags. """

    if tags is None or len(tags) == 0:
        return "untagged"

    # get a unique list of tags.
    # note, tags can have event set to 'false positive' in which case we use this as the 'animal' type.
    tags = list(set(tag['animal'] if tag['event'] != 'false positive' else 'false-positive' for tag in tags))

    if len(tags) >= 2:
        return "multi"

    return tags[0]


def format_row(row):
    return "{} {} {}s".format(
        row['id'], row['Device']['devicename'], row['duration'])


def iter_to_file(filename, source, overwrite=False):
    if not overwrite and Path(filename).is_file():
        return False
    with open(filename, "wb") as f:
        for chunk in source:
            f.write(chunk)
    return True


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('out_folder', default=None, help='Root folder to place downloaded files in.')
    parser.add_argument('user', default=None, help='Username')
    parser.add_argument('password', default=None, help='Password')

    parser.add_argument('-s', '--server', default=['https://api-test.cacophony.org.nz', 'https://api.cacophony.org.nz'],
                        help='CPTV file server URL')
    parser.add_argument('--start-date', default=None,
                        help='If specified only files recorded on or after this date will be downloaded.')
    parser.add_argument('--end-date', default=None,
                        help='If specified only files recorded before or on this date will be downloaded.')
    parser.add_argument('-r', '--recent', type=int, default=None,
                        help='Download files only from the previous n days (overwrites start-date and end-date')

    parser.add_argument('-t', '--tag', default=None,
                        help='Specific tag to download, of not specified all non ignored tags will be downloaded')
    parser.add_argument('-i', '--ignore', default=['untagged', 'multi'],
                        help='List of tags to ignore')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='Print additional information')
    parser.add_argument('-x', '--auto-delete', action="store_true", default=False,
                        help='If enabled clips found in sub-folders other than their tag folder will be deleted.')
    parser.add_argument('-l', '--limit', default=1000, help='Limit number of downloads')

    args = parser.parse_args()

    downloader = CPTVDownloader()

    downloader.out_folder = args.out_folder
    downloader.user = args.user
    downloader.password = args.password

    downloader.start_date = args.start_date
    downloader.end_date = args.end_date

    if args.recent:
        print("Downloading new clips from the past {} days.".format(args.recent))
        downloader.start_date = datetime.datetime.now() - datetime.timedelta(days=args.recent)
        downloader.end_date = datetime.datetime.now()

    downloader.only_tags = args.tag
    downloader.ignore_tags = args.ignore
    downloader.limit = args.limit
    downloader.verbose = args.verbose
    downloader.auto_delete = args.auto_delete

    if downloader.auto_delete:
        print("Auto delete enabled.")

    server_list = []
    if args.server:
        server_list = args.server if type(args.server) == list else [args.server]

    for server in server_list:
        downloader.process(server)


if __name__ == '__main__':
    main()
