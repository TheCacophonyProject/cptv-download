#!/usr/bin/python

from pathlib import Path
import argparse

from dateutil.parser import parse as parsedate

from api import API
from pool import Pool


MIME_TO_EXT = {
    "audio/mp4": "mp4",
    "video/mp4": "mp4",
    "audio/mp3": "mp3",
    "audio/mpeg": "mp3",
}


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

    args = parser.parse_args()

    args.out_folder = Path(args.out_folder)
    args.out_folder.mkdir(exist_ok=True)

    print("Querying recordings")
    api = API(args.server, args.user, args.password)
    recordings = api.query(
        type_="audio",
        startDate=args.start_date,
        endDate=args.end_date,
        devices=args.device,
        limit=99999,
    )
    print("Found {} recordings".format(len(recordings)))

    pool = Pool(args.workers, download, api, args.out_folder)
    for recording in recordings:
        pool.put(recording)
    pool.stop()


def download(q, api, out_folder):
    """Worker to handle downloading of files.
    """
    while True:
        r = q.get()
        if r is None:
            return
        try:
            try:
                out_path = download_name(r)
            except ValueError as err:
                print("error with {}: {}".format(r["id"], err))
                continue

            print("downloading " + str(out_path))
            iter_to_file(api.download_raw(r["id"]), str(out_folder / out_path))
        finally:
            q.task_done()


def download_name(r):
    dt = parsedate(r["recordingDateTime"])
    device_name = r["Device"]["devicename"]

    mime_type = r.get("fileMimeType")
    if not mime_type:
        raise ValueError("recording has no mime type")
    ext = "." + MIME_TO_EXT[mime_type]

    return device_name + "-" + dt.strftime("%Y%m%d-%H%M%S") + ext


def iter_to_file(source, filename):
    with open(filename, "wb") as f:
        for chunk in source:
            f.write(chunk)


if __name__ == "__main__":
    main()
