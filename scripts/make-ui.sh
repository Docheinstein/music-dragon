#!/bin/bash

# For each xxx.ui in the ./res/ui folder generates a file name ui_xxx.py in ui folder
find "./res/ui" -name "*.ui" -exec sh -c 'pyuic6 {} -o music_dragon/ui/ui_"$(basename -s .ui {})".py' \;

# Generate resources file
pyside6-rcc -o music_dragon/ui/res_rc.py res/res.qrc