import os
from pathlib import Path

import eyed3
from PyQt5.QtCore import pyqtSignal
from eyed3.core import AudioFile

import workers
from log import debug
from workers import Worker

MP3_IMAGE_TAG_INDEX_FRONT_COVER = 3

mp3s = {}


def load_mp3(file: str):
    p = Path(file)

    if not p.is_file():
        print(f"ERROR: cannot load file '{file}': not a file")
        return None

    if p.suffix != ".mp3":
        return None

    abs_file_path = str(p.absolute())

    try:
        mp3: AudioFile = eyed3.load(abs_file_path)
        if mp3:
            if not mp3.tag:
                print(f"WARN: not tag for mp3 '{file}', skipping")
                return None

            artist = mp3.tag.artist
            album = mp3.tag.album
            title = mp3.tag.title
            track_num = mp3.tag.track_num
            image = None
            # for img in mp3.tag.images:
            #     if img.picture_type == MP3_IMAGE_TAG_INDEX_FRONT_COVER:
            #         image = img.image_data

            key = (artist, album, title)

            debug(
                f"Loaded {abs_file_path}: (artist={artist}, album={album}, title={title}, image={'yes' if image else 'no'})")
            value = {
                "artist": artist,
                "album": album,
                "title": title,
                "track_num": track_num,
                # "image": image,
                "path": abs_file_path
            }
            mp3s[key] = value
            return value
    except Exception as e:
        print(f"WARN: failed to load mp3 from '{file}': {e}")

    return None


def load_mp3s(directory: str, mp3_loaded_callback=None):
    root = Path(directory)
    if not root.is_dir():
        print(f"ERROR: cannot load from directory '{directory}': not a directory")
        return

    file_count = 0
    loaded_file_count = 0
    for root, dirs, files in os.walk(str(root.absolute()), topdown=False):
        for file in files:
            file_count += 1
            mp3 = load_mp3(os.path.join(root, file))
            if mp3:
                loaded_file_count += 1
                if callable(mp3_loaded_callback):
                    mp3_loaded_callback(mp3)
    debug(f"Loaded {loaded_file_count}/{file_count} mp3 files")



# ============ LOAD MP3s  ===============
# Load mp3s and their tags from directory
# =======================================

class LoadMp3s(Worker):
    mp3_loaded = pyqtSignal(str, str, str, str)

    def __init__(self, directory: str):
        super().__init__()
        self.directory = directory

    def run(self):
        # Fetch all the releases and releases tracks for the release groups
        debug(f"STORAGE: load_mp3s: '{self.directory}'")

        load_mp3s(self.directory, mp3_loaded_callback=self._on_mp3_loaded)

    def _on_mp3_loaded(self, mp3):
        self.mp3_loaded.emit(mp3["artist"], mp3["album"], mp3["title"], mp3["path"])


def load_mp3s_background(directory, mp3_loaded_callback=None, finished_callback=None, priority=workers.Worker.PRIORITY_NORMAL):
    worker = LoadMp3s(directory)
    worker.priority = priority
    if mp3_loaded_callback:
        worker.mp3_loaded.connect(mp3_loaded_callback)
    if finished_callback:
        worker.finished.connect(finished_callback)
    workers.schedule(worker)

def reload_mp3s_background(directory, callback, priority=workers.Worker.PRIORITY_NORMAL):
    mp3s.clear()
    load_mp3s_background(directory, callback, priority)


