from pathlib import Path
from typing import Optional, Union

import json
from music_dragon.log import debug
from music_dragon.utils import app_cache_path, get_folder_size

_cache_path: Optional[Path] = None

_images_caching = False
_requests_caching = False
_localsongs_caching = False

_LOCALSONGS_CACHE_FILENAME = "localsongs"

# keep an in-memory list of the cached files, so that we don't even
# have to check whether a cache file exists on the disk
_available_cache_files = set()

def initialize(images: bool, requests: bool, localsongs: bool):
    global _cache_path
    _cache_path = app_cache_path()
    if not _cache_path.exists():
        debug("Creating cache folder")
        _cache_path.mkdir(parents=True, exist_ok=True)
    enable_images_cache(images)
    enable_requests_cache(requests)
    enable_localsongs_cache(localsongs)
    _load_cache()

def _load_cache():
    debug("Loading available cache files")
    for f in _cache_path.iterdir():
        debug(f"CACHE: add {str(f.absolute())}")
        _available_cache_files.add(str(f.absolute()))

def enable_images_cache(enabled):
    global _images_caching
    _images_caching = enabled

def enable_requests_cache(enabled):
    global _requests_caching
    _requests_caching = enabled

def enable_localsongs_cache(enabled):
    global _localsongs_caching
    _localsongs_caching = enabled

# Utility

def cache_size():
    return get_folder_size(_cache_path)

def clear():
    debug("Clearing cache")
    _available_cache_files.clear()
    for f in _cache_path.iterdir():
        debug(f"Removing {f}")
        f.unlink()

def has_file(file: str, lazy=True) -> bool:
    p = Path(_cache_path, file)
    path = str(p.absolute())
    if lazy:
        return path in _available_cache_files
    return path in _available_cache_files and p.is_file()

# Image

def get_image(file: str) -> Optional[bytes]:
    global _cache_path, _images_caching

    # check whether this type of caching is enabled
    if not _images_caching:
        return None
    # check whether the cache file should be there
    p = Path(_cache_path, file)
    path = str(p.absolute())
    if path not in _available_cache_files:
        debug(f"CACHE: miss image: {file}")
        return None # for sure is not on the disk
    # check whether the cache file is actually there
    if p.exists():
        debug(f"CACHE: hit image: {file}")
        with p.open("rb") as f:
            return f.read()
    debug(f"CACHE: miss image: {file}")
    return None

def put_image(file: str, data: bytes) -> Optional[bytes]:
    global _cache_path, _images_caching
    if not _images_caching:
        return None
    p = Path(_cache_path, file)
    path = str(p.absolute())
    debug(f"CACHE: put image: {file}")
    # write to disk
    if data:
        with p.open("wb") as f:
            f.write(data)
    else:
        p.touch() # null image
    # write to memory
    _available_cache_files.add(path)

# Request

def get_request(file: str) -> Optional[Union[list, dict]]:
    global _cache_path, _requests_caching
    # check whether this type of caching is enabled
    if not _requests_caching:
        return None
    # check whether the cache file should be there
    p = Path(_cache_path, file)
    path = str(p.absolute())
    if path not in _available_cache_files:
        debug(f"CACHE: miss request: {file}")
        return None # for sure is not on the disk
    # check whether the cache file is actually there
    if p.exists():
        debug(f"CACHE: hit request: {file}")
        with p.open("r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return None # null image
    debug(f"CACHE: miss request: {file}")
    return None


def put_request(file: str, data: Union[list, dict]):
    global _cache_path, _requests_caching
    if not _requests_caching:
        return None
    p = Path(_cache_path, file)
    path = str(p.absolute())
    debug(f"CACHE: put request: {file}")
    # write to disk
    with p.open("w") as f:
        json.dump(data, f)
    # write to memory
    _available_cache_files.add(path)


# Local songs

def get_localsongs() -> Optional[dict]:
    global _cache_path, _localsongs_caching
    # check whether this type of caching is enabled
    if not _localsongs_caching:
        return None
    # check whether the cache file should be there
    p = Path(_cache_path, _LOCALSONGS_CACHE_FILENAME)
    path = str(p.absolute())
    if path not in _available_cache_files:
        debug(f"CACHE: miss local songs: {_LOCALSONGS_CACHE_FILENAME}")
        return None # for sure is not on the disk
    # check whether the cache file is actually there
    if p.exists():
        debug(f"CACHE: hit local songs: {_LOCALSONGS_CACHE_FILENAME}")
        with p.open("r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return None # null image
    debug(f"CACHE: miss local songs: {_LOCALSONGS_CACHE_FILENAME}")
    return None


def put_localsongs(data: dict):
    global _cache_path, _localsongs_caching
    if not _localsongs_caching:
        return None
    p = Path(_cache_path, _LOCALSONGS_CACHE_FILENAME)
    path = str(p.absolute())
    debug(f"CACHE: put local songs: {_LOCALSONGS_CACHE_FILENAME}")
    # write to disk
    with p.open("w") as f:
        json.dump(data, f)
    # write to memory
    _available_cache_files.add(path)

def clear_localsongs():
    p = Path(_cache_path, _LOCALSONGS_CACHE_FILENAME)
    debug(f"CACHE: remove local songs: {_LOCALSONGS_CACHE_FILENAME}")
    p.unlink(missing_ok=True)