import json
import requests
from urllib.parse import urljoin


class API:

    def __init__(self, baseurl, username, password):
        self._baseurl = baseurl
        self._username = username
        self._token = self._get_jwt(password)
        self._auth_header = {'Authorization': self._token}

    def _get_jwt(self, password):
        url = urljoin(self._baseurl, "/authenticate_user")
        r = requests.post(url, data={
            'username': self._username,
            'password': password,
            })

        if r.status_code == 200:
            return r.json().get('token')
        elif r.status_code == 422:
            raise ValueError("Could not log on as '{}'.  Please check user name.".format(self._username))
        elif r.status_code == 401:
            raise ValueError("Could not log on as '{}'.  Please check password.".format(self._username))
        else:
            r.raise_for_status()


        

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
        r = requests.get(
            urljoin(self._baseurl, '/api/v1/signedUrl'),
            headers={'Authorization': 'JWT ' + token},
            stream=True)
        r.raise_for_status()
        yield from r.iter_content(chunk_size=4096)

    def _check_response(self, r):
        if r.status_code == 400:
            messages = r.json().get('messages', '')
            raise IOError("request failed ({}): {}".format(r.status_code, messages))
        r.raise_for_status()
        return r.json()
