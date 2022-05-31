import os
from pathlib import Path
from typing import List, Optional

import eyed3
from PyQt5.QtCore import pyqtSignal
from eyed3.core import AudioFile

import workers
from log import debug
from workers import Worker

MP3_IMAGE_TAG_INDEX_FRONT_COVER = 3

mp3s_indexes_by_metadata = {}
mp3s = []

class Mp3:
    def __init__(self):
        # tag
        self.tag = None
        self.artist = None
        self.album = None
        self.song = None
        self.track_num = None
        self.image = None

        self.path: Optional[Path] = None

        #
        self.fetched_release_group = False
        self.release_group_id = None

        self.fetched_artist = False
        self.artist_id = None

        self.fetched_track = False
        self.track_id = None

    def load_from_file(self, file: str, load_image=True):
        p = Path(file)

        if not p.is_file():
            print(f"ERROR: cannot load file '{file}': not a file")
            return False

        if p.suffix != ".mp3":
            return False

        self.path = p.absolute()

        try:
            mp3: AudioFile = eyed3.load(self.path)
            if mp3:
                if not mp3.tag:
                    print(f"WARN: not tag for mp3 '{file}', skipping")
                    return False

                self.tag = mp3.tag
                self.artist = mp3.tag.artist
                self.album = mp3.tag.album
                self.song = mp3.tag.title
                self.track_num = mp3.tag.track_num
                if load_image:
                    self._load_image_from_tag()

                debug(f"Loaded {self.path}: "
                      f"(artist={self.artist}, album={self.album}, "
                      f"title={self.album}, image={'yes' if self.image else 'no'})")
                return True
        except Exception as e:
            print(f"WARN: failed to load mp3 from '{file}': {e}")

        return False

    def _load_image_from_tag(self):
        for img in self.tag.images:
            if img.picture_type == MP3_IMAGE_TAG_INDEX_FRONT_COVER:
                self.image = img.image_data
                debug(f"Loaded image of {self}")

    def __str__(self):
        return f"{self.artist} - {self.album} - {self.song}"


def get_by_metadata(artist: str, album: str, song: str):
    idx = mp3s_indexes_by_metadata.get((artist, album, song))
    debug(f"Checking availability of ({artist}, {album}, {song})")
    if idx is not None and 0 <= idx < len(mp3s):
        debug("-> found")
        return mp3s[idx]
    return None

def load_mp3(file: str, load_image=True):
    mp3: Mp3 = Mp3()
    if mp3.load_from_file(file, load_image=load_image):
        mp3s_indexes_by_metadata[(mp3.artist, mp3.album, mp3.song)] = len(mp3s)
        mp3s.append(mp3)
        return mp3
    return None

def load_mp3s(directory: str, load_images=True, mp3_loaded_callback=None):
    root = Path(directory)
    if not root.is_dir():
        print(f"ERROR: cannot load from directory '{directory}': not a directory")
        return

    file_count = 0
    loaded_file_count = 0
    for root, dirs, files in os.walk(str(root.absolute()), topdown=False):
        for file in files:
            file_count += 1
            mp3 = load_mp3(os.path.join(root, file), load_image=load_images)
            if mp3:
                loaded_file_count += 1
                if callable(mp3_loaded_callback):
                    mp3_loaded_callback(mp3)
    debug(f"Loaded {loaded_file_count}/{file_count} mp3 files")

def clear_mp3s():
    mp3s_indexes_by_metadata.clear()
    mp3s.clear()

# ============ LOAD MP3s  ===============
# Load mp3s and their tags from directory
# =======================================

class LoadMp3sWorker(Worker):
    mp3_loaded = pyqtSignal(Mp3)

    def __init__(self, directory: str, load_images):
        super().__init__()
        self.directory = directory
        self.load_images = load_images

    def run(self):
        # Fetch all the releases and releases tracks for the release groups
        debug(f"LOCALSONGS: load_mp3s: '{self.directory}'")

        load_mp3s(self.directory, mp3_loaded_callback=self._on_mp3_loaded, load_images=self.load_images)
        # TODO: sort?

    def _on_mp3_loaded(self, mp3: Mp3):
        self.mp3_loaded.emit(mp3)


def load_mp3s_background(directory, mp3_loaded_callback=None, finished_callback=None,
                         load_images=True, priority=workers.Worker.PRIORITY_BELOW_NORMAL):
    worker = LoadMp3sWorker(directory, load_images=load_images)
    worker.priority = priority
    if mp3_loaded_callback:
        worker.mp3_loaded.connect(mp3_loaded_callback)
    if finished_callback:
        worker.finished.connect(lambda: finished_callback(load_images))
    workers.schedule(worker)

# ============ LOAD MP3  ===============
# Load mp3 and its tags from file
# =======================================

class LoadMp3Worker(Worker):
    mp3_loaded = pyqtSignal(Mp3)

    def __init__(self, file: str, load_image):
        super().__init__()
        self.file = file
        self.load_image = load_image

    def run(self):
        # Fetch all the releases and releases tracks for the release groups
        debug(f"LOCALSONGS: load_mp3: '{self.file}'")

        mp3 = load_mp3(self.file, load_image=self.load_image)
        if mp3:
            self.mp3_loaded.emit(mp3)

def load_mp3_background(file, mp3_loaded_callback=None, load_image=True,
                        priority=workers.Worker.PRIORITY_BELOW_NORMAL):
    worker = LoadMp3Worker(file, load_image=load_image)
    worker.priority = priority
    if mp3_loaded_callback:
        worker.mp3_loaded.connect(mp3_loaded_callback)
    workers.schedule(worker)


# ============ LOAD MP3s IMAGES ===============
# Load mp3s images
# =============================================

class LoadMp3sImagesWorker(Worker):
    mp3_image_loaded = pyqtSignal(Mp3)

    def __init__(self):
        super().__init__()

    def run(self):
        debug(f"LOCALSONGS: load_mp3s_images: ({len(mp3s)})")

        for mp3 in mp3s:
            mp3._load_image_from_tag()
            self.mp3_image_loaded.emit(mp3)


def load_mp3s_images_background(
        mp3_image_loaded_callback=None, finished_callback=None,
        priority=workers.Worker.PRIORITY_LOW):
    worker = LoadMp3sImagesWorker()
    worker.priority = priority
    if mp3_image_loaded_callback:
        worker.mp3_image_loaded.connect(mp3_image_loaded_callback)
    if finished_callback:
        worker.finished.connect(finished_callback)
    workers.schedule(worker)
