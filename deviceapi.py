import os
import json
import requests
from urllib.parse import urljoin
from requests_toolbelt.multipart.encoder import MultipartEncoder

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

        return r.json().get('token')

    def uploadrecording(self, filename, jsonProps = None): 
        url = urljoin(self._baseurl, '/api/v1/recordings')
        print(filename)

        if (jsonProps == None):
            jsonProps = '{"type": "thermalRaw"}'
            print (' null props')

        with open(filename, 'rb') as thermalfile: 
            multipart_data = MultipartEncoder(
                fields={
                        # a file upload field
                        'file': ('file.py', thermalfile),
                        # plain text fields
                        'data': jsonProps 
                    }
                )
            headers={'Content-Type': multipart_data.content_type, 'Authorization': self._token}
            r = requests.post(url, data=multipart_data, headers=headers)


        if r.status_code == 400:
            messages = r.json()['messages']
            print ("request failed ({}): {}".format(r.status_code, messages))
        else:
            r.raise_for_status()



    

