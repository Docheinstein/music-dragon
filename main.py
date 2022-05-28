import argparse
import sys

import musicbrainz
import preferences
import localsongs
import ui

from PyQt5.QtWidgets import QApplication, QMessageBox

import utils
import workers
import ytmusic
from log import debug
from ui.mainwindow import MainWindow
from ui.ytmusicsetupwindow import YtMusicSetupWindow


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

    window = MainWindow()
    window.show()

    ytmusic.initialize()
    #
    # if ytmusic.auth_file().exists():
    #     try:
    #         ytmusic.initialize()
    #     except Exception as e:
    #         QMessageBox.critical(window, "YtMusic Setup Failed",
    #                              "Failed to initialize YtMusic API.\n"
    #                              f"{e}",
    #                              QMessageBox.Ok)
    #
    # else:
    #     ytmusicsetup = YtMusicSetupWindow()
    #     ytmusicsetup.show()

    musicbrainz.initialize()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()