import yaml
import urllib.request
import json
import argparse
import os
import logging
logging.basicConfig(level=logging.INFO)

# get auth
with open("auth.yaml") as f:
    data = yaml.load(f)
    ACCESS_TOKEN = data["dropbox_token"]

def make_dropbox_request(endpoint, args, data, access_token=ACCESS_TOKEN):
    """Makes a request to the given endpoint with the given api args.
    Expects args to not yet be encoded into a string.
    data, however, should be bytes"""
    url = "https://content.dropboxapi.com/2/" + endpoint
    headers = {
        "Authorization": "Bearer " + access_token,
        "Dropbox-API-Arg":  json.dumps(args, ensure_ascii=False),
        "Content-Type": "application/octet-stream"
    }
    req = urllib.request.Request(url, headers=headers, data=data)
    with urllib.request.urlopen(req) as response:
        status = json.loads(response.read().decode('utf-8'))
    return status

def get_args():
    """Parses arguments. If a single argument, uploads it.
    If it is a directory, uploads everything in it
    (either recursively or not depending on the other arg).
    If there is a list of arguments, then each is treated
    as a single file"""
    parser = argparse.ArgumentParser(
        description="Helpful tool to upload files to dropbox")
    parser.add_argument('files', nargs='+',
        help="Files or folders to upload.")
    parser.add_argument('--recurse', '-r',
                        action='store_true',
                        help="whether to recurse into subdirectories")
    parser.add_argument('--path', default="/",
                        help="path on the dropbox side")
    return parser.parse_args()

def handle_directory(local_path, dropbox_dir, recurse):
    """Uploads a directory's contents to dropbox_dir + local_path"""
    # first let's figure out the new dropbox directory path
    logging.info("Checking directory %s", local_path)
    # split it with the file separator and get the last non-empty guy
    path = local_path.split(os.path.sep)
    path = path[-1] if path[-1] else path[-2]
    dropbox_path = dropbox_dir + "/" + path
    # now go through the directory
    for f in os.listdir(local_path):
        fullpath = os.path.join(local_path, f)
        if os.path.isdir(fullpath):
            if recurse:
                handle_directory(fullpath, dropbox_path, recurse)
        else:
            handle_single_file(fullpath, dropbox_path)


def handle_single_file(local_path, dropbox_dir):
    """Uploads only one file to the given dropbox location + local filename.
    Always overwrites existing files."""
    # TODO paths aren't always right
    args = {
        "path": dropbox_dir + "/" + os.path.basename(local_path),
        "mode": "overwrite"
    }
    with open(local_path, 'rb') as f:
        data = f.read()
    logging.info("Attempting to upload %s", local_path)
    make_dropbox_request("files/upload", args, data)

def main():
    """Actually does the business
    """
    args = get_args()
    logging.info("Got %d files/directories to upload", len(args.files))
    for fname in args.files:
        if os.path.isdir(fname):
            handle_directory(fname, args.path, args.recurse)
        else:
            handle_single_file(fname, args.path)

if __name__ == "__main__":
    main()
