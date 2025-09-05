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
from psycopg2.extras import RealDictCursor

HOST_NAME = socket.gethostname()
CONFIG_FILE = "./config.yaml"
DUMP_EXT = ".pgdump"


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--start-date",
        help="If specified, only files recorded on or after this date will be downloaded.",
    )
    parser.add_argument("out_folder", help="Root folder to place downloaded files in.")
    args = parser.parse_args()
    return args


def connect_to_db():

    try:
        conn = psycopg2.connect(
            host="localhost", database="cacodb", user="postgres", password="postgres"
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
    bucket_name = config["bucket"]

    s3 = boto3.resource("s3", **s3_config)

    conn = connect_to_db()
    with open("tagged_recordings.sql", "r") as f:
        taggedthermals_sql = f.read()

    with open("tracks_for_recordings.sql", "r") as f:
        tracks_sql = f.read()


    start_date = parse_date(args.start_date)
    end_date = start_date + datetime.timedelta(days=2)
    limit = 10
    offset = 0
    query_sql = taggedthermals_sql.format(start_date, end_date, limit, offset)
    print(query_sql)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query_sql)
    rec_rows = cur.fetchall()

    recs = {}
    for rec_row in rec_rows:
        print("Rec ",rec_row["id"])
        if rec_row["id"] in recs:
            print("add to existing ", rec_row)
            tag = map_recording_tag(rec_row)
            print("Adding tag to ",rec_row["id"],tag)
            recs[rec_row["id"]]["tags"].append(tag)
            continue        

        # save any recordings as we are now on new rec
        for rec in recs.values():
            out_file = download_dir / f"{rec["id"]}.txt"

            print("Writing out to ",out_file)
            with out_file.open("w") as f:
                json.dump(rec,f, indent=4, cls=CustomJSONEncoder)
            return

        recs = {}
        track_q = tracks_sql.format(rec_row["id"])
        cur.execute(track_q)
        tracks_rows = cur.fetchall()
        
        tracks = {}
        for track_row in tracks_rows:
            track_id = track_row["id"]
            if track_id in tracks:
                tag = map_track_tag(track_row)
                tracks[track_id]["tags"].append(tag)
            else:
                track_data = get_track_data(s3, bucket_name, track_row["id"])
                track_row["data"]= track_data
                mapped_track = map_track(track_row)
                tracks[track_id] = mapped_track
                
        recording = map_recording(rec_row)
        rec_row["tracks"]= list(tracks.items())
        recs[recording["id"]] = recording
        print("Added ", recording)

def get_track_data(s3, bucket_name, track_id):
    obj = s3.Object(bucket_name, f"Track/{track_id}")
    response = obj.get()

    # Get the StreamingBody
    body = response["Body"]

    # Decompress the gzipped data
    # Use io.BytesIO to treat the StreamingBody as a file-like object for gzip
    with gzip.GzipFile(fileobj=io.BytesIO(body.read())) as gz_file:
        unzipped_data_bytes = gz_file.read()
    data_s = json.loads(unzipped_data_bytes.decode("utf-8"))

    return data_s


def map_track_tag(track_tag):
    track_tag_base = {
        "confidence": track_tag["TrackTags.confidence"],
        "id": track_tag["TrackTags.id"],
        "automatic": track_tag["TrackTags.automatic"],
        "trackId": track_tag["TrackTags.TrackId"],
        "what": track_tag["TrackTags.what"],
        "path": track_tag["TrackTags.path"],
        "model": track_tag["TrackTags.model"],
    }
    
    if (track_tag_base["automatic"]):
        return track_tag_base
    else:
        track_tag_base["userId"] = track_tag["TrackTags.UserId"]
        track_tag_base["userName"] = track_tag["TrackTags.User.userName"]
        return track_tag_base
        
def map_track(track):
    t = {
        "id": track["id"],
        "start": track["startSeconds"],
        "end": track["endSeconds"],
        "filtered":track["filtered"],
    }
    if track.get("tracking_score") is not None:
        t["tracking_score"] = track["tracking_score"];
    if track.get("minFreqHz") is not None:
        t["minFreq"] = track["minFreqHz"];
    if track.get("maxFreqHz") is not None:
        t["maxFreqHz"] = track["maxFreqHz"];
    
    positions = []
    for position in track["data"]["positions"]:
        positions.append(map_position(position))

    t["positions"] = positions
    track_tag = map_track_tag(track)  
    t["tags"] = [track_tag]   
    return t

def map_position(position):
    if isinstance(position,list):
        return {
        "x": position[1][0],
        "y": position[1][1],
        "width": position[1][2] - position[1][0],
        "height": position[1][3] - position[1][1],
        "frameTime": position[0],
        }
    return {
      "x": position["x"],
      "y": position["y"],
      "width": position["width"],
      "height": position["height"],
      "order": position["frame_number"] if "frame_number" else position["order"],
      "mass": position["mass"],
      "blank": position["blank"],
    };

def map_recording(recording):
    new_rec = {
        "id": recording["id"],
        "deviceId": recording["DeviceId"],
        "duration": recording["duration"],
        "location": recording["location"],
        "deviceName": recording["Device.deviceName"],
        "groupId": recording["Group.id"],
        "groupName": recording["Group.groupName"],
        "processing": recording["processing"],
        "processingState": recording["processingState"],
        "recordingDateTime": recording["recordingDateTime"],
        "stationName": recording["Station.name"],
        "type": recording["type"],
    }
    if recording["Tags.id"] is not None:
        new_rec["tags"] = [map_recording_tag(recording)]
    if recording.get("fileHash") is not None:
        new_rec["fileHash"]= recording["fileHash"]
  
    if recording.get("rawMimeType") is not None:
        new_rec["rawMimeType"]= recording["rawMimeType"]

    if recording.get("StationId") is not None:
        new_rec["stationId"]= recording["StationId"]

    if recording.get("additionalMetadata") is not None:
        new_rec["additionalMetadata"]= recording["additionalMetadata"]

    return new_rec

def map_recording_tag(rec_tag):
    print("rec tag is ",rec_tag)
    tag = {
        "automatic": rec_tag["Tags.automatic"],
        "confidence": rec_tag["Tags.confidence"],
        "detail": rec_tag["Tags.detail"],
        "id": rec_tag["Tags.id"],
        "recordingId": rec_tag["id"],
        "version": rec_tag["Tags.version"],
        "createdAt": rec_tag["Tags.createdAt"],
        "comment": rec_tag["Tags.comment"],
    }
    if rec_tag["Tags.taggerId"] is not None :
        tag["Tags.taggerId"] = rec_tag["Tags.taggerId"]
        if rec_tag["Tags.tagger"] is not None :
            tag["Tags.taggerName"] = rec_tag["Tags.tagger.userName"]
        
    
    if rec_tag["Tags.startTime"]  is not None and rec_tag["Tags.startTime"] is not None:
        tag["Tags.startTime"] = rec_tag["Tags.startTime"];
    
    if rec_tag["Tags.duration"] is not None and rec_tag["Tags.duration"] is not None:
        tag["Tags.duration"] = rec_tag["Tags.duration"]
    
    return tag



class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)



if __name__ == "__main__":
    main()
