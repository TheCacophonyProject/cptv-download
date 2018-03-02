from apibase import APIBase

import json
import requests
from urllib.parse import urljoin


class API(APIBase):

    def __init__(self, baseurl, username, password):
        super().__init__(baseurl, username, password, 'user')

    def query(self, startDate=None, endDate=None, min_secs=5, limit=100, offset=0, tagmode=None, tags=None):
        url = urljoin(self._baseurl, '/api/v1/recordings')

        where = [{"duration": {"$gte": min_secs}}]
        if startDate is not None:
            where.append({'recordingDateTime': {'$gte': startDate.isoformat()}})
        if endDate is not None:
            where.append({'recordingDateTime': {'$lte': endDate.isoformat()}})

        params = {'where': json.dumps(where)}
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
        if tagmode is not None:
            params['tagMode'] = tagmode
        if tags is not None:
            params['tags'] = json.dumps(tags)

        r = requests.get(url, params=params, headers=self._auth_header)
        if r.status_code == 200:
            return r.json()['rows']
        elif r.status_code == 400:
            messages = r.json()['messages']
            raise IOError("request failed ({}): {}".format(r.status_code, messages))
        else:
            r.raise_for_status()

    def download_cptv(self, id):
        return self._download_recording(id, 'downloadRawJWT')

    def download_mp4(self, id):
        return self._download_recording(id, 'downloadFileJWT')

    def _download_recording(self, id, jwt_key):
        url = urljoin(self._baseurl, '/api/v1/recordings/{}'.format(id))
        r = requests.get(url, headers=self._auth_header)
        d = self._check_response(r)
        return self._download_signed(d[jwt_key])

    def _download_signed(self, token):
        print(token)
        r = requests.get(
            urljoin(self._baseurl, '/api/v1/signedUrl'),
            params={'jwt': token},
            stream=True)
        r.raise_for_status()
        yield from r.iter_content(chunk_size=4096)
