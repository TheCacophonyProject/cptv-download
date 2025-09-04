#!/usr/bin/python3
import yaml
import os
import sys
import boto3
import datetime
import subprocess
import psycopg2
import socket
import argparse
from pathlib import Path
import logging
from dateutil.parser import parse as parse_date
import gzip
import io
import json
HOST_NAME = socket.gethostname()
CONFIG_FILE = "./psql-download.yaml"
DUMP_EXT = ".pgdump"


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--start-date',
        help='If specified, only files recorded on or after this date will be downloaded.')
    parser.add_argument(
        'bucket',
        help='s3 bucket name')
    parser.add_argument(
        'out_folder',
        help='Root folder to place downloaded files in.')
    args = parser.parse_args()
    return args




def connect_to_db():

    try:
        conn = psycopg2.connect(
            host="localhost",
            database="cacodb",
            user="postgres",
            password="postgres"
        )
        print("Connection to PostgreSQL successful!")

        # Perform database operations here
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")

    # finally:
    #     if 'conn' in locals() and conn:
    #         conn.close()
    #         print("Connection closed.")
    return None
def main():
    args = parse_args()
    download_dir = Path(args.out_folder)
    download_dir.mkdir(exist_ok=True)

    print("Running CPTV Download on cacodb")

    if not os.path.exists(CONFIG_FILE):
        print(f"failed to find config file '{CONFIG_FILE}'")
        sys.exit()

    with open(CONFIG_FILE, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)


    s3_config = config["s3_auth"]
    s3 = boto3.resource("s3", **s3_config)

    conn = connect_to_db()
    with open("taggedthermals.sql", 'r') as f:
        taggedthermals_sql = f.read()
    
    with open("tracks.sql", 'r') as f:
        tracks_sql = f.read()
    start_date = parse_date(args.start_date)
    end_date = start_date + datetime.timedelta(days=2)
    limit = 10
    offset = 0
    query_sql = taggedthermals_sql.format(start_date,end_date,limit,offset)

        # Example: Select data
    cur = conn.cursor()

    cur.execute(query_sql)
    rows = cur.fetchall()
    for row in rows:
        print(row)
        tracks_sql.format(row["id"])
        tracks_rows = cur.fetchall()
        for track_row in tracks_rows:
            get_track_data(s3,args.bucket,track_row["id"])
        break

def get_track_data(s3,bucket_name,track_id):
    obj = s3.Object(bucket_name, f"Track/{track_id}")
    response = obj.get()

    # Get the StreamingBody
    body = response['Body']

    # Decompress the gzipped data
    # Use io.BytesIO to treat the StreamingBody as a file-like object for gzip
    with gzip.GzipFile(fileobj=io.BytesIO(body.read())) as gz_file:
        unzipped_data_bytes = gz_file.read()
        print(data_s.decode("utf-8"))

    data_s = json.load(unzipped_data_bytes.decode("utf-8"))
    print("data is ",data_s)
# export const getTrackData = async (trackId: TrackId) => {
#   try {
#     const data = await openS3().getObject(`Track/${trackId}`);
#     const compressedData = await data.Body.transformToByteArray();
#     const uncompressed = await gunzip(compressedData);
#     return JSON.parse(uncompressed.toString("utf-8"));
#   } catch (e) {
#     return {};
#   }
if __name__ == "__main__":
    main()