from apibase import APIBase

import json
import requests
from requests_toolbelt import MultipartEncoder
from urllib.parse import urljoin


class API(APIBase):
    def __init__(self, baseurl, username, password):
        super().__init__(baseurl, username, password, "user")

    def get(self, recording_id):
        url = urljoin(self._baseurl, "/api/v1/recordings/" + recording_id)
        r = requests.get(url, headers=self._auth_header)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (400, 422):
            messages = r.json()["message"]
            raise IOError("request failed ({}): {}".format(r.status_code, messages))
        return r.raise_for_status()

    def get_tracks(self, recording_id):
        url = urljoin(
            self._baseurl, "/api/v1/recordings/{}/tracks".format(recording_id)
        )
        r = requests.get(url, headers=self._auth_header)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (400, 422):
            messages = r.json()["message"]
            raise IOError("request failed ({}): {}".format(r.status_code, messages))
        return r.raise_for_status()

    def reprocess(self, recordings: []):
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
        raw_json=False,
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
            if raw_json:
                return r.json()
            else:
                return r.json()["rows"]
        if r.status_code in (400, 422):
            messages = r.json()["message"]
            raise IOError("request failed ({}): {}".format(r.status_code, messages))
        return r.raise_for_status()

    def download(self, recording_id):
        return self._download_recording(recording_id, "downloadFileJWT")

    def download_raw(self, recording_id):
        return self._download_recording(recording_id, "downloadRawJWT")

    def _download_recording(self, recording_id, jwt_key):
        url = urljoin(self._baseurl, "/api/v1/recordings/{}".format(recording_id))
        r = requests.get(url, headers=self._auth_header)
        d = self._check_response(r)
        return self._download_signed(d[jwt_key])

    def _download_signed(self, token):
        r = requests.get(
            urljoin(self._baseurl, "/api/v1/signedUrl"),
            params={"jwt": token},
            stream=True,
        )
        r.raise_for_status()
        yield from r.iter_content(chunk_size=4096)

    def upload_recording(self, groupname, devicename, filename, props=None):
        """Upload a recording on behalf of a device.
        """
        url = urljoin(
            self._baseurl,
            "/api/v1/recordings/device/{}/group/{}".format(devicename, groupname),
        )

        if not props:
            if filename.endswith(".cptv"):
                props = {"type": "thermalRaw"}
            elif filename.endswith(".mp3"):
                props = {"type": "audio"}
            else:
                raise ValueError("not sure how to handle this file type")

        with open(filename, "rb") as f:
            multipart_data = MultipartEncoder(
                fields={"file": ("file.dat", f), "data": json.dumps(props)}
            )
            headers = {
                "Content-Type": multipart_data.content_type,
                "Authorization": self._token,
            }
            r = requests.post(url, data=multipart_data, headers=headers)

        self._check_response(r)
        return r.json()
