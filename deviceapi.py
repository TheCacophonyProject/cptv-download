import json
import requests
from urllib.parse import urljoin
from requests_toolbelt.multipart.encoder import MultipartEncoder

class DeviceAPI:

    def __init__(self, baseurl, devicename='uploader', password='password'):
        self._baseurl = baseurl
        self._devicename = devicename
        self._token = self._get_jwt(password)
        self._auth_header = {'Authorization': self._token}

    def _get_jwt(self, password):
        url = urljoin(self._baseurl, "/authenticate_device")
        r = requests.post(url, data={
            'devicename': self._devicename,
            'password': password,
            })

        try: 
            r.raise_for_status()
        except:
            raise Exception("Could not log on as '" + self._devicename +  "'.  Please check device name and password")
            
        return r.json().get('token')
        

    def uploadrecording(self, filename, jsonProps = None): 
        url = urljoin(self._baseurl, '/api/v1/recordings')

        if (jsonProps is None):
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


        if r.status_code == 200:
            print('Successful upload of ', filename)
        elif r.status_code == 400:
            messages = r.json()['messages']
            print ("request failed ({}): {}".format(r.status_code, messages))
        else:
            r.raise_for_status()



    

