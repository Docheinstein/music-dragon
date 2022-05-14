#!/bin/bash

# For each xxx.ui in the ./res/ui folder generates a file name ui_xxx.py in ui folder
find "./res/ui" -name "*.ui" -exec sh -c 'pyuic5 {} -o ui/ui_"$(basename -s .ui {})".py' \;