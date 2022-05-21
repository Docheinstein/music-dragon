import argparse
import sys

import musicbrainz
import preferences
import ui

from PyQt5.QtWidgets import QApplication

import workers
import ytmusic
from ui.mainwindow import MainWindow


def main():
    parser = argparse.ArgumentParser(
        description="MusicDragon"
    )

    # Read args
    parsed = vars(parser.parse_args(sys.argv[1:]))

    app = QApplication(sys.argv)

    preferences.initialize()
    ui.resources.initialize()
    workers.initialize()
    musicbrainz.initialize()
    ytmusic.initialize("res/other/yt_auth.json")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()