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

import youtube_dl


def main():
    parser = argparse.ArgumentParser(
        description="MusicDragon"
    )

    # Read args
    parsed = vars(parser.parse_args(sys.argv[1:]))

    app = QApplication(sys.argv)

    window = MainWindow()
    window.setup()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()