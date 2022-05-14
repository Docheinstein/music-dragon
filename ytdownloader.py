import sys
from pathlib import Path
from typing import List, Optional

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool
from youtube_dl import YoutubeDL

import preferences
from entities import YtTrack
from log import debug


class TrackDownloaderSignals(QObject):
    started = pyqtSignal(YtTrack)
    progress = pyqtSignal(YtTrack, float)
    finished = pyqtSignal(YtTrack)


class TrackDownloaderRunnable(QRunnable):
    def __init__(self, track: YtTrack):
        super().__init__()
        self.signals = TrackDownloaderSignals()
        self.track = track

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
        directory = preferences.directory()
        debug(f"Directory: {directory}")

        output = str(Path(directory,
                      f"{self.track.mb_track.release.release_group.artists_string()}",
                      f"{self.track.mb_track.release.release_group.title}",
                      f"{self.track.mb_track.title}.%(ext)s"))

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'logger': YoutubeDLLogger(),
            'progress_hooks': [progress_hook],
            'outtmpl': output
        }

        with YoutubeDL(ydl_opts) as ydl:
            yt_url = f'https://youtube.com/watch?v={self.track.video_id}'
            debug(f"Going to download from '{yt_url}'; destination: '{output}'")
            ydl.download([yt_url])

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
            track_downloader_runnable = TrackDownloaderRunnable(self.queue[0])
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
