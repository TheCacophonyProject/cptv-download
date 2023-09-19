import argparse
import glob
import os
import json
from cacophonyapi.user import UserAPI as API

from pathlib import Path
import datetime


def upload_recording(api, file_name, args):
    print("uploading", file_name)
    if file_name.suffix == ".cptv":
        file_name = Path(file_name)
        try:
            rec_date = datetime.datetime.strptime(file_name.stem, "%Y%m%d-%H%M%S")
        except Exception as ex:
            print("Coult not parse date ", file_name.stem, ex)
            rec_date = None
        props = {
            "type": "thermalRaw",
        }
        if rec_date is not None:
            props["recordingDateTime"] = rec_date.isoformat()
        api.upload_recording(
            args.groupname, args.devicename, str(file_name), props=props
        )
    elif file_name.suffix in [".m4a", ".mp3", ".wav"]:
        meta_f = file_name.with_suffix(".txt")
        if not meta_f.exists():
            print("Require audio meta data to get rec data time")
            rec_date = file_name.name[:10]
            rec_date = datetime.datetime.strptime(rec_date, "%Y-%m-%d")
            rec_date = rec_date.isoformat()
        else:
            with open(meta_f, "r") as f:
                meta = json.load(f)
            rec_date = meta["recordingDateTime"]
        props = {
            "type": "audio",
            "recordingDateTime": rec_date,
            "additionalMetadata": {"file": file_name.name},
        }
        api.upload_recording(
            args.groupname, args.devicename, str(file_name), props=props
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
    api = API(args.server_url, args.username, args.password)
    base_dir = Path(args.filename)
    if base_dir.is_dir():
        for file_name in base_dir.rglob("*"):
            if file_name.is_file():
                upload_recording(api, file_name, args)
    else:
        upload_recording(api, base_dir, args)


if __name__ == "__main__":
    main()
