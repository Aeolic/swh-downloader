import argparse
import os
import shutil
import time

import requests


def main():
    parser = argparse.ArgumentParser(
        description="This python script requests cooking for a given revision or directory from "
                    "softwareheritage.org. \n "
                    "")
    parser.add_argument("id", metavar="ID", type=str, help="The revision or directory id.")
    parser.add_argument("-o", default=".", help="Output directory. Default: current directory")
    parser.add_argument("--dir", dest="id_type", action='store_const', const='directory',
                        default="revision",
                        help="Interpret given id as SWH directory id. Default: Revision id.")
    args = parser.parse_args()
    swh_id, id_type, output_dir = args.id, args.id_type, args.o

    if id_type == "revision":
        get_dir_url = "https://archive.softwareheritage.org/api/1/revision/{0}".format(
            swh_id)  # TODO this should use https://archive.softwareheritage.org/api/1/revision/directory/doc/, but this returns 500 right now

        print("Resolving revision id...")
        revision_info = requests.get(get_dir_url)
        if revision_info.status_code != 200:
            print("Trying to resolve the revision id did not return 200 OK but: {0}".format(
                revision_info.status_code))
            exit(1)
        rev_info_json = revision_info.json()
        dir_id = rev_info_json["directory"]
        print("Got directory id:", dir_id)

    else:
        dir_id = swh_id

    request_cooking_url = "https://archive.softwareheritage.org/api/1/vault/directory/{0}".format(
        dir_id)
    is_cooked = False
    print("Requesting cooking for directory {0}.".format(dir_id))
    while not is_cooked:
        cooking_status = requests.post(request_cooking_url)
        if cooking_status.status_code != 200:
            print("Trying to get the cooking status did not return 200 OK but: {0}".format(
                cooking_status.status_code))
            exit(1)
        cooking_status_json = cooking_status.json()
        task_status = cooking_status_json["status"]

        if task_status != "done":
            print("Cooking is not done yet, retrying in 10 seconds.")
            time.sleep(10)
        else:
            print("Cooking is done, attempting to download the directory.")
            is_cooked = True

    print("Downloading the directory...")
    fetch_url = request_cooking_url + "/raw/"
    fetch_dir = requests.get(fetch_url)
    if fetch_dir.status_code != 200:
        print("Trying to download the directory did not return 200 OK but: {0}".format(
            fetch_dir.status_code))
        exit(1)

    filename = "{0}.tar.gz".format(dir_id)
    with open(filename, "wb") as f:
        f.write(fetch_dir.content)
    print("Extracting the tar file...")
    shutil.unpack_archive(filename, output_dir)
    print("Deleting tar file...")
    os.remove(filename)


if __name__ == '__main__':
    main()
