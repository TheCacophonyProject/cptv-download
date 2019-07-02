#!/usr/bin/python

import argparse
import json
import requests
from urllib.parse import urljoin


class APIBase:
    def __init__(self, baseurl, loginname, password, logintype):
        self._baseurl = baseurl
        self._loginname = loginname
        self._token = self._get_jwt(password, logintype)
        self._auth_header = {"Authorization": self._token}

    def _get_jwt(self, password, logintype):
        nameProp = logintype + "name"

        url = urljoin(self._baseurl, "/authenticate_" + logintype)
        r = requests.post(url, data={nameProp: self._loginname, "password": password})

        if r.status_code == 200:
            return r.json().get("token")
        elif r.status_code == 422:
            raise ValueError(
                "Could not log on as '{}'.  Please check {} name.".format(
                    self._loginname, logintype
                )
            )
        elif r.status_code == 401:
            raise ValueError(
                "Could not log on as '{}'.  Please check password.".format(
                    self._loginname
                )
            )
        else:
            r.raise_for_status()

    def _check_response(self, r):
        if r.status_code == 400:
            messages = r.json().get("messages", "")
            raise IOError("request failed ({}): {}".format(r.status_code, messages))
        r.raise_for_status()
        return r.json()


class API(APIBase):
    def __init__(self, baseurl, username, password):
        super().__init__(baseurl, username, password, "user")

    def reprocess(self, recordings):
        url = urljoin(self._baseurl, "/api/v1/reprocess")
        r = requests.post(
            url, headers=self._auth_header, data={"recordings": json.dumps(recordings)}
        )
        if r.status_code == 200:
            return r.json()
        if r.status_code in (400, 422):
            messages = r.json()["message"]
            raise IOError("request failed ({}): {}".format(r.status_code, messages))
        return r.raise_for_status()

    def query(
        self,
        type_=None,
        startDate=None,
        endDate=None,
        min_secs=None,
        limit=100,
        offset=0,
        tagmode=None,
        tags=None,
        devices=None,
        where=None,
    ):
        url = urljoin(self._baseurl, "/api/v1/recordings")
        if where is None:
            where = {}
        if type_ is not None:
            where["type"] = type_
        if min_secs is not None:
            where["duration"] = {"$gte": min_secs}
        if startDate is not None:
            where["recordingDateTime"] = {"$gte": startDate.isoformat()}
        if endDate is not None:
            where.setdefault("recordingDateTime", {})["$lte"] = endDate.isoformat()
        if devices is not None:
            where["DeviceId"] = devices
        params = {"where": json.dumps(where)}

        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if tagmode is not None:
            params["tagMode"] = tagmode
        if tags is not None:
            params["tags"] = json.dumps(tags)

        r = requests.get(url, params=params, headers=self._auth_header)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (400, 422):
            messages = r.json()["message"]
            raise IOError("request failed ({}): {}".format(r.status_code, messages))
        return r.raise_for_status()


class Reprocessor:
    def __init__(self, server_url, user, password, id, limit):
        self.user = user
        self.password = password
        self.url = server_url
        self.recording_id = id
        self.limit = limit

    def reprocess(self):
        """ Downloads all requested files from specified server """

        api = API(self.url, self.user, self.password)

        if self.recording_id:
            print(f"reprocessing {self.recording_id}")
            api.reprocess([self.recording_id])
            return

        where = {}
        # algorithm was only added when trackbased tagging was introduced
        where["additionalMetadata.algorithm"] = {"$eq": None}
        count = api.query(where=where, limit=self.limit)["count"]
        if count:
            print(f"Still reprocessing {count} records")
            return

        where["processingState"] = "FINISHED"
        # where["additionalMetadata.algorithm"] = {"$eq": None}
        rows = api.query(where=where, limit=self.limit)["rows"]
        recording_ids = [row["id"] for row in rows]
        print(f"reprocessing {recording_ids}")
        api.reprocess(recording_ids)


def main():
    args = parse_args()
    reprocessor = Reprocessor(
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
