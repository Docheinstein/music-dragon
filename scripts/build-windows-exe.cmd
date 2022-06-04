@echo off

echo =========== BUILD INSTALLER ==========

pyinstaller.exe music_dragon/main.py --workpath ./tmp -F --add-data "other/pyinstaller_imports/;." --hidden-import "vlc"