import argparse
import logging
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

import music_dragon.ui.res_rc

from music_dragon import utils, workers, ytmusic, preferences, cache, musicbrainz, APP_DISPLAY_NAME, \
    APP_ORGANIZATION_NAME
from music_dragon.log import debug
from music_dragon.ui.mainwindow import MainWindow
from music_dragon.ui import resources


def main():
    utils.initialize_execution_time()

    parser = argparse.ArgumentParser(
        description="MusicDragon"
    )

    # --verbose
    parser.add_argument("-v", "--verbose",
                        action="store_const", const=True, default=False,
                        dest="verbose",
                        help="Print more messages")

    parsed = vars(parser.parse_args(sys.argv[1:]))
    music_dragon.log.debug_enabled = parsed.get("verbose")

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(":/images/logo.png"))
    app.setOrganizationName(APP_ORGANIZATION_NAME)
    app.setApplicationName(APP_DISPLAY_NAME)

    debug(f"Config location: {utils.app_config_path()}")
    debug(f"Cache location: {utils.app_cache_path()}")

    preferences.initialize()
    resources.initialize()
    workers.initialize(max_num_threads=preferences.thread_number())
    ytmusic.initialize()
    musicbrainz.initialize()
    cache.initialize(images=preferences.is_images_cache_enabled(),
                     requests=preferences.is_requests_cache_enabled())

    # import ytdownloader
    # def cb(_1, _2, _3):
    #     pass
    # ytdownloader.fetch_playlist_info("OLAK5uy_lpSnEyKbjOu3VsxiS7TIpYNZuyXziuy_M", cb, {})
    # def cb(_1, _2):
    #     pass

    # ytmusic.fetch_album_or_playlist_info("OLAK5uy_lpSnEyKbjOu3VsxiS7TIpYNZuyXziuy_M", cb)
    # ytmusic.fetch_album_or_playlist_info("PLCfCU1Ok5NVslWB4mi0MtVsvpjILpFy-p", cb)

    window = MainWindow()
    window.show()


    sys.exit(app.exec_())


if __name__ == '__main__':
    main()