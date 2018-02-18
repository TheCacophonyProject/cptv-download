from deviceapi import DeviceAPI

import argparse
from pool import Pool

import os

import json

class CPTVUploader:
    def __init__(self):
        self.url = None
        self.source_dir = None

    def process(self):
        print('url is ', self.url)
        api = DeviceAPI(self.url)

        files = self._find_files_to_upload()
        for file in files:
            self._uploadfile(api, file)

        # pool = Pool(4, self._uploader, api)
        # for file in files:
        #     pool.put(file)
        # pool.stop()


    def _uploadfile(self, api, filename):
        props = self._readPropertiesFromFile(filename)

        print('props to transfer ')
        print(props)

        api.uploadrecording(filename, props)


    def _uploader(self, queue, api):
        while True:
            
            filename = queue.get()

            if filename is None:
                print('Closing thread')
                break

            try:
                _uploadfile(api, filename)

            finally:
                queue.task_done()

    def _find_files_to_upload(self):
        cptvfiles = list()

        print('testing dir', self.source_dir)
        for root, dirs, files in os.walk(self.source_dir):
            for file in files:
                if file.lower().endswith(".cptv"):
                    cptvfiles.append(os.path.join(root, file))
        
        return cptvfiles

    def _readPropertiesFromFile(self, filename): 
        basefile = os.path.splitext(filename)[0]
        jsonfilename = basefile + '.txt'

        print(jsonfilename)

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
                
                # Tags can be imported at the moment - maybe because there is no tagger Id. 
                # tags = oldprops['Tags']

                # if (tags is not None):
                #     tagPropTypesToTransfer = ("confidence", "number", "sex", "updatedAt", "startTime", 
                #         "age","automatic", "createdAt", "trapType", "event", "animal", "duration")
                #     newTags = list()

                #     for tag in tags:
                #         newTagProps = dict()
                #         for key in tagPropTypesToTransfer: 
                #             if (tag[key] is not None):
                #                 newTagProps[key] = tag[key]

                #         newTags += newTagProps
                    
                #     newProps['Tags'] = newTagProps

                return json.dumps(newProps)
        
        return None


def main(): 
    parser = argparse.ArgumentParser()

    parser.add_argument('server_url',  help='Server (base) url to send the CPTV files to')
    
    parser.add_argument('source_dir',  help='Root folder where files for upload are stored')
    
    uploader = CPTVUploader()

    args = parser.parse_args()

    uploader.url = args.server_url
    uploader.source_dir = args.source_dir

    uploader.process()



if __name__ == '__main__':
    main()