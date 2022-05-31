#!/bin/bash

# For each xxx.ui in the ./res/ui folder generates a file name ui_xxx.py in ui folder
find "./res/ui" -name "*.ui" -exec sh -c 'pyuic5 --from-imports {} -o music_dragon/ui/ui_"$(basename -s .ui {})".py' \;
pyrcc5 -o music_dragon/res_rc.py res/res.qrc