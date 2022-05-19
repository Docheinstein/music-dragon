import argparse
import sys

import musicbrainz
import preferences
import ui

from PyQt5.QtWidgets import QApplication

import workers
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
    musicbrainz.initialize()
    workers.initialize()

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()