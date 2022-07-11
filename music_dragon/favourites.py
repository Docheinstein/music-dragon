from pathlib import Path
from typing import Optional

from music_dragon.log import debug
from music_dragon.utils import app_config_path

_favourites_path: Optional[Path] = None
favourites = set()


def initialize():
    global _favourites_path
    _favourites_path = app_config_path() / "favourites"
    if not _favourites_path.exists():
        debug("Creating favourites folder")
        _favourites_path.parent.mkdir(parents=True, exist_ok=True)
    debug(f"Favourites path: {_favourites_path}")

def set_favourite(artist: str, album: Optional[str], song: Optional[str], favourite: bool, save: bool=True):
    global favourites
    fav_string = _compute_favourite_string(artist, album, song)
    debug(f"{'Favourite' if favourite else 'Unfavourite'}: {fav_string}")
    if favourite:
        favourites.add(fav_string)
    else:
        try:
            favourites.remove(fav_string)
        except KeyError:
            pass
    if save:
        save_favourites()

def is_favourite(artist: str, album: str=None, song: str=None) -> bool:
    yes = _compute_favourite_string(artist, album, song) in favourites
    # debug(f"is_favourite(artist={artist},album={album},song={song})={yes}")
    return yes

def load_favourites():
    debug("Loading favourites...")
    if not _favourites_path.exists():
        return
    with _favourites_path.open("r") as f:
        for l in f:
            l = l.strip()
            favourites.add(l)
    debug(f"Favourite loaded, count={len(favourites)}")

def save_favourites():
    debug(f"Saving favourites ({len(favourites)})...")
    with _favourites_path.open("w") as f:
        for fav in favourites:
            f.write(f"{fav}\n")
    debug(f"Favourite saved")

def _compute_favourite_string(artist: str, album, song):
    fav_string = artist
    if album:
        fav_string += f"/{album}"
    if song:
        fav_string += f"/{song}"
    return fav_string