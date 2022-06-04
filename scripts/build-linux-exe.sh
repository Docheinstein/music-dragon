#!/bin/bash

echo "=========== BUILD INSTALLER =========="

# -D: onedir
# -F: onefile
# pyinstaller main.spec --workpath ./tmp
pyinstaller music_dragon/main.py --workpath ./tmp -F \
  --add-data "other/pyinstaller_imports/:."
#pyinstaller music_dragon/main.py --workpath ./tmp -D \
#  --add-data "/usr/lib/libvlc.so:." \
#  --add-data "/usr/lib/libvlccore.so:." \
#  --add-data "/usr/lib/vlc/plugins/:." \
#  --add-data "/usr/lib/vlc/libvlc_pulse.so/:." \
#  --add-data "/usr/lib/vlc/libvlc_vdpau.so/:." \

