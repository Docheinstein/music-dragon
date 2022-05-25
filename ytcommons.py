import re

YOUTUBE_RE = re.compile(r"(?:[a-z_:\/\.]+)youtube\.com\/watch\?v=(\w+)(?:&list=(\w+)?)?")
# YOUTUBE_RE = re.compile(r"([a-z_:/.]+)youtube\.com/watch\?v=(\w+)(?:&list=(\w+)?)?")


def youtube_video_id_to_youtube_music_url(video_id: str):
    return f"https://music.youtube.com/watch?v={video_id}"

def youtube_video_id_to_youtube_url(video_id: str):
    return f"https://www.youtube.com/watch?v={video_id}"


def youtube_url_to_video_id(video_url: str):
    m = YOUTUBE_RE.match(video_url)
    if not m:
        return None
    if m.groups():
        return m.groups()[0]

def is_youtube_url(video_url: str):
    return True if youtube_url_to_video_id(video_url) else False