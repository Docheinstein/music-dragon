import os
import sys

from setuptools import setup, find_packages

from music_dragon import APP_NAME, APP_VERSION


def read(file_name):
    with open(os.path.join(os.path.dirname(__file__), file_name)) as f:
        return f.read()

print("setup.py prefix:", sys.prefix)


setup(
    name=APP_NAME,
    version=APP_VERSION,

    python_requires=">=3",

    packages=find_packages(),

    include_package_data=True,

    entry_points={
        'console_scripts': [
            'music-dragon = music_dragon.main:main',
        ]
    },

    # Dependencies
    install_requires=[
        "musicbrainzngs",
        "yt_dlp",
        "ytmusicapi",
        "python-vlc",
        "eyed3",
        "PyQt5",
        "wikidata",
        "requests",
        "levenshtein",
    ],

    # Metadata
    author="Stefano Dottore",
    author_email="docheinstein@gmail.com",
    description="All-in-one music manager: scrapes albums, artists and songs from musicbrainz and automatically download them from youtube.",
    long_description_content_type="text/markdown",
    long_description=read('README.md'),
    license="MIT",
    keywords="music manager youtube spotify musicbrainz musicbrainzngs tag cover eyed3 ytmusicapi youtube_dl",
    url="https://github.com/Docheinstein/music-dragon",
)
