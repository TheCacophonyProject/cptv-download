#!/usr/bin/python

import argparse

from api import API


def reprocess(args):
    """ Reprocesses all specified recording from specified server """

    api = API(args.server, args.user, args.password)

    print(f"Querying server {args.server}")
    print(f"Limit is {args.limit}")
    if len(args.recording_id) == 1:
        recordings = args.recording_id[0].split(",")
        print(f"Reprocessing {recordings}")
        api.reprocess(recordings)
        return

    where = {
        "additionalMetadata.algorithm": {"$eq": None},
        "type": "thermalRaw",
        "processingState": {"$ne": "FINISHED"},
    }

    if len(args.recording_id) == 2:
        if args.recording_id[0]:
            id_where = where.get("id", {})
            id_where["$gte"] = int(args.recording_id[0])
            where["id"] = id_where
        if args.recording_id[1]:
            id_where = where.get("id", {})
            id_where["$lte"] = int(args.recording_id[1])
            where["id"] = id_where

    count = api.query(where=where, limit=args.limit, raw_json=True)["count"]
    if count:
        print(f"Still reprocessing {count} records")
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
    return range_s.split(":")


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("user", help="API server username")
    parser.add_argument("password", help="API server password")
    parser.add_argument("-s", "--server", default=["https://api.cacophony.org.nz"], help="API server URL")
    parser.add_argument(
        "-l", "--limit", type=int, default=100, help="Number of recordings to set to reprocessing"
    )
    parser.add_argument(
        "-id",
        dest="recording_id",
        type=recording_range,
        default=None,
        help="Specify a recording range start:end or comma seperated list of recordings to reprocess id,id2,...",
    )

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
