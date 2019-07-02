#!/usr/bin/python

import argparse

from api import API


class CPTVReprocessor:
    def __init__(self, server_url, user, password, id, limit):
        self.user = user
        self.password = password
        self.url = server_url
        self.recording_id = id
        self.limit = limit

    def reprocess(self):
        """ Reprocesses all specified recording from specified server """

        api = API(self.url, self.user, self.password)

        print(f"Querying server {self.url}")
        print(f"Limit is {self.limit}")
        if self.recording_id:
            print(f"Recording id is {self.recording_id}")
            api.reprocess([self.recording_id])
            return

        where = {}
        # algorithm was only added when trackbased tagging was introduced
        where["additionalMetadata.algorithm"] = {"$eq": None}
        where["type"] = "video"
        count = api.query(where=where, limit=self.limit, raw_json=True)["count"]
        if count:
            print(f"Still reprocessing {count} records")
            return

        where["processingState"] = "FINISHED"
        rows = api.query(where=where, limit=self.limit)
        recording_ids = [row["id"] for row in rows]
        print(f"Reprocessing recording ids: {recording_ids}")
        api.reprocess(recording_ids)


def main():
    args = parse_args()
    reprocessor = CPTVReprocessor(
        args.server, args.user, args.password, args.recording_id, args.limit
    )
    reprocessor.reprocess()


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("user", help="API server username")
    parser.add_argument("password", help="API server password")
    parser.add_argument(
        "-s",
        "--server",
        default=["https://api.cacophony.org.nz"],
        help="CPTV file server URL",
    )
    parser.add_argument(
        "-l",
        "--limit",
        default=None,
        help="Number of recordings to set to reprocessing",
    )
    parser.add_argument(
        "-id",
        dest="recording_id",
        default=None,
        help="Specify the recording id to download",
    )
    # yapf: enable

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
