#!/usr/bin/python3
import yaml
import os
import sys
import boto3
import socket
import argparse
from pathlib import Path

HOST_NAME = socket.gethostname()
CONFIG_FILE = "./config.yaml"
DUMP_EXT = ".pgdump"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("out_folder", help="Root folder to place downloaded files in.")
    args = parser.parse_args()
    return args


# # probably better off running in bash as will take ages
# def restore_backup(backup_file):
#     cmd = f"sudo -u postgres pg_restore --clean -d cacodb {backup_file}"


#   }
def main():
    args = parse_args()
    download_dir = Path(args.out_folder)
    download_dir.mkdir(exist_ok=True)

    print("Running DB backup")

    if not os.path.exists(CONFIG_FILE):
        print(f"failed to find config file '{CONFIG_FILE}'")
        sys.exit()

    with open(CONFIG_FILE, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    s3_config = config["s3_archive_auth"]
    bucket_name = s3_config["db_bucket"]
    del s3_config["db_bucket"]
    del s3_config["bucket"]

    s3 = boto3.resource("s3", **s3_config)
    bucket = s3.Bucket(bucket_name)

    latest_file = None
    latest_modified = None
    for obj in bucket.objects.all():
        if latest_file is None or obj.last_modified > latest_modified:
            latest_file = obj.key
            latest_modified = obj.last_modified
    print(f"The latest file is: {latest_file}")
    s3_file = Path(latest_file)
    print(s3_file.name)
    save_file = download_dir / s3_file.name
    if save_file.exists():
        print("DB file already exists ", save_file)
    else:
        bucket.download_file(latest_file, save_file)
        print(f'Downloaded too {save_file} linking to {download_dir / "latest.pgdump"}')
        link_f = download_dir / "latest.pgdump"
        os.symlink(save_file, link_f)

    print(
        f"Restore with sudo -u postgres pg_restore --clean -d cacodb {download_dir/'latest.pgdump'}"
    )


if __name__ == "__main__":
    main()
