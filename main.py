import argparse
import sys

import cache
import musicbrainz
import preferences
import ui

from PyQt5.QtWidgets import QApplication

import utils
import workers
import ytmusic
from log import debug
from ui.mainwindow import MainWindow


def main():
    utils.initialize_execution_time()

    parser = argparse.ArgumentParser(
        description="MusicDragon"
    )

    parsed = vars(parser.parse_args(sys.argv[1:]))

    app = QApplication(sys.argv)
    app.setOrganizationName("Docheinstein")
    app.setApplicationName("MusicDragon")

    debug(f"Config location: {utils.app_config_path()}")
    debug(f"Cache location: {utils.app_cache_path()}")

    preferences.initialize()
    ui.resources.initialize()
    workers.initialize(max_num_threads=preferences.thread_number())
    ytmusic.initialize()
    musicbrainz.initialize()
    cache.initialize(images=preferences.is_images_cache_enabled(),
                     requests=preferences.is_requests_cache_enabled())

    window = MainWindow()
    window.show()


    sys.exit(app.exec_())


if __name__ == '__main__':
    main()