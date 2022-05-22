import json
import os.path
import sys

import eyed3
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from eyed3.core import AudioFile
from eyed3.id3 import Tag
from youtube_dl import YoutubeDL

import workers
from log import debug
from utils import j
from workers import Worker

MP3_IMAGE_TAG_INDEX_FRONT_COVER = 3


def yt_video_id_to_url(video_id: str):
    return f"https://youtube.com/watch?v={video_id}"

def yt_video_url_to_id(video_url: str):
    return video_url.split("=")[-1]

downloads = {}

def download_count():
    return len(downloads)

def get_download(video_id: str):
    return downloads.get(video_id)

class TrackDownloaderWorker(Worker):
    progress = pyqtSignal(str, float, str)
    download_finished = pyqtSignal(str, str)
    # download_error = pyqtSignal(str, str)
    conversion_finished = pyqtSignal(str, str)
    tagging_finished = pyqtSignal(str, str)

    def __init__(self,
                 video_id: str,
                 artist: str, album: str, song: str, track_num: int, image: bytes,
                 output_directory: str, output_format: str,
                 apply_tags=True, user_data=None):
        super().__init__()
        self.video_id = video_id
        self.artist = artist
        self.album = album
        self.song = song
        self.track_num = track_num
        self.image = image
        self.apply_tags = apply_tags
        self.user_data = user_data
        self.output_directory = output_directory
        self.output_format = output_format


    @pyqtSlot()
    def run(self) -> None:
        class YoutubeDLLogger(object):
            def debug(self, msg):
                debug(msg)

            def warning(self, msg):
                print(f"WARN: {msg}")

            def error(self, msg):
                print(f"ERROR: {msg}", file=sys.stderr)

        def progress_hook(d):
            if d["status"] == "downloading":
                debug("YOUTUBE_DL update: downloading")

                if "_percent_str" in d:
                    self.progress.emit(self.video_id, float(d["_percent_str"].strip("%")), self.user_data)

            if d["status"] == "finished":
                debug("YOUTUBE_DL update: finished")
                self.download_finished.emit(self.video_id, self.user_data)


            if d["status"] == "error":
                debug(f"YOUTUBE_DL update: error\n{j(d)}")
                # self.download_error.emit(self.video_id, self.user_data)


        # https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/YoutubeDL.py#L141
        debug(f"Output directory: '{self.output_directory}'")

        outtmpl: str  = self.output_format
        debug(f"Output template before wildcards substitutions: '{outtmpl}'")

        # Output format substitutions
        outtmpl = outtmpl.replace("{artist}", self.artist)
        outtmpl = outtmpl.replace("{album}", self.album)
        outtmpl = outtmpl.replace("{song}", self.song)
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
            'outtmpl': outtmpl,
            'ignoreerrors': True
        }

        with YoutubeDL(ydl_opts) as ydl:
            yt_url = yt_video_id_to_url(self.video_id)
            debug(f"Going to download from '{yt_url}'")

            # TODO: download speed up?
            ydl.download([yt_url])

            debug("Conversion completed")

            self.conversion_finished.emit(self.video_id, self.user_data)

            if self.apply_tags:
                debug(f"Applying mp3 tags to {output}")

                try:
                    f: AudioFile = eyed3.load(output)
                    if f:
                        if not f.tag:
                            f.tag.initTag()

                        tag: eyed3.id3.Tag = f.tag
                        if self.artist is not None:
                            tag.artist = self.artist
                        if self.album is not None:
                            tag.album = self.album
                        if self.song is not None:
                            tag.title = self.song
                        if self.track_num is not None:
                            tag.track_num = self.track_num
                        if self.image:
                            # TODO: use better cover
                            tag.images.set(MP3_IMAGE_TAG_INDEX_FRONT_COVER, self.image, "image/jpeg")
                        tag.save()
                        debug("Tagging completed")
                        self.tagging_finished.emit(self.video_id, self.user_data)
                    else:
                        print(f"WARN: failed to apply mp3 tags to {output}")
                except:
                    print(f"WARN: failed to apply mp3 tags to {output}")


def start_track_download(
        video_id: str,
        artist: str, album: str, song: str, track_num: int, image: bytes,
        output_directory: str, output_format: str,
        started_callback,
        progress_callback,
        finished_callback,
        apply_tags=True, user_data=None):

    worker = TrackDownloaderWorker(
        video_id, artist, album, song, track_num, image,
        output_directory, output_format,
        apply_tags, user_data)


    def internal_started_callback():
        v = downloads.get(video_id)
        if not v:
            print(f"WARN: no track with video id = {video_id} was in queue")
            return

        v["status"] = "downloading"
        started_callback(video_id, user_data)

    def internal_progress_callback(video_id_, progress, user_data_):
        v = downloads.get(video_id)
        if not v:
            print(f"WARN: no track with video id = {video_id} was in download")
            return
        v["progress"] = progress
        progress_callback(video_id_, progress, user_data_)

    def internal_finished_callback():
        try:
            downloads.pop(video_id)
        except ValueError:
            print(f"WARN: no track with video id = {video_id} was in download")
        finished_callback(video_id, user_data)

    worker.started.connect(internal_started_callback)
    worker.progress.connect(internal_progress_callback)
    worker.finished.connect(internal_finished_callback)

    downloads[video_id] = {
        "user_data": user_data,
        "status": "queued",
        "progress": 0,
    }
    for video_id, down in downloads.items():
        debug(f"{video_id}: {down['status']} ({down['progress']}%)")

    workers.execute(worker)


# class YtDownloader(QObject):
#     track_download_started = pyqtSignal(YtTrack)
#     track_download_progress = pyqtSignal(YtTrack, float)
#     track_download_finished = pyqtSignal(YtTrack)
#
#     def __init__(self):
#         super().__init__()
#         self.queue: List[YtTrack] = []
#         # self.current_download_task: Optional[TrackDownloaderRunnable] = None
#
#     def enqueue(self, yttrack: YtTrack):
#         self.queue.append(yttrack)
#         if len(self.queue) == 1:
#             self.start_next_download()
#
#     def start_next_download(self):
#         debug("start_next_download")
#         if self.queue:
#             debug(f"start_next_download: downloading {self.queue[0].mb_track.title}")
#             track_downloader_runnable = TrackDownloaderRunnable(
#                 self.queue[0],
#                 output_directory=preferences.directory(),
#                 output_format=preferences.output_format()
#             )
#             track_downloader_runnable.signals.started.connect(self.on_download_started)
#             track_downloader_runnable.signals.progress.connect(self.on_download_progress)
#             track_downloader_runnable.signals.finished.connect(self.on_download_finished)
#             QThreadPool.globalInstance().start(track_downloader_runnable)
#         else:
#             debug("start_next_download: nothing to do")
#
#     def on_download_started(self, track: YtTrack):
#         debug(f"on_download_started(track={track.mb_track.title})")
#         self.track_download_started.emit(track)
#
#     def on_download_progress(self, track: YtTrack, progress: float):
#         debug(f"on_download_progress(track={track.mb_track.title}, progress={progress})")
#         self.track_download_progress.emit(track, progress)
#
#     def on_download_finished(self, track: YtTrack):
#         debug(f"on_download_finished(track={track.mb_track.title})")
#         done = self.queue[0]
#         assert(done.video_id == track.video_id)
#         self.queue = self.queue[1:]
#         self.track_download_finished.emit(track)
#         self.start_next_download()
