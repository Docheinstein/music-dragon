import json
import os.path
import sys
from pathlib import Path

import eyed3
import youtube_dl
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from eyed3.core import AudioFile
from eyed3.id3 import Tag
from youtube_dl import YoutubeDL

import preferences
import workers
import ytcommons
from log import debug
from utils import j, sanitize_filename
from workers import Worker

MP3_IMAGE_TAG_INDEX_FRONT_COVER = 3
YOUTUBE_DL_MAX_DOWNLOAD_ATTEMPTS = 10


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

def ytdl_download(ytdl, url_list):
    """Download a given list of URLs."""
    outtmpl = ytdl.params.get('outtmpl', youtube_dl.DEFAULT_OUTTMPL)
    if (len(url_list) > 1
            and outtmpl != '-'
            and '%' not in outtmpl
            and ytdl.params.get('max_downloads') != 1):
        raise youtube_dl.SameFileError(outtmpl)

    res = None

    for url in url_list:
        try:
            # It also downloads the videos
            res = ytdl.extract_info(
                url, force_generic_extractor=ytdl.params.get('force_generic_extractor', False))
        except youtube_dl.utils.UnavailableVideoError:
            ytdl.report_error('unable to download video')
        except youtube_dl.MaxDownloadsReached:
            ytdl.to_screen('[info] Maximum number of downloaded files reached.')
            raise
        else:
            if ytdl.params.get('dump_single_json', False):
                ytdl.to_stdout(json.dumps(res))

    res["_filename"] = ytdl.prepare_filename(res) # as performed internally
    return res

class CancelException(Exception):
    def __init__(self):
        super(CancelException, self).__init__("canceled by user")

# ============= TRACK DOWNLOADER ============
# Download youtube track
# =========================================

class TrackDownloaderWorker(Worker):
    progress = pyqtSignal(str, float, str)
    error = pyqtSignal(str, str, str)
    output_destination_known = pyqtSignal(str, str, str)
    download_finished = pyqtSignal(str, str)
    conversion_finished = pyqtSignal(str, str)
    tagging_finished = pyqtSignal(str, str)

    def __init__(self,
                 video_id: str,
                 artist: str, album: str, song: str, track_num: int, image: bytes,
                 output_directory: str, output_format: str,
                 metadata=True, user_data=None):
        super().__init__()
        self.video_id = video_id
        self.artist = artist
        self.album = album
        self.song = song
        self.track_num = track_num
        self.image = image
        self.metadata = metadata
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
            if self.is_canceled:
                debug("YOUTUBE_DL hook invoked while worker is canceled: raising CancelException")
                raise CancelException()

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
        if self.metadata is True:
            outtmpl = outtmpl.replace("{artist}", sanitize_filename(self.artist))
            outtmpl = outtmpl.replace("{album}", sanitize_filename(self.album))
            outtmpl = outtmpl.replace("{song}", sanitize_filename(self.song))

        outtmpl = outtmpl.replace("{ext}", "%(ext)s")

        debug(f"Output template after wildcards substitutions: '{outtmpl}'")

        outtmpl = os.path.join(self.output_directory, outtmpl)

        debug(f"Destination template: '{outtmpl}'")
        # debug(f"Destination [real]: '{output}'")

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
            'verbose': True,
            # 'writeinfojson': self.metadata == "auto"
        }

        # TODO: download speed up?

        last_error = None
        for attempt in range(YOUTUBE_DL_MAX_DOWNLOAD_ATTEMPTS):
            debug(f"Download attempt n. {attempt} for {self.video_id}")
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    yt_url = ytcommons.youtube_video_id_to_youtube_url(self.video_id)
                    debug(f"Going to download from '{yt_url}'")

                    debug(f"YOUTUBE_DL: download: '{self.video_id}'")
                    result = ytdl_download(ydl, [yt_url])
                    debug(
                        "=== ytdl_download ==="
                        f"{j(result)}"
                        "======================"
                    )

                    output = str(Path(result['_filename']).with_suffix(".mp3").absolute())
                    debug(f"Download destination: {output}")
                    self.output_destination_known.emit(self.video_id, output, self.user_data)

                    debug("Conversion completed")

                    self.conversion_finished.emit(self.video_id, self.user_data)

                    if self.metadata is True:
                        artist = self.artist
                        album = self.album
                        song = self.song
                        track_num = self.track_num
                        image = self.image

                        debug(f"Applying mp3 tags to {output}\n"
                              f"artist={artist}"
                              f"album={album}"
                              f"song={song}"
                              f"track_num={track_num}"
                              f"image={'yes' if image else 'no'}"
                          )

                        try:
                            f: AudioFile = eyed3.load(output)
                            if f:
                                if not f.tag:
                                    f.tag.initTag()

                                tag: eyed3.id3.Tag = f.tag
                                if artist is not None:
                                    tag.artist = artist
                                if album is not None:
                                    tag.album = album
                                if song is not None:
                                    tag.title = song
                                if track_num is not None:
                                    tag.track_num = track_num
                                if image:
                                    tag.images.set(MP3_IMAGE_TAG_INDEX_FRONT_COVER, image, "image/jpeg")
                                tag.save()
                                debug("Tagging completed")
                                self.tagging_finished.emit(self.video_id, self.user_data)
                            else:
                                print(f"WARN: failed to apply mp3 tags to {output}: cannot load mp3")
                        except Exception as e:
                            print(f"WARN: failed to apply mp3 tags to {output}: {e}")
                return # download done

            except CancelException as ce:
                print(f"WARN: cancel request received during attempt n. {attempt} for video {self.video_id}")
                return

            except Exception as e:
                print(f"WARN: download attempt n. {attempt} failed for video {self.video_id}: {e}")
                last_error = e

        print(f"ERROR: all download attempts ({YOUTUBE_DL_MAX_DOWNLOAD_ATTEMPTS} "
              f"failed for video {self.video_id}: {last_error}", file=sys.stderr)
        self.error.emit(self.video_id, f"ERROR: {last_error}", self.user_data)

    def can_execute(self):
        # Can execute only if there are less running (or dispatched) workers than max_simultaneous_downloads
        # This would be enough if the workers_scheduler would schedule the jobs
        # as a queue, but since the jobs are scheduled as a stack (on purpose)#
        # we have to return True only if this worker is actually the earlier one

        earlier_worker = None
        downloading_count = 0
        for w in workers.worker_scheduler.workers.values():
            if isinstance(w, TrackDownloaderWorker):
                if w.status == Worker.STATUS_WAITING and (earlier_worker is None or w.born < earlier_worker.born):
                    earlier_worker = w

                if w.status == Worker.STATUS_DISPATCHED or w.status == Worker.STATUS_RUNNING:
                    downloading_count += 1

        max_download_count = preferences.max_simultaneous_downloads()
        can = downloading_count < max_download_count and earlier_worker.worker_id == self.worker_id
        debug(f"Checking whether can download track: "
              f"{'yes' if can else 'no'} (dispatched/running workers {downloading_count}, max is {max_download_count}, born = {self.born})")

        return can

def enqueue_track_download(
        video_id: str,
        artist: str, album: str, song: str, track_num: int, image: bytes,
        output_directory: str, output_format: str,
        queued_callback,
        started_callback,
        progress_callback,
        finished_callback,
        canceled_callback,
        error_callback,
        metadata=True, user_data=None):

    worker = TrackDownloaderWorker(
        video_id, artist, album, song, track_num, image,
        output_directory, output_format,
        metadata, user_data)
    worker.priority = Worker.PRIORITY_BELOW_NORMAL

    def internal_started_callback():
        d = downloads.get(video_id)
        if not d:
            print(f"WARN: no track with video id = {video_id} was in queue")
            return

        d["status"] = "downloading"
        if started_callback:
            started_callback(video_id, user_data)

    def internal_progress_callback(video_id_, progress, user_data_):
        d = downloads.get(video_id)
        if not d:
            print(f"WARN: no track with video id = {video_id} was in download")
            return
        d["progress"] = progress
        if progress_callback:
            progress_callback(video_id_, progress, user_data_)

    def internal_output_destination_known_callback(video_id_, output, user_data_):
        d = downloads.get(video_id)
        if not d:
            print(f"WARN: no track with video id = {video_id} was in download")
            return

        d["file"] = output

    def internal_finished_callback():
        file = None
        try:
            d = downloads.pop(video_id)
            d["status"] = "finished"
            file = d["file"]
            finished_downloads[video_id] = d
        except KeyError:
            print(f"WARN: no track with video id = {video_id} was in download")
        if finished_callback:
            finished_callback(video_id, file, user_data)

    def internal_canceled_callback():
        try:
            d = downloads.pop(video_id)
            d["status"] = "canceled"
        except KeyError:
            print(f"WARN: no track with video id = {video_id} was in download")
        if canceled_callback:
            canceled_callback(video_id, user_data)

    def internal_error_callback(video_id_, error_msg, user_data_):
        try:
            d = downloads.pop(video_id)
            d["status"] = "finished"
            d["error"] = error_msg
            finished_downloads[video_id] = d
        except KeyError:
            print(f"WARN: no track with video id = {video_id} was in download")
        if error_callback:
            error_callback(video_id, error_msg, user_data)

    worker.started.connect(internal_started_callback)
    worker.progress.connect(internal_progress_callback)
    worker.output_destination_known.connect(internal_output_destination_known_callback)
    worker.finished.connect(internal_finished_callback)
    worker.canceled.connect(internal_canceled_callback)
    worker.error.connect(internal_error_callback)

    downloads[video_id] = {
        "user_data": user_data,
        "status": "queued",
        "progress": 0,
        "attempt": 0,
        "worker": worker
    }
    for video_id, down in downloads.items():
        debug(f"{video_id}: {down['status']} ({down['progress']}%)")

    workers.schedule(worker)

    # call directly
    if queued_callback:
        queued_callback(video_id, user_data)

def cancel_track_download(video_id: str):
    d = downloads.get(video_id)
    if not d:
        print(f"WARN: no track with video id = {video_id} found")
        return
    d["worker"].cancel()

# ============= TRACK INFO FETCHER ============
# Fetch track info
# =========================================

class TrackInfoFetcherWorker(Worker):
    result = pyqtSignal(str, dict, str)

    def __init__(self, video_id: str, user_data=None):
        super().__init__()
        self.video_id = video_id
        self.user_data = user_data

    @pyqtSlot()
    def run(self) -> None:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'verbose': True,
        }

        # TODO: download speed up?

        last_error = None
        for attempt in range(YOUTUBE_DL_MAX_DOWNLOAD_ATTEMPTS):
            debug(f"Retrieval attempt n. {attempt} for {self.video_id}")
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    yt_url = ytcommons.youtube_video_id_to_youtube_url(self.video_id)
                    debug(f"YOUTUBE_DL: extract_info: '{self.video_id}'")
                    info = ydl.extract_info(yt_url, download=False)
                    debug(
                        "=== extract_info ==="
                        f"{j(info)}"
                        "======================"
                    )

                    self.result.emit(self.video_id, info, self.user_data)
                    return  # done
            except CancelException as ce:
                print(f"WARN: cancel request received during retrieval n. {attempt} for video {self.video_id}")
                return

            except Exception as e:
                print(f"WARN: retrieval attempt n. {attempt} failed for video {self.video_id}: {e}")
                last_error = e

        print(f"ERROR: all retrieval attempts ({YOUTUBE_DL_MAX_DOWNLOAD_ATTEMPTS} "
              f"failed for video {self.video_id}: {last_error}", file=sys.stderr)
        # self.error.emit(self.video_id, f"ERROR: {last_error}", self.user_data)

def fetch_track_info(video_id: str, callback, user_data=None):
    worker = TrackInfoFetcherWorker(video_id, user_data)
    worker.priority = Worker.PRIORITY_BELOW_NORMAL
    worker.result.connect(callback)
    workers.schedule(worker)
