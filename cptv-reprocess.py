#!/usr/bin/python

import argparse

from api import API


def reprocess(server_url, user, password, recording_id, limit):
    """ Reprocesses all specified recording from specified server """

    api = API(server_url, user, password)

    print(f"Querying server {server_url}")
    print(f"Limit is {limit}")
    if recording_id:
        print(f"Recording id is {recording_id}")
        api.reprocess([recording_id])
        return

    where = {
        "additionalMetadata.algorithm": {"$eq": None},
        "type": "thermalRaw",
        "processingState": {"$ne": "FINISHED"},
    }

    count = api.query(where=where, limit=limit, raw_json=True)["count"]
    if count:
        print(f"Still reprocessing {count} records")
        return

    where["processingState"] = "FINISHED"
    rows = api.query(where=where, limit=limit)
    recording_ids = [row["id"] for row in rows]
    print(f"Reprocessing recording ids: {recording_ids}")
    api.reprocess(recording_ids)


def main():
    args = parse_args()
    reprocess(args.server, args.user, args.password, args.recording_id, args.limit)


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
        default=None,
        help="Specify the recording id to download",
    )

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
