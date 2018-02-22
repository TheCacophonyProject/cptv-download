from deviceapi import DeviceAPI

import argparse

import os

import json

class CPTVUploader:
    def __init__(self):
        self.url = None        
        self.source_dir = None
        self.device_name = None
        self.device_password = None

    def process(self):
        print('Uploading to  ', self.url)
        api = DeviceAPI(self.url, devicename = self.device_name, password = self.device_password)

        files = self._find_files_to_upload()
        for file in files:
            self._uploadfile(api, file)

    def _uploadfile(self, api, filename):
        props = self._readPropertiesFromFile(filename)

        api.uploadrecording(filename, props)


    def _uploader(self, queue, api):
        while True:
            
            filename = queue.get()

            if filename is None:
                break

            try:
                _uploadfile(api, filename)

            finally:
                queue.task_done()

    def _find_files_to_upload(self):
        cptvfiles = list()

        for root, dirs, files in os.walk(self.source_dir):
            for file in files:
                if file.lower().endswith(".cptv"):
                    cptvfiles.append(os.path.join(root, file))
        
        return cptvfiles

    def _readPropertiesFromFile(self, filename): 
        basefile = os.path.splitext(filename)[0]
        jsonfilename = basefile + '.txt'

        if (os.path.isfile(jsonfilename)):
            with open(jsonfilename, 'r') as propsfile: 

                oldprops = json.load(propsfile)

                # List of properties to transfer.   Many such as Id, we don't want to transfer. 
                propTypesToTransfer = ("batteryCharging", "additionalMetadata", "comment", "location", 
                            "fileSize", "batteryLevel", "duration", "rawFileSize", "airplaneModeOn", 
                            "version", "recordingDateTime", "fileMimeType", "type")

                newProps = dict()

                for key in propTypesToTransfer: 
                    if (key in oldprops and oldprops[key] is not None):
                        newProps[key] = oldprops[key]

                newProps["comment"] = 'uploaded from "' + filename + '"'
                
                # Tags can't be imported at the moment - maybe because there is no tagger Id. 

                # if ('Tags' in oldprops and oldprops['Tags'] is not None):
                #   tags = oldprops['Tags']
                #     tagPropTypesToTransfer = ("confidence", "number", "sex", "updatedAt", "startTime", 
                #         "age","automatic", "createdAt", "trapType", "event", "animal", "duration")
                #     newTags = list()

                #     for tag in tags:
                #         newTagProps = dict()
                #         for key in tagPropTypesToTransfer: 
                #             if (key in tag and tag[key] is not None):
                #                 newTagProps[key] = tag[key]
                #         newTags += newTagProps                    
                #     newProps['Tags'] = newTagProps

                return json.dumps(newProps)
        
        return None


def main(): 
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--password',
        dest='device_password',
        default='password',
        help='Password for the device')

    parser.add_argument('server_url',  help='Server (base) url to send the CPTV files to')
    
    parser.add_argument('source_dir',  help='Root folder where files for upload are stored')
    
    parser.add_argument('device_name',  help='Device identifier to upload recordings under')

    uploader = CPTVUploader()

    args = parser.parse_args()

    uploader.url = args.server_url
    uploader.source_dir = args.source_dir
    uploader.device_name = args.device_name
    uploader.device_password = args.device_password

    uploader.process()



if __name__ == '__main__':
    main()