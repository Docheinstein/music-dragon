# Music Dragon

Desktop application written in Python3 + PyQt5 with a spotify-likish interface that can be used to 
search artists, albums and songs and automatically download and tag those with one click.

Supports Linux and Windows (experimental).

### Features
- Search artists, albums or songs (`musicbrainz`)
- Automatically download single songs or entire albums from youtube with a single click (`youtube_dl`)
- Manually download any song or playlist from youtube by pasting its URL
- Automatically fetch images of songs and albums
- Automatically tag downloaded songs using musicbrainz and youtube metadata, with a configurable tagging pattern
- Show and manage local songs
- Automatically recognize whether songs and albums have already been downloaded
  (the border of the song/album's cover changes accordingly)
- Play songs, either locally or directly from youtube stream

### What it looks like

![Search](https://raw.githubusercontent.com/Docheinstein/music-dragon/master/img/screenshot-0.png "Search")
![Artist](https://raw.githubusercontent.com/Docheinstein/music-dragon/master/img/screenshot-1.png "Artist")
![Album](https://raw.githubusercontent.com/Docheinstein/music-dragon/master/img/screenshot-2.png "Album")
![Downloads](https://raw.githubusercontent.com/Docheinstein/music-dragon/master/img/screenshot-3.png "Downloads")

## INSTALLATION

#### Linux

```
pip install music-dragon
```

#### Windows

Using pip:

```
pip install music-dragon
```

Otherwise:

* Clone the repository
* Follow the instructions at .\other\pyinstaller_data\windows\README.txt:
  * Place the ffmpeg binaries (ffmpeg, ffplay, ffprobe) in .\other\pyinstaller_data\windows\ffmpeg
  * Place the content of the VLC folder in .\other\pyinstaller_data\windows\vlc
* Compile with .\scripts\build-windows-exe.cmd
* Run the executable in .\dist\main\main.exe

## USAGE
```
music-dragon
```

## TODO
* Improve UI
* Allow manual tagging of local songs (`eyed3`)
* Solve some known bugs
* Refactor