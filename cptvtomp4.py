import argparse
import glob
import os
import json

from pathlib import Path
import datetime

from mpegcreator import MPEGCreator
from cptv import CPTVReader
import numpy as np
import cv2


def normalize(frame, a_min, a_max):
    frame = (np.float32(frame) - a_min) / (a_max - a_min)
    np.clip(frame, 0, None, out=frame)
    return np.uint8(frame * 255)


def convertToMP4(filename):
    cptv_file = Path(filename)
    out_file = cptv_file.with_suffix(".mp4")
    print("Converting", out_file)
    min_pixel = None
    max_pixel = None
    with open(str(cptv_file), "rb") as f:
        reader = CPTVReader(f)
        for frame in reader:
            if frame.background_frame:
                continue

            a_max = np.amax(frame.pix)
            a_min = np.amin(frame.pix[frame.pix > 0])
            if min_pixel is None:
                min_pixel = a_min
                max_pixel = a_max
            else:
                min_pixel = min(a_min, min_pixel)
                max_pixel = max(max_pixel, a_max)
    with open(str(cptv_file), "rb") as f:
        reader = CPTVReader(f)
        mpeg = MPEGCreator(str(out_file))
        for frame in reader:
            if frame.background_frame:
                continue
            normed = normalize(frame.pix, min_pixel, max_pixel)
            normed = normed[:, :, np.newaxis]
            normed = np.repeat(normed, 3, axis=2)
            mpeg.next_frame(normed)

        mpeg.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="File/Folder of cptv to convert to mp4")

    args = parser.parse_args()
    base_dir = Path(args.filename)
    if base_dir.is_dir():
        for file_name in base_dir.rglob("**/*.cptv"):
            if file_name.is_file():
                convertToMP4(file_name)
    else:
        convertToMP4(base_dir)


if __name__ == "__main__":
    main()
