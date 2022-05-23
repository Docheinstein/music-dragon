import json
import os.path
import sys

import eyed3
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from eyed3.core import AudioFile
from eyed3.id3 import Tag
from youtube_dl import YoutubeDL

import preferences
import workers
from log import debug
from utils import j
from workers import Worker

MP3_IMAGE_TAG_INDEX_FRONT_COVER = 3
YOUTUBE_DL_MAX_DOWNLOAD_ATTEMPTS = 10

def yt_video_id_to_url(video_id: str):
    return f"https://youtube.com/watch?v={video_id}"

def yt_video_url_to_id(video_url: str):
    return video_url.split("=")[-1]

downloads = {}
finished_downloads = {}

def download_count():
    return len(downloads)

def get_download(video_id: str):
    return downloads.get(video_id)

def finished_download_count():
    return len(finished_downloads)

def get_finished_download(video_id: str):
    return finished_downloads.get(video_id)

class TrackDownloaderWorker(Worker):
    progress = pyqtSignal(str, float, str)
    error = pyqtSignal(str, str, str)
    # canceled = pyqtSignal(str, str)
    download_finished = pyqtSignal(str, str)
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

        def progress_hook(hook_info):
            if hook_info["status"] == "downloading":
                debug("YOUTUBE_DL update: downloading")

                if "_percent_str" in hook_info:
                    self.progress.emit(self.video_id, float(hook_info["_percent_str"].strip("%")), self.user_data)

            if hook_info["status"] == "finished":
                debug("YOUTUBE_DL update: finished")
                self.download_finished.emit(self.video_id, self.user_data)

            if hook_info["status"] == "error":
                debug(f"YOUTUBE_DL update: error\n{j(hook_info)}")
                self.error.emit(self.video_id, "ERROR", self.user_data)


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
            'cachedir': False,
            'verbose': True
            # 'ignoreerrors': True
        }

        # TODO: download speed up?

        last_error = None
        for attempt in range(YOUTUBE_DL_MAX_DOWNLOAD_ATTEMPTS):
            debug(f"Download attempt n. {attempt} for {self.video_id}")
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    yt_url = yt_video_id_to_url(self.video_id)
                    debug(f"Going to download from '{yt_url}'")

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
                return # download done
            except Exception as e:
                print(f"WARN: download attempt n. {attempt} failed for video {self.video_id}: {e}")
                last_error = e

        print(f"ERROR: all download attempts ({YOUTUBE_DL_MAX_DOWNLOAD_ATTEMPTS} "
              f"failed for video {self.video_id}: {last_error}", file=sys.stderr)
        self.error.emit(self.video_id, f"ERROR: {last_error}", self.user_data)

    def can_execute(self):
        down = downloads.get(self.video_id)
        if not down:
            print(f"WARN: no download waiting for video id {self.video_id}")
            return False

        down = downloads[self.video_id]
        if down["status"] != "queued":
            return False

        downloading_count = [d["status"] == "downloading" for d in downloads.values()].count(True)
        max_download_count = preferences.max_simultaneous_downloads()
        can = downloading_count < max_download_count
        debug(f"Checking whether can download {down['user_data']} with status {down['status']}: "
              f"{'yes' if can else 'no'} (was downloading {downloading_count} tracks, max is {max_download_count})")
        return can

    def is_canceled(self):
        down = downloads.get(self.video_id)
        return True if down is None else False # not found means canceled


def start_track_download(
        video_id: str,
        artist: str, album: str, song: str, track_num: int, image: bytes,
        output_directory: str, output_format: str,
        queued_callback,
        started_callback,
        progress_callback,
        finished_callback,
        error_callback,
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
            d = downloads.pop(video_id)
            d["status"] = "finished"
            finished_downloads[video_id] = d
        except KeyError:
            print(f"WARN: no track with video id = {video_id} was in download")
        finished_callback(video_id, user_data)

    def internal_error_callback(video_id_, error_msg, user_data_):
        try:
            d = downloads.pop(video_id)
            d["status"] = "finished"
            d["error"] = error_msg
            finished_downloads[video_id] = d
        except KeyError:
            print(f"WARN: no track with video id = {video_id} was in download")
        error_callback(video_id, error_msg, user_data)

    worker.started.connect(internal_started_callback)
    worker.progress.connect(internal_progress_callback)
    worker.finished.connect(internal_finished_callback)
    worker.error.connect(internal_error_callback)

    downloads[video_id] = {
        "user_data": user_data,
        "status": "queued",
        "progress": 0,
        "attempt": 0
    }
    for video_id, down in downloads.items():
        debug(f"{video_id}: {down['status']} ({down['progress']}%)")

    workers.schedule(worker, priority=workers.WorkerScheduler.PRIORITY_BELOW_NORMAL)

    # call directly
    queued_callback(video_id, user_data)

def stop_track_download(video_id: str):
    try:
        d = downloads.pop(video_id)
        d["status"] = "canceled"
    except KeyError:
        print(f"WARN: no track with video id = {video_id} was in download")