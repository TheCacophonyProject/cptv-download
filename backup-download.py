#!/usr/bin/python3
import yaml
import os
import sys
import boto3
import datetime
import subprocess
from influxdb import InfluxDBClient
import socket
import argparse
from pathlib import Path
import logging

HOST_NAME = socket.gethostname()
CONFIG_FILE = "./config.yaml"
DUMP_EXT = ".pgdump"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("out_folder", help="Root folder to place downloaded files in.")
    args = parser.parse_args()
    return args


# probably better off running in bash as will take ages
def restore_backup(backup_file):
    cmd = f"sudo -u postgres pg_restore -d cacodb {backup_file}"


# export const getTrackData = async (trackId: TrackId) => {
#   try {
#     const data = await openS3().getObject(`Track/${trackId}`);
#     const compressedData = await data.Body.transformToByteArray();
#     const uncompressed = await gunzip(compressedData);
#     return JSON.parse(uncompressed.toString("utf-8"));
#   } catch (e) {
#     return {};
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
    bucket_name = config["bucket"]
    s3_config = config["s3_auth"]
    s3 = boto3.resource("s3", **s3_config)
    bucket = s3.Bucket(bucket_name)

    latest_file = None
    latest_modified = None
    for obj in bucket.objects.all():
        if latest_file is None or obj.last_modified > latest_modified:
            latest_file = obj.key
            latest_modified = obj.last_modified
    print(f"The latest file is: {latest_file}")
    bucket.download_file(latest_file, download_dir)


if __name__ == "__main__":
    main()
