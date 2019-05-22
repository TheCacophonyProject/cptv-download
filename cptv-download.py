#!/usr/bin/python

from pathlib import Path
import argparse
import datetime
import json
import os

from dateutil.parser import parse

from api import API
from pool import Pool

SPECIAL_DIRS = ["test", "hard"]


class CPTVDownloader:
    def __init__(self):
        self.start_date = None
        self.end_date = None
        self.limit = None
        self.tag_mode = None
        self.recording_id = None
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

        if self.recording_id:
            recording = api.get(self.recording_id).get("recording")
            self._download(recording, api, Path(self.out_folder))
            return
        print("Querying server {0}".format(url))
        print("Limit is {0}".format(self.limit))
        print("Tag mode {0}".format(self.tag_mode))
        print("Dates are {0} - {1}".format(self.start_date, self.end_date))
        print("Required tags are {0}".format(self.only_tags))
        print("Ignore tags are {0}".format(self.ignore_tags))

        rows = api.query(
            limit=self.limit,
            startDate=self.start_date,
            endDate=self.end_date,
            tagmode=self.tag_mode,
            tags=self.only_tags,
        )

        if self.auto_delete:
            self.update_file_locations()

        pool = Pool(self.workers, self._downloader, api, Path(self.out_folder))
        for row in rows:
            pool.put(row)
        pool.stop()

    def update_file_locations(self):
        """ Scans output folder building a list of all files. """
        self.file_list = {}

        for root, _, files in os.walk(self.out_folder):
            for file in files:
                if file not in self.file_list:
                    self.file_list[file] = []
                self.file_list[file].append(root)

    def _downloader(self, q, api, out_base):
        """ Worker to handle downloading of files. """
        ignored = 0
        not_selected = 0
        processed = 0

        while True:

            r = q.get()
            if r is None:
                print(
                    "Worker processed %d and skipped %d files"
                    % (processed, ignored + not_selected)
                )
                break

            try:
                self._download(r, api, out_base)
                processed += 1
            finally:
                q.task_done()

    def _download(self, r, api, out_base):

        tags = r.get("Tags")
        tracks = r.get("Tracks")

        dt = parse(r["recordingDateTime"])
        file_base = dt.strftime("%Y%m%d-%H%M%S") + "-" + r["Device"]["devicename"]

        out_dir = os.path.join(out_base, get_distributed_folder(file_base))
        fullpath = os.path.join(out_dir, file_base)
        if self.auto_delete:
            self._delete_existing(file_base, out_dir)

        os.makedirs(out_dir, exist_ok=True)
        print("Processing ", file_base)

        if iter_to_file(fullpath + ".cptv", api.download_raw(r["id"])):
            print(format_row(r) + ".cptv" + " [{}]".format(out_dir))

        if self.include_mp4:
            if iter_to_file(fullpath + ".mp4", api.download(r["id"])):
                print(format_row(r) + ".mp4" + " [{}]".format(out_dir))

        if self.include_metadata:
            tracks = api.get_tracks(r["id"])
            r["additionalMetadata"] = ""
            r["tracks"] = tracks.get("tracks")
            if not os.path.exists(fullpath + ".txt"):
                json.dump(r, open(fullpath + ".txt", "w"), indent=4)

    def _delete_existing(self, file_base, new_dir):
        for path in self.file_list.get(file_base + ".cptv", []):
            path = Path(path)
            if str(path) != str(new_dir) and path.name not in SPECIAL_DIRS:
                print(
                    "Found {} in '{}' but should be in '{}'".format(
                        file_base, str(path), str(new_dir)
                    )
                )
                for ext in ["cptv", "dat", "mp4"]:
                    remove_file(str(path / (file_base + "." + ext)))


def remove_file(file):
    """ Delete a file (if it exists). """
    try:
        os.remove(file)
    except FileNotFoundError:
        pass
    except OSError as e:
        print("Warning, could not remove file {}. Error: {}".format(file, e))


def get_distributed_folder(name, num_folders=256, seed=31):
    """Creates a hash of the name then returns the modulo num_folders"""
    str_bytes = str.encode(name)
    hash_code = 0
    for byte in str_bytes:
        hash_code = hash_code * seed + byte

    return "{:02x}".format(hash_code % num_folders)


def get_tag_directory(tags):
    """Determine the directory store videos in based on tags. """

    if tags is None:
        return "untagged"

    # get a unique list of tags.
    # note, tags can have event set to 'false positive' in which case we use this as the 'animal' type.
    clip_tags = set()

    for tag in tags:
        if tag["automatic"]:
            continue
        tag_name = (
            tag["animal"] if tag["event"] != "false positive" else "false-positive"
        )
        clip_tags.add(tag_name)

    if len(clip_tags) >= 2:
        return "multi"

    if not clip_tags:
        return "untagged-by-humans"

    tag = list(clip_tags)[0]

    return tag.replace("/", "-")


def format_row(row):
    return "{} {} {}s".format(
        row["id"], row["Device"]["devicename"], row.get("duration")
    )


def iter_to_file(filename, source, overwrite=False):
    if not overwrite and Path(filename).is_file():
        return False
    with open(filename, "wb") as f:
        for chunk in source:
            f.write(chunk)
    return True


def main():
    parser = argparse.ArgumentParser()

    # yapf: disable
    parser.add_argument(
        'out_folder',
        help='Root folder to place downloaded files in.')
    parser.add_argument('user', help='API server username')
    parser.add_argument('password', help='API server password')
    parser.add_argument(
        '-s', '--server',
        default=['https://api.cacophony.org.nz'],
        help='CPTV file server URL')
    parser.add_argument(
        '--start-date',
        help='If specified, only files recorded on or after this date will be downloaded.')
    parser.add_argument(
        '--end-date',
        help='If specified, only files recorded before or on this date will be downloaded.')
    parser.add_argument(
        '-r', '--recent',
        type=int,
        help='Download files only from the previous n days (overwrites start-date and end-date')
    parser.add_argument(
        '-t', '--tag',
        action='append',
        default=[],
        help='Specific tag to download, of if not specified all non ignored tags will be downloaded - can use multiple times')
    parser.add_argument(
        '-i', '--ignore',
        action='append',
        default=None,
        help='Tag to ignore - can use multiple times')
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=False,
        help='Print additional information')
    parser.add_argument(
        '-x', '--auto-delete',
        action="store_true",
        default=False,
        help='If enabled clips found in sub-folders other than their tag folder will be deleted.')
    parser.add_argument(
        '-l', '--limit',
        default=1000,
        help='Limit number of downloads')
    parser.add_argument('--mp4', 
        dest='include_mp4', 
        action='store_true', 
        default=False,
        help='add if you want to download mp4 files')
    parser.add_argument('-m', '--tagmode', 
        dest='tag_mode', 
        default='automatic+human',
        help='Select videos by only a particular tag mode.  Default is only selects videos tagged by both humans and automatic')
    parser.add_argument('-id', 
        dest='recording_id', 
        default=None,
        help='Specify the recording id to download')
    # yapf: enable

    args = parser.parse_args()

    downloader = CPTVDownloader()
    downloader.recording_id = args.recording_id
    downloader.out_folder = args.out_folder
    downloader.user = args.user
    downloader.password = args.password

    if args.start_date:
        downloader.start_date = parse(args.start_date)

    if args.end_date:
        downloader.end_date = parse(args.end_date)

    if args.recording_id:
        print("Downloading Recording - {}".format(downloader.recording_id))
    elif args.recent:
        print("Downloading new clips from the past {} days.".format(args.recent))
        downloader.start_date = datetime.datetime.now() - datetime.timedelta(
            days=args.recent
        )
        downloader.end_date = datetime.datetime.now()

    downloader.only_tags = args.tag
    downloader.limit = args.limit
    downloader.verbose = args.verbose
    downloader.auto_delete = args.auto_delete
    downloader.include_mp4 = args.include_mp4
    downloader.tag_mode = args.tag_mode
    if args.ignore:
        downloader.ignore_tags = args.ignore
    else:
        downloader.ignore_tags = ["untagged", "multi", "untagged-by-humans"]

    if downloader.auto_delete:
        print("Auto delete enabled.")

    server_list = []
    if args.server:
        server_list = args.server if isinstance(args.server, list) else [args.server]

    for server in server_list:
        downloader.process(server)


if __name__ == "__main__":
    main()
