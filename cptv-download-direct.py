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
from multiprocessing import Pool, Process, Queue
import time

HOST_NAME = socket.gethostname()
CONFIG_FILE = "./config.yaml"
DUMP_EXT = ".pgdump"
OLD_TRACKER = parse_date("2021-06-01 17:02:30.592 +1200")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--type",
        default="thermalRaw",
        help="Type of filed to download defaults to thermalRaw",
    )
    parser.add_argument(
        "--start-date",
        help="If specified, only files recorded on or after this date will be downloaded.",
    )
    parser.add_argument("out_folder", help="Root folder to place downloaded files in.")
    args = parser.parse_args()
    return args


def connect_to_db():
    try:
        print("Connecting to localhost as user postgres")
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


s3_archive_bucket = None


def init_logging():
    """Set up logging for use by various classifier pipeline scripts.

    Logs will go to stderr.
    """

    fmt = "%(levelname)7s %(message)s"
    logging.basicConfig(
        stream=sys.stderr, level=logging.INFO, format=fmt, datefmt="%Y-%m-%d %H:%M:%S"
    )


def main():
    args = parse_args()
    init_logging()
    download_dir = Path(args.out_folder)
    download_dir.mkdir(exist_ok=True)

    logging.info("Running CPTV Download on cacodb")

    if not os.path.exists(CONFIG_FILE):
        logging.info(f"failed to find config file '{CONFIG_FILE}'")
        sys.exit()

    with open(CONFIG_FILE, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    s3_config = config["s3_auth"]
    bucket_name = s3_config["bucket"]
    del s3_config["bucket"]
    s3 = boto3.resource("s3", **s3_config)

    s3_archive_config = config["s3_archive_auth"]
    archive_bucket = s3_archive_config["bucket"]
    del s3_archive_config["bucket"]
    s3_archive = boto3.resource("s3", **s3_archive_config)
    global s3_archive_bucket
    s3_archive_bucket = s3_archive.Bucket(archive_bucket)
    conn = connect_to_db()
    with open("tagged_recordings.sql", "r") as f:
        taggedthermals_sql = f.read()

    with open("tracks_for_recordings.sql", "r") as f:
        tracks_sql = f.read()

    start_date = parse_date(args.start_date)
    limit = 200
    offset = 0
    cur = conn.cursor(cursor_factory=RealDictCursor)
    saved = 0
    recs = {}
    s3_queue = Queue()
    num_processes = 8
    processes = []
    for i in range(num_processes):
        p = Process(
            target=save_file_process,
            args=(s3_queue,),
        )
        processes.append(p)
        p.start()

    while True:
        query_sql = taggedthermals_sql.format(args.type, start_date, limit, offset)
        cur.execute(query_sql)
        rec_rows = cur.fetchall()
        if rec_rows is None or len(rec_rows) == 0:
            logging.info("Finished")
            break
        for rec_row in rec_rows:
            if rec_row["id"] in recs:
                if rec_row["Tags.id"] is not None:
                    existing_rec = recs[rec_row["id"]]
                    if "tags" not in existing_rec:
                        existing_rec["tags"] = []
                    tag = map_recording_tag(rec_row)
                    existing_rec["tags"].append(tag)
                continue

            # save any recordings as we are now on new rec
            for rec in recs.values():
                save_rec(rec, download_dir, s3_queue)
                saved += 1
                if saved % 100 == 0:
                    logging.info("Saved %s", saved)
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
                    if track_data is not None:
                        track_row["data"] = track_data
                    mapped_track = map_track(track_row)
                    tracks[track_id] = mapped_track

            recording = map_recording(rec_row)
            recording["tracks"] = list(tracks.values())
            recs[recording["id"]] = recording

        offset += limit
    # save any recordings as we are now on new rec
    for rec in recs.values():
        save_rec(rec, download_dir, s3_queue)

    for i in range(len(processes)):
        s3_queue.put(("DONE"))
    for process in processes:
        process.join()


def save_file_process(queue):
    while True:
        data = queue.get()
        try:
            if data == "DONE":
                break
            save_rec_file(data)
        except:
            logging.error("Could not save rec", exc_info=True)


def save_rec_file(data):
    filename, key = data
    # logging.info("Downloading %s", key)
    with open(filename, "wb") as f:
        s3_archive_bucket.download_fileobj(key, f)


def save_rec(rec, out_dir, s3_queue):
    dtstring = rec["recordingDateTime"].strftime("%Y%m%d-%H%M%S")
    # match old cptv-download so dont redl files
    file_base = f'{rec["id"]}-{dtstring}-{rec["deviceName"]}.txt'
    # str(rec["id"]) + "-" + dtstring + "-" + r["deviceName"]
    out_folder = get_distributed_folder(file_base)
    out_file = out_dir / out_folder / file_base
    logging.debug("Writing to %s", out_file)
    out_file.parent.mkdir(exist_ok=True, parents=True)
    with out_file.open("w") as f:
        json.dump(rec, f, indent=4, cls=CustomJSONEncoder)
    cptv_file = out_file.with_suffix(".cptv")
    if cptv_file.exists():
        return
    s3_queue.put((str(cptv_file), f'objectstore/prod/{rec["rawFileKey"]}'))


def get_track_data(s3, bucket_name, track_id):
    try:
        obj = s3.Object(bucket_name, f"Track/{track_id}")
        response = obj.get()
    except:
        logging.error("Couldn't get track data for track %s", track_id)
        return None
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

    if track_tag_base["automatic"]:
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
        "filtered": track["filtered"],
    }
    if track.get("tracking_score") is not None:
        t["tracking_score"] = track["tracking_score"]
    if track.get("minFreqHz") is not None:
        t["minFreq"] = track["minFreqHz"]
    if track.get("maxFreqHz") is not None:
        t["maxFreqHz"] = track["maxFreqHz"]

    positions = []
    if "data" in track:
        for position in track["data"]["positions"]:
            positions.append(map_position(position))

    t["positions"] = positions
    track_tag = map_track_tag(track)
    t["tags"] = [track_tag]
    return t


def map_position(position):
    if isinstance(position, list):
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
        "order": (
            position["frame_number"]
            if "frame_number" in position
            else position["order"]
        ),
        "mass": position.get("mass", None),
        "blank": position.get("blank", False),
    }


def map_recording(recording):
    new_rec = {
        "id": recording["id"],
        "deviceId": recording["DeviceId"],
        "duration": recording["duration"],
        "deviceName": recording["Device.deviceName"],
        "groupId": recording["Group.id"],
        "groupName": recording["Group.groupName"],
        "processing": recording["processing"],
        "processingState": recording["processingState"],
        "recordingDateTime": recording["recordingDateTime"],
        "stationName": recording["Station.name"],
        "type": recording["type"],
        "rawFileKey": recording["rawFileKey"],
    }
    if recording.get("lat") is not None and recording.get("lng") is not None:
        new_rec["location"] = {"lat": recording.get("lat"), "lng": recording.get("lng")}

    if recording["Tags.id"] is not None:
        new_rec["tags"] = [map_recording_tag(recording)]
    if recording.get("fileHash") is not None:
        new_rec["fileHash"] = recording["fileHash"]

    if recording.get("rawMimeType") is not None:
        new_rec["rawMimeType"] = recording["rawMimeType"]

    if recording.get("StationId") is not None:
        new_rec["stationId"] = recording["StationId"]
        if (
            recording.get("Station.lat") is not None
            and recording.get("Station.lng") is not None
        ):
            new_rec["stationlocation"] = {
                "lat": recording.get("Station.lat"),
                "lng": recording.get("Station.lng"),
            }

    if recording.get("additionalMetadata") is not None:
        new_rec["additionalMetadata"] = recording["additionalMetadata"]

    # was a bug pre this where background image was processed as well as clip so all regions are off by one frame
    tracker_version = 10
    if "recordingDateTime" in new_rec:
        try:
            if new_rec["recordingDateTime"] < OLD_TRACKER:
                tracker_version = 9
        except (ValueError, TypeError):
            tracker_version = 9
    new_rec["tracker_version"] = tracker_version
    return new_rec


def map_recording_tag(rec_tag):
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
    if rec_tag["Tags.taggerId"] is not None:
        tag["Tags.taggerId"] = rec_tag["Tags.taggerId"]
        if rec_tag.get("Tags.tagger.userName") is not None:
            tag["Tags.taggerName"] = rec_tag["Tags.tagger.userName"]

    if rec_tag["Tags.startTime"] is not None and rec_tag["Tags.startTime"] is not None:
        tag["Tags.startTime"] = rec_tag["Tags.startTime"]

    if rec_tag["Tags.duration"] is not None and rec_tag["Tags.duration"] is not None:
        tag["Tags.duration"] = rec_tag["Tags.duration"]

    return tag


def get_distributed_folder(name, num_folders=256, seed=31):
    """Creates a hash of the name then returns the modulo num_folders"""
    str_bytes = str.encode(name)
    hash_code = 0
    for byte in str_bytes:
        hash_code = hash_code * seed + byte

    return "{:02x}".format(hash_code % num_folders)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


if __name__ == "__main__":
    start = time.time()

    main()
    print("Took ", time.time() - start)
