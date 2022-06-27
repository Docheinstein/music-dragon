import os
from pathlib import Path
from typing import Optional

import eyed3
from PyQt5.QtCore import pyqtSignal
from eyed3.core import AudioFile

from music_dragon import workers
from music_dragon.log import debug
from music_dragon.utils import crc32
from music_dragon.workers import Worker

MP3_IMAGE_TAG_INDEX_FRONT_COVER = 3

mp3s_indexes_by_metadata = {}
mp3s = []

class Mp3:
    def __init__(self):
        # tag
        self.tag = None
        self.length = None
        self.artist = None
        self.album = None
        self.song = None
        self.track_num = None
        self.image = None
        self.image_path = None # only available if cached
        self.size = None
        self.year = None

        self.path: Optional[Path] = None

        #
        self.fetched_release_group = False
        self.release_group_id = None

        self.fetched_artist = False
        self.artist_id = None

        self.fetched_track = False
        self.track_id = None

    def title(self):
        if self.song:
            return self.song
        print(f"WARN: no song attribute for mp3 {self.path}")
        return self.path.stem

    def load_from_file(self, file: str, load_image=True):
        p = Path(file)

        if not p.is_file():
            print(f"ERROR: cannot load file '{file}': not a file")
            return False

        if p.suffix != ".mp3":
            return False

        self.path = p.absolute()
        self.tag = None

        try:
            self.size = os.stat(self.path).st_size

            mp3: AudioFile = eyed3.load(self.path)
            if mp3:
                if not mp3.tag:
                    print(f"WARN: no mp3 tag found for file '{file}', skipping")
                    return False
                self.length = 1000 * mp3.info.time_secs
                self.tag = mp3.tag
                self.artist = mp3.tag.artist
                self.album = mp3.tag.album
                self.song = mp3.tag.title
                self.track_num = mp3.tag.track_num[0]
                try:
                    self.year = mp3.tag.getBestDate().year
                except:
                    pass

                if load_image:
                    self._load_image_from_tag()

                debug(f"Loaded {self.path}: "
                      f"(artist={self.artist}, "
                      f"album={self.album}, "
                      f"title={self.song}, "
                      f"year={self.year}, "
                      f"track_num={self.track_num}, "
                      f"image={'yes' if self.image else 'no'})")
                return True
        except Exception as e:
            print(f"WARN: failed to load mp3 from '{file}': {e}")

        return False

    def load_from_info(self, info: dict, load_image=True):
        self.size = info.get("size")
        self.path = Path(info.get("path"))
        self.length = info.get("length")
        self.artist = info.get("artist")
        self.album = info.get("album")
        self.song = info.get("song")
        self.track_num = info.get("track_num")
        self.year = info.get("year")
        self.image_path = info.get("image")
        self.tag = None

        if load_image:
            if self.image_path:
                self._load_image_from_path(self.image_path)

                debug(f"Loaded [cached] {self.path}: "
                      f"(artist={self.artist}, "
                      f"album={self.album}, "
                      f"title={self.song}, "
                      f"year={self.year}, "
                      f"track_num={self.track_num}, "
                      f"image={'yes' if self.image else 'no'})")

        return True


    def load_image(self):
        if self.image:
            return

        if self.image_path is not None:
            self._load_image_from_path(self.image_path)
        else:
            self._load_image_from_tag()


    def _load_image_from_tag(self):
        # Eventually load tag
        if not self.tag:
            try:
                mp3: AudioFile = eyed3.load(self.path)
                if mp3:
                    self.tag = mp3.tag
            except Exception as e:
                print(f"WARN: failed to load mp3 from '{self.path}': {e}")

        if not self.tag:
            print(f"WARN: no tag for mp3 {self.path}")
            return

        for img in self.tag.images:
            if img.picture_type == MP3_IMAGE_TAG_INDEX_FRONT_COVER:
                self.image = img.image_data
                debug(f"Loaded image of {self}")


    def _load_image_from_path(self, image_path):
        with Path(image_path).open("rb") as img:
            self.image = img.read()
            debug(f"Loaded [cached] image of {self}")


    def __str__(self):
        return f"{self.artist} - {self.album} - {self.song}"


def get_by_metadata(artist: str, album: str, song: str) -> Optional[Mp3]:
    idx = mp3s_indexes_by_metadata.get((artist, album, song))
    debug(f"Checking availability of ({artist}, {album}, {song})")
    if idx is not None and 0 <= idx < len(mp3s):
        debug("-> found")
        return mp3s[idx]
    else:
        debug("-> not found")
    return None


def load_mp3(file: str, load_image=True):
    mp3: Mp3 = Mp3()
    if mp3.load_from_file(file, load_image=load_image):
        mp3s_indexes_by_metadata[(mp3.artist, mp3.album, mp3.title())] = len(mp3s)
        mp3s.append(mp3)
        return mp3
    return None

def load_mp3_from_info(mp3_info: dict, load_image=True):
    mp3: Mp3 = Mp3()
    if mp3.load_from_info(mp3_info, load_image=load_image):
        mp3s_indexes_by_metadata[(mp3.artist, mp3.album, mp3.title())] = len(mp3s)
        mp3s.append(mp3)
        return mp3
    return None

def load_mp3s(directory: str, info=None, load_images=True, mp3_loaded_callback=None):
    root = Path(directory)
    if not root.exists():
        print(f"WARN: cannot load mp3s from directory '{directory}': does not exist")
        return
    if not root.is_dir():
        print(f"WARN: cannot load mp3s from directory '{directory}': not a directory")
        return

    file_count = 0
    loaded_file_count = 0
    for root, dirs, files in os.walk(str(root.absolute()), topdown=False):
        for file in files:
            if not file.endswith(".mp3"):
                continue # skip non mp3
            file_count += 1

            full_path = os.path.join(root, file)

            mp3 = None

            # check whether we already know this file
            if info and full_path in info:
                mp3_info =  info[full_path]
                stat = os.stat(full_path)
                # TODO: md5, crc32 would be more reliable
                if mp3_info.get("size", 0) == stat.st_size:
                    mp3 = load_mp3_from_info(mp3_info)

            if not mp3:
                mp3 = load_mp3(full_path, load_image=load_images)

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

    def __init__(self, directory: str, info: dict, load_images):
        super().__init__()
        self.directory = directory
        self.info = info
        self.load_images = load_images

    def run(self):
        # Fetch all the releases and releases tracks for the release groups
        debug(f"LOCALSONGS: load_mp3s: '{self.directory}'")

        load_mp3s(self.directory, info=self.info, mp3_loaded_callback=self._on_mp3_loaded, load_images=self.load_images)
        # TODO: sort?

    def _on_mp3_loaded(self, mp3: Mp3):
        self.mp3_loaded.emit(mp3)


def load_mp3s_background(directory,
                         info: dict=None,
                         mp3_loaded_callback=None, finished_callback=None,
                         load_images=True, priority=workers.Worker.PRIORITY_BELOW_NORMAL):
    worker = LoadMp3sWorker(directory, info=info, load_images=load_images)
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
            mp3.load_image()
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
