"""
A command line client for interacting with the Cacophony Project Files API.

See https://api.cacophony.org.nz/#api-Files
"""

# TODO: upload support (with descriptions etc)
# TODO: sync support (sync file and details between environments)

import argparse
import sys
from os.path import join

from api import API


def main():
    args = parse_args()
    api = API(args.server, args.username, args.password)

    if args.command == "list":
        do_list(api)
    elif args.command == "download":
        do_download(api, args)
    elif args.command == "delete":
        do_delete(api, args)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--server", default="https://api.cacophony.org.nz", help="API server URL"
    )
    parser.add_argument("username", help="Username to authenticate with as")
    parser.add_argument("password", help="Password to authenticate with")

    subparsers = parser.add_subparsers(dest="command")

    # list
    subparsers.add_parser("list", help="list available files")

    # download
    download_parser = subparsers.add_parser("download", help="download files")
    download_parser.add_argument("-i", "--id", help="File id to download")
    download_parser.add_argument(
        "--all", action="store_true", help="Download all files"
    )
    download_parser.add_argument(
        "-d", "--directory", default=".", help="Target directory for downloads"
    )

    # delete
    delete_parser = subparsers.add_parser("delete", help="delete files")
    delete_parser.add_argument("id", help="File id to delete", nargs="+")

    args = parser.parse_args()
    if not args.command:
        args.command = "list"

    return args


def do_list(api):
    for f in api.list_files():
        print(format_file_info(f))


def format_file_info(info):
    line = f"{info['id']:4}[{info['type']}]: "
    d = info["details"]
    if info["type"] == "audioBait":
        line += repr(d["name"])
        animal = d.get("animal")
        if animal:
            line += " animal=" + repr(animal)
        filename = d.get("originalName")
        if filename:
            line += " file=" + repr(filename)
        source = d.get("source")
        if source:
            line += " src=" + source
        return line
    return line + str(d)


def do_download(api, args):
    if args.id:
        download_one_file(api, args.id, args.directory)
    elif args.all:
        for f in api.list_files():
            download_one_file(api, f["id"], args.directory)
    else:
        sys.exit("--id or --all must be given")


def do_delete(api, args):
    for file_id in args.id:
        api.delete_file(file_id)
    print(f"deleted {len(args.id)} file(s)")


def download_one_file(api, file_id, directory):
    info, data = api.download_file(file_id)
    filename = join(directory, make_filename(info))
    print("downloading to {!r}".format(filename))
    iter_to_file(filename, data)


def make_filename(info):
    return f"{info['id']}-{info['details']['originalName']}"


def iter_to_file(filename, source):
    with open(filename, "wb") as f:
        for chunk in source:
            f.write(chunk)


if __name__ == "__main__":
    main()
