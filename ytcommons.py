import re

YOUTUBE_PLAYLIST_RE_1 = re.compile(r"(?:[a-z_:\/\.]+)youtube\.com\/watch\?v=(?:[0-9a-zA-Z_\-]+)&list=([0-9a-zA-Z_\-]+)")
YOUTUBE_PLAYLIST_RE_2 = re.compile(r"(?:[a-z_:\/\.]+)youtube\.com\/playlist\?list=([0-9a-zA-Z_\-]+)")
YOUTUBE_VIDEO_RE = re.compile(r"(?:[a-z_:\/\.]+)youtube\.com\/watch\?v=([0-9a-zA-Z_\-]+)")


def youtube_video_id_to_youtube_music_url(video_id: str):
    return f"https://music.youtube.com/watch?v={video_id}"

def youtube_video_id_to_youtube_url(video_id: str):
    return f"https://www.youtube.com/watch?v={video_id}"


def youtube_playlist_id_to_youtube_music_url(playlist_id: str):
    return f"https://music.youtube.com/playlist?list={playlist_id}"

def youtube_playlist_id_to_youtube_url(playlist_id: str):
    return f"https://www.youtube.com/playlist?list={playlist_id}"


def youtube_url_to_video_id(video_url: str):
    if is_youtube_playlist_url(video_url):
        return None # do no return anything if the url contains a playlist reference
    m = YOUTUBE_VIDEO_RE.match(video_url)
    if m and m.groups():
        return m.groups()[0]
    return None

def youtube_url_to_playlist_id(video_url: str):
    m1 = YOUTUBE_PLAYLIST_RE_1.match(video_url)
    if m1 and m1.groups():
        return m1.groups()[0]
    m2 = YOUTUBE_PLAYLIST_RE_2.match(video_url)
    if m2 and m2.groups():
        return m2.groups()[0]
    return None

def is_youtube_video_url(video_url: str):
    return True if youtube_url_to_video_id(video_url) else False

def is_youtube_playlist_url(video_url: str):
    return True if youtube_url_to_playlist_id(video_url) else False

def is_youtube_url(video_url: str):
    return True if (is_youtube_video_url(video_url) or is_youtube_playlist_url(video_url)) else False