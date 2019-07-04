#!/usr/bin/python

import argparse

from api import API


def reprocess(args):
    """ Reprocesses all specified recording from specified server """

    api = API(args.server, args.user, args.password)

    print(f"Querying server {args.server}")
    print(f"Limit is {args.limit}")
    if args.recording_id:
        print(f"Recording id is {args.recording_id}")
        api.reprocess([args.recording_id])
        return

    where = {
        "additionalMetadata.algorithm": {"$eq": None},
        "type": "thermalRaw",
        "processingState": {"$ne": "FINISHED"},
    }

    if args.lower_id:
        id_where = where.get("id", {})
        id_where["$gte"] = args.lower_id
        where["id"] = id_where
    if args.upper_id:
        id_where = where.get("id", {})
        id_where["$lte"] = args.upper_id
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
        type=int,
        default=None,
        help="Specify the recording id to download",
    )
    parser.add_argument(
        "-upperid",
        dest="upper_id",
        type=int,
        default=None,
        help="Specify the recording upper id e.g Recording.id <= upper_id",
    )

    parser.add_argument(
        "-lowerid",
        dest="lower_id",
        type=int,
        default=None,
        help="Specify the recording lower id value e.g Recording.id >= lower_id",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
