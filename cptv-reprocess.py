#!/usr/bin/python

import argparse
from datetime import datetime, timedelta

from cacophonyapi.user import UserAPI as API
from dateutil.parser import parse as parse_date
import time


def reprocess(args):
    """Reprocesses all specified recording from specified server"""

    api = API(args.server, args.user, args.password)

    print(f"Querying server {args.server}")
    print(f"Limit is {args.limit}")
    if len(args.recording_id) == 1:
        recordings = [
            int(rec_id) for rec_id in args.recording_id[0].split(",") if rec_id
        ]
        print(f"Reprocessing {recordings}")
        api.reprocess(recordings)
        return

    where = {
        "type": args.type,
    }
    if args.before is not None:
        where["recordingDateTime"] = {"$lt": args.before.isoformat()}
    else:
        where["recordingDateTime"] = {"$lt": datetime.now().isoformat()}

    if args.before is not None:
        where["recordingDateTime"] = {"$gt": args.after.isoformat()}

    print(where)
    if args.group_id:
        where["GroupId"] = args.group_id
    if args.device_id:
        where["DeviceId"] = args.device_id

    where["processingState"] = "FINISHED"
    limit = args.limit
    reprocessed = 0
    while limit is None or reprocessed < limit:
        rows = api.query(where=where, limit=100)
        # Sanity check
        if args.device_id is not None:
            for row in rows:
                assert row.get["deviceId"] == args.device_id
        if args.device_id is not None:
            for row in rows:
                assert row["groupId"] == args.group_id

        recording_ids = [row["id"] for row in rows]
        print(f"Reprocessing recording ids: {recording_ids}")
        api.reprocess(recording_ids)
        reprocessed += len(recording_ids)
        if len(rows) < limit:
            print("Done")
            break


def main():
    args = parse_args()
    if args.before is not None:
        args.before = parse_date(args.before)
    if args.after is not None:
        args.after = parse_date(args.after)
    reprocess(args)


def recording_range(range_s):
    id_range = range_s.split(":")
    if len(id_range) > 2:
        raise argparse.ArgumentTypeError(
            "multiple ':', exepected format of start:end or id,id2,... "
        )

    if len(id_range) == 2:
        try:
            all(int(x) for x in id_range if x)
        except ValueError:
            raise argparse.ArgumentTypeError("must be an int")

        if id_range[0] and id_range[1] and (int(id_range[0]) > int(id_range[1])):
            raise argparse.ArgumentTypeError("start > end, expected start:end")
    elif len(id_range) == 1:
        try:
            all(int(x) for x in id_range[0].split(",") if x)
        except ValueError:
            raise argparse.ArgumentTypeError("must be an int")
    return id_range


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("user", help="API server username")
    parser.add_argument("password", help="API server password")
    parser.add_argument(
        "-s", "--server", default="https://api.cacophony.org.nz", help="API server URL"
    )
    parser.add_argument(
        "--before",
        default=None,
        help="Proces recordings before this date",
    )
    parser.add_argument(
        "--after",
        default=None,
        help="Proces recordings before this date",
    )
    parser.add_argument(
        "--group-id",
        type=int,
        default=None,
        help="Reprocess all recordings under a group",
    )
    parser.add_argument(
        "--device-id",
        type=int,
        default=None,
        help="Reprocess all recordings under a device",
    )
    parser.add_argument(
        "-t",
        "--type",
        default="audio",
        help="Type of recording",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=None,
        help="Number of recordings to set to reprocessing",
    )
    parser.add_argument(
        "-i",
        "--id",
        dest="recording_id",
        type=recording_range,
        default=[],
        help="Specify a recording range start:end or comma separated list of recordings to reprocess id,id2,...",
    )

    # parser.add_argument(
    #     "-a",
    #     "--algorithm",
    #     dest="algorithm_id",
    #     type=int,
    #     default=None,
    #     help="Only reprocess recordings with an algorithm_id less than this",
    # )
    return parser.parse_args()


if __name__ == "__main__":
    main()
