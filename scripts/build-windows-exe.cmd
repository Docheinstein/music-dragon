@echo off

echo =========== BUILD INSTALLER ==========

pyinstaller.exe music_dragon/main.py --workpath ./tmp -D -w^
    --add-data "other/pyinstaller_data/shared/ytmusicapi/;." ^
    --add-data "other/pyinstaller_data/windows/ffmpeg/;." ^
    --add-data "other/pyinstaller_data/windows/vlc/;." ^
    --hidden-import "levenshtein"
