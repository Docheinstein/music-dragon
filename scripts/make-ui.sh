#!/bin/bash

# For each xxx.ui in the ./ui folder generates a file name ui_xxx.py in root folder
find ./ui -name "*.ui" -exec sh -c 'pyuic5 {} -o ./ui_"$(basename -s .ui {})".py' \;