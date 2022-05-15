import json
import os.path
import sys
from pathlib import Path
from typing import List, Optional

import eyed3
import youtube_dl
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool
from eyed3.core import AudioFile
from eyed3.id3 import Tag
from youtube_dl import YoutubeDL

import preferences
from entities import YtTrack
from log import debug
from utils import j

FRONT_COVER = 3


class TrackDownloaderSignals(QObject):
    started = pyqtSignal(YtTrack)
    progress = pyqtSignal(YtTrack, float)
    finished = pyqtSignal(YtTrack)


class TrackDownloaderRunnable(QRunnable):
    def __init__(self, track: YtTrack, output_directory, output_format):
        super().__init__()
        self.signals = TrackDownloaderSignals()
        self.track = track
        self.output_directory = output_directory
        self.output_format = output_format


    @pyqtSlot()
    def run(self) -> None:
        debug(f"[TrackDownloaderRunnable (track={self.track.video_title})]")

        self.signals.started.emit(self.track)

        class YoutubeDLLogger(object):
            def debug(self, msg):
                debug(msg)

            def warning(self, msg):
                print(f"WARN: {msg}")

            def error(self, msg):
                print(f"ERROR: {msg}", file=sys.stderr)

        def progress_hook(d):
            if "_percent_str" in d:
                self.signals.progress.emit(self.track, float(d["_percent_str"].strip("%")))

            # if d['status'] == 'finished':
            #     self.signals.finished.emit()

        # https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/YoutubeDL.py#L141
        debug(f"Directory: '{self.output_directory}'")

        outtmpl: str  = self.output_format
        debug(f"Output template before wildcards substitutions: '{outtmpl}'")

        outtmpl = outtmpl.replace("{artist}", self.track.mb_track.release.release_group.artists_string())
        outtmpl = outtmpl.replace("{album}", self.track.mb_track.release.release_group.title)
        outtmpl = outtmpl.replace("{song}", self.track.mb_track.title)
        outtmpl = outtmpl.replace("{ext}", "%(ext)s")

        debug(f"Output template after wildcards substitutions: '{outtmpl}'")

        outtmpl = os.path.join(self.output_directory, outtmpl)
        output = outtmpl.replace("%(ext)s", "mp3") # hack

        debug(f"Destination template: '{outtmpl}'")
        debug(f"Destination [real]: '{output}'")

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'logger': YoutubeDLLogger(),
            'progress_hooks': [progress_hook],
            'outtmpl': outtmpl
        }

        with YoutubeDL(ydl_opts) as ydl:
            yt_url = f'https://youtube.com/watch?v={self.track.video_id}'
            debug(f"Going to download from '{yt_url}'")

            # TODO: download speed up?
            ydl.download([yt_url])

            debug(f"Applying mp3 tags to {output}")

            try:
                f: AudioFile = eyed3.load(output)
                if f:
                    if not f.tag:
                        f.tag.initTag()

                    tag: eyed3.id3.Tag = f.tag
                    tag.artist = self.track.mb_track.release.release_group.artists_string()
                    tag.album = self.track.mb_track.release.release_group.title
                    tag.title = self.track.mb_track.title
                    tag.track_num = self.track.mb_track.track_number
                    # TODO: use better cover
                    tag.images.set(FRONT_COVER, self.track.mb_track.release.release_group.cover(), "image/jpeg")
                    tag.save()

                else:
                    print(f"WARN: failed to apply mp3 tags to {output}")

            except:
                print(f"WARN: failed to apply mp3 tags to {output}")



        self.signals.finished.emit(self.track)


class YtDownloader(QObject):
    track_download_started = pyqtSignal(YtTrack)
    track_download_progress = pyqtSignal(YtTrack, float)
    track_download_finished = pyqtSignal(YtTrack)

    def __init__(self):
        super().__init__()
        self.queue: List[YtTrack] = []
        # self.current_download_task: Optional[TrackDownloaderRunnable] = None

    def enqueue(self, yttrack: YtTrack):
        self.queue.append(yttrack)
        if len(self.queue) == 1:
            self.start_next_download()

    def start_next_download(self):
        debug("start_next_download")
        if self.queue:
            debug(f"start_next_download: downloading {self.queue[0].mb_track.title}")
            track_downloader_runnable = TrackDownloaderRunnable(
                self.queue[0],
                output_directory=preferences.directory(),
                output_format=preferences.output_format()
            )
            track_downloader_runnable.signals.started.connect(self.on_download_started)
            track_downloader_runnable.signals.progress.connect(self.on_download_progress)
            track_downloader_runnable.signals.finished.connect(self.on_download_finished)
            QThreadPool.globalInstance().start(track_downloader_runnable)
        else:
            debug("start_next_download: nothing to do")

    def on_download_started(self, track: YtTrack):
        debug(f"on_download_started(track={track.mb_track.title})")
        self.track_download_started.emit(track)

    def on_download_progress(self, track: YtTrack, progress: float):
        debug(f"on_download_progress(track={track.mb_track.title}, progress={progress})")
        self.track_download_progress.emit(track, progress)

    def on_download_finished(self, track: YtTrack):
        debug(f"on_download_finished(track={track.mb_track.title})")
        done = self.queue[0]
        assert(done.video_id == track.video_id)
        self.queue = self.queue[1:]
        self.track_download_finished.emit(track)
        self.start_next_download()
