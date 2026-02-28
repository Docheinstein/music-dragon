import argparse
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

import music_dragon.ui.res_rc

from music_dragon import utils, workers, ytmusic, preferences, cache, musicbrainz, favourites, APP_DISPLAY_NAME, \
    APP_ORGANIZATION_NAME, APP_VERSION
from music_dragon.log import debug
from music_dragon.ui.mainwindow import MainWindow
from music_dragon.ui import resources

from yt_dlp.version import __version__ as yt_dlp_version
from yt_dlp_ejs._version import __version__  as yt_dlp_ejs_version

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


    debug(f"{APP_DISPLAY_NAME} version: {APP_VERSION}")
    debug(f"yt-dlp version: {yt_dlp_version}")
    debug(f"yt-dlp-ejs version: {yt_dlp_ejs_version}")

    debug(f"Config location: {utils.app_config_path()}")
    debug(f"Cache location: {utils.app_cache_path()}")

    preferences.initialize()
    favourites.initialize()
    favourites.load_favourites()
    resources.initialize()
    workers.initialize(max_num_threads=preferences.thread_number())
    ytmusic.initialize()
    musicbrainz.initialize()
    cache.initialize(images=preferences.is_images_cache_enabled(),
                     requests=preferences.is_requests_cache_enabled(),
                     localsongs=preferences.is_localsongs_cache_enabled())

    window = MainWindow()
    window.show()


    sys.exit(app.exec())


if __name__ == '__main__':
    main()
