import argparse

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
    parser.add_argument("filename", help="File to upload")
    args = parser.parse_args()

    api = API(args.server_url, args.username, args.password)
    api.upload_recording(args.groupname, args.devicename, args.filename)


if __name__ == "__main__":
    main()
