#!/usr/bin/python

from pathlib import Path
import argparse

from dateutil.parser import parse as parsedate
from dateutil.tz import tzlocal

from cacophonyapi.user import UserAPI as API
from pool import Pool


MIME_TO_EXT = {
    "audio/mp4": "mp4",
    "video/mp4": "mp4",
    "audio/mp3": "mp3",
    "audio/mpeg": "mp3",
}

local_tz = tzlocal()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("out_folder", help="Folder to place downloaded files in")
    parser.add_argument("user", help="API server username")
    parser.add_argument("password", help="API server password")
    parser.add_argument(
        "-s",
        "--server",
        default="https://api.cacophony.org.nz",
        help="Cacophony API Server URL",
    )
    parser.add_argument(
        "--start-date",
        type=parsedate,
        help="If specified, only files recorded on or after this date will be downloaded.",
    )
    parser.add_argument(
        "--end-date",
        type=parsedate,
        help="If specified, only files recorded before or on this date will be downloaded.",
    )
    # FIXME - this should take device names
    parser.add_argument(
        "-d",
        "--device",
        type=int,
        action="append",
        help="Limit to this integer device id (can be used multiple times)",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=4,
        help="Number of concurrent downloads to run",
    )
    parser.add_argument(
        "-L",
        "--local-time",
        default=False,
        action="store_true",
        help="Convert timestamps in filenames to local time",
    )
    parser.add_argument(
        "-i",
        "--id",
        type=int,
        default=None,
        help="Download a specific recording (other options are ignored)",
    )

    args = parser.parse_args()

    args.out_folder = Path(args.out_folder)
    args.out_folder.mkdir(exist_ok=True)



    print("Querying recordings")
    api = API(args.server, args.user, args.password)
    if args.id is not None:
        recordings = [api.get(args.id)]
    else:
        recordings = api.query(
            type_="audio",
            startDate=args.start_date,
            endDate=args.end_date,
            devices=args.device,
            limit=99999,
        )
    print("Found {} recordings".format(len(recordings)))

    pool = Pool(args.workers, download, api, args)
    for recording in recordings:
        pool.put(recording)
    pool.stop()


def download(q, api, args):
    """Worker to handle downloading of files.
    """
    while True:
        r = q.get()
        if r is None:
            return
        try:
            try:
                out_path = download_name(r, args.local_time)
            except ValueError as err:
                print("error with {}: {}".format(r["id"], err))
                continue

            print("downloading " + str(out_path))
            iter_to_file(api.download_raw(r["id"]), str(args.out_folder / out_path))
        finally:
            q.task_done()


def download_name(r, local_time):
    dt = parsedate(r["recordingDateTime"])
    if local_time:
        dt = dt.astimezone(local_tz)
    device_name = r["Device"]["devicename"]

    mime_type = r.get("rawMimeType")
    if not mime_type:
        raise ValueError("recording has no raw mime type")
    ext = MIME_TO_EXT[mime_type]

    return f"{r['id']}-{device_name}-{dt.strftime('%Y%m%d-%H%M%S')}.{ext}"


def iter_to_file(source, filename):
    with open(filename, "wb") as f:
        for chunk in source:
            f.write(chunk)


if __name__ == "__main__":
    main()
