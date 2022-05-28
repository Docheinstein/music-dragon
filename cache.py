from pathlib import Path
from typing import Optional

import json
import utils
from log import debug
from utils import app_cache_path, get_folder_size

_cache_path: Optional[Path] = None

_images_caching = False
_requests_caching = False

def initialize(images: bool, requests: bool):
    global _cache_path
    _cache_path = app_cache_path()
    if not _cache_path.exists():
        debug("Creating cache folder")
        _cache_path.mkdir(parents=True, exist_ok=True)
    enable_images_cache(images)
    enable_requests_cache(requests)

def enable_images_cache(enabled):
    global _images_caching
    _images_caching = enabled

def enable_requests_cache(enabled):
    global _requests_caching
    _requests_caching = enabled

def cache_size():
    return get_folder_size(_cache_path)

def clear():
    debug("Clearing cache")
    for f in _cache_path.iterdir():
        debug(f"Removing {f}")
        f.unlink()

# Image

def get_image(file: str) -> Optional[bytes]:
    global _cache_path, _images_caching
    if not _images_caching:
        return None
    p =  Path(_cache_path, file)
    if p.exists():
        debug(f"CACHE: loading image from {file}")
        with p.open("rb") as f:
            return f.read()
    return None

def put_image(file: str, data: bytes) -> Optional[bytes]:
    global _cache_path, _images_caching
    if not _images_caching:
        return None
    p = Path(_cache_path, file)
    debug(f"CACHE: writing image to {file}")
    with p.open("wb") as f:
        f.write(data)

# Request


def get_request(file: str) -> Optional[bytes]:
    global _cache_path, _requests_caching
    if not _requests_caching:
        return None
    p = Path(_cache_path, file)
    if p.exists():
        debug(f"CACHE: loading request from {file}")
        with p.open("r") as f:
            return json.load(f)
    return None


def put_request(file: str, data: dict) -> Optional[bytes]:
    global _cache_path, _images_caching
    if not _images_caching:
        return None
    p = Path(_cache_path, file)
    debug(f"CACHE: writing image to {file}")
    with p.open("w") as f:
        json.dump(data, f)
