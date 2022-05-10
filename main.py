import argparse
import asyncio
import json
import os
import sys
import tempfile
from os import write
import urllib.request
import musicbrainzngs as mb

from PyQt5.QtCore import QSize, QTimer, Qt
from PyQt5.QtWidgets import QApplication, QLabel, QGridLayout, QWidget, QProgressBar
from PyQt5.QtGui import QPixmap, QKeyEvent, QFont
from musicbrainzngs import ResponseError

from log import debug
from mainwindow import MainWindow
from utils import j


def setup():
    mb.set_useragent("MusicDragon", "0.1")

def main():
    parser = argparse.ArgumentParser(
        description="MusicDragon"
    )

    # Read args
    parsed = vars(parser.parse_args(sys.argv[1:]))

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    setup()
    main()
    exit(0)

    print("Getting releases...")
    result = mb.search_releases("Fear of the Dark", limit=10, primarytype="Album")
    print("Got releases")

    # print(j(result))
    got = False
    for release in result["release-list"]:
        if got:
            break
        # release_details = mb.get_release_by_id(release["id"])
        try:
            print(f"Getting image list for release {release['id']}")

            img = mb.get_image_list(release["id"])
            print(f"Got image for {release['id']}")


            """
            image_list = mb.get_image_list(release["id"])["images"]
            print("Got image list")
            
            
            
            for image in image_list:
                if image["front"]:
                    print("Found front image metadata")
                    image_id = image["id"]
                    image_url = image["thumbnails"]["small"]

                    print("Fetching image data...")
                    response = urllib.request.urlopen(image_url)
                    data = response.read()
                    print("Fetched image data")

                    print("Writing image data...")
                    (fd, name) = tempfile.mkstemp(prefix=f"{release['id']}_{image_id}", suffix=".png")
                    with os.fdopen(fd, "wb") as f:
                        f.write(data)
                        print(f"Wrote image data to {name}")
                        got = True
                        break
                """
        except ResponseError as err:
            print(f"WARN: failed to retrieve image for {release['id']}: {err}")