import json
import requests
from urllib.parse import urljoin


class DeviceAPI:

    def __init__(self, baseurl, devicename='dev_brent01', password='password'):
        self._baseurl = baseurl
        self.devicename = devicename
        self._token = self._get_jwt(password)
        self._auth_header = {'Authorization': self._token}

    def _get_jwt(self, password):
        url = urljoin(self._baseurl, "/authenticate_device")
        r = requests.post(url, data={
            'devicename': self.devicename,
            'password': password,
            })
        print(r.json().get('messages'))

        r.raise_for_status()


        print(r.json().get('token'))
        
        return r.json().get('token')

