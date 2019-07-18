#!/usr/bin/python

import argparse
from datetime import datetime, timedelta

from api import API


def reprocess(args):
    """ Reprocesses all specified recording from specified server """

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

    hour_ago = datetime.now() - timedelta(hours=1)
    where = {
        "type": "thermalRaw",
        "processingState": {"$ne": "FINISHED"},
        "processingStartTime": {"$or": {"$gt": hour_ago.isoformat(), "$eq": None}},
    }
    if args.algorithm_id:
        where["$or"] = [
            {"additionalMetadata.algorithm": {"$eq": None}},
            {"additionalMetadata.algorithm": {"$lt": args.algorithm_id}},
        ]
    else:
        where["additionalMetadata.algorithm"] = {"$eq": None}

    if len(args.recording_id) == 2:
        if args.recording_id[0]:
            where.setdefault("id", {})["$gte"] = int(args.recording_id[0])
        if args.recording_id[1]:
            where.setdefault("id", {})["$lte"] = int(args.recording_id[1])

    q = api.query(where=where, limit=args.limit, raw_json=True)
    count = q["count"]
    if count:
        print(f"Still reprocessing {count} records")
        print([row["id"] for row in q["rows"]])
        return

    where["processingState"] = "FINISHED"
    rows = api.query(where=where, limit=args.limit)
    recording_ids = [row["id"] for row in rows]
    print(f"Reprocessing recording ids: {recording_ids}")
    api.reprocess(recording_ids)


def main():
    args = parse_args()
    reprocess(args)


def recording_range(range_s):
    id_range = range_s.split(":")
    if len(id_range) > 2:
        raise argparse.ArgumentTypeError(
            "multiple ':', exepected format of start:end or id,id2,... "
        )
    elif len(id_range) == 2:
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
        "-s",
        "--server",
        default=["https://api.cacophony.org.nz"],
        help="API server URL",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=100,
        help="Number of recordings to set to reprocessing",
    )
    parser.add_argument(
        "-id",
        dest="recording_id",
        type=recording_range,
        default=[],
        help="Specify a recording range start:end or comma seperated list of recordings to reprocess id,id2,...",
    )

    parser.add_argument(
        "-a",
        "--algorithm",
        dest="algorithm_id",
        type=int,
        default=None,
        help="Only reprocess recordings with an algorithm_id less than this",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
