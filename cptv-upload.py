import argparse
import glob
import os
import json
from cacophonyapi.user import UserAPI as API

from pathlib import Path


def upload_recording(api, file, args):
    print("uploading", file)
    if file.suffix == ".cptv":
        api.upload_recording(args.groupname, args.devicename, args.filename)
    elif file.suffix in [".m4a", ".mp3", ".wav"]:
        meta_f = file.with_suffix(".txt")
        if not meta_f.exists():
            print("Require audio meta data to get rec data time")
        else:
            with open(meta_f, "r") as f:
                meta = json.load(f)
            rec_date = meta["recordingDateTime"]
        props = {"type": "audio", "recordingDateTime": rec_date}
        print("props", props)
        api.upload_recording(
            args.groupname, args.devicename, args.filename, props=props
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "server_url", help="Server (base) url to send the CPTV files to"
    )
    parser.add_argument("username", help="Username to upload as")
    parser.add_argument("password", help="Password to authenticate with")
    parser.add_argument("groupname", help="Group name to upload on behalf of")
    parser.add_argument("devicename", help="Device to upload on behalf of")
    parser.add_argument(
        "filename",
        help="File to upload. If it is a directory will upload all cptv files in that dir",
    )

    args = parser.parse_args()
    print(args.server_url, args.username, args.password)
    api = API(args.server_url, args.username, args.password)
    base_dir = Path(args.filename)
    if base_dir.is_dir():
        for file in base_dir.iterdir():
            upload_recording(api, file, args)
            # if file.suffix == ".cptv":
            #     filepath = os.path.join(args.filename, file)
            #     api.upload_recording(args.groupname, args.devicename, filepath)
            # elif file.suffix in [".m4a", ".mp3", ".wav"]:
            #     Path(args.filename)
            #     filepath = os.path.join(args.filename, file)
            #     api.upload_recording(args.groupname, args.devicename, filepath)
    else:
        upload_recording(api, base_dir, args)


if __name__ == "__main__":
    main()
