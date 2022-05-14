import argparse
import sys

from PyQt5.QtWidgets import QApplication

from mainwindow import MainWindow


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