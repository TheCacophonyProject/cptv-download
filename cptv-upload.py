from deviceapi import DeviceAPI


class CPTVUploader:
    def __init__(self):
        self.url = 'http://10.0.2.15:1080'

    def process(self):
        api = DeviceAPI(self.url)


def main(): 
    uploader = CPTVUploader()

    uploader.process()


if __name__ == '__main__':
    main()