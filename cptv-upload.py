import argparse
import glob
import os

from api import API


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "server_url", help="Server (base) url to send the CPTV files to"
    )
    parser.add_argument("username", help="Username to upload as")
    parser.add_argument("password", help="Password to authenticate with")
    parser.add_argument("groupname", help="Group name to upload on behalf of")
    parser.add_argument("devicename", help="Device to upload on behalf of")
    parser.add_argument("--filename", help="File to upload")
    parser.add_argument("--filedir", help="Will upload all cptv files in this dir")

    args = parser.parse_args()

    api = API(args.server_url, args.username, args.password)
    if args.filename != None:
        print("uploading just one recording")
        api.upload_recording(args.groupname, args.devicename, args.filename)
    elif args.filedir != None:
        print("uploading multiple files")
        for file in os.listdir(args.filedir):
            if file.endswith(".cptv"):
                filepath = os.path.join(args.filedir, file)
                print(filepath)
                api.upload_recording(args.groupname, args.devicename, filepath)
    else:
        print("filename or filedor is required")

if __name__ == "__main__":
    main()
