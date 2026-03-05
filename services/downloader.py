"""
Core download logic powered by yt-dlp.
Returns local file path + metadata.
"""
import asyncio
import os
import re
import time
import logging
from dataclasses import dataclass
from typing import Optional

import yt_dlp

from config import TEMP_DIR, DOWNLOAD_TIMEOUT

logger = logging.getLogger(__name__)

YOUTUBE_COOKIES   = "/app/cookies/youtube_cookies.txt"
INSTAGRAM_COOKIES = "/app/cookies/instagram_cookies.txt"

PLATFORM_PATTERNS = {
    "YouTube":   re.compile(r"(youtube\.com|youtu\.be)"),
    "TikTok":    re.compile(r"tiktok\.com"),
    "Instagram": re.compile(r"instagram\.com"),
}

YT_EXTRACTOR_ARGS = {
    "youtube": {
        "player_client": ["ios", "web"]
    }
}


def detect_platform(url: str) -> Optional[str]:
    for name, pattern in PLATFORM_PATTERNS.items():
        if pattern.search(url):
            return name
    return None


@dataclass
class VideoInfo:
    title: str
    duration: int
    thumbnail: Optional[str]
    platform: str
    url: str


@dataclass
class DownloadResult:
    file_path: str
    title: str
    is_audio: bool


def _fmt_duration(seconds) -> str:
    try:
        seconds = int(seconds or 0)
        if not seconds:
            return "неизвестно"
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
    except Exception:
        return "неизвестно"


def _cookies_for(url: str) -> Optional[str]:
    if "youtube" in url or "youtu.be" in url:
        if os.path.exists(YOUTUBE_COOKIES):
            return YOUTUBE_COOKIES
    if "instagram" in url:
        if os.path.exists(INSTAGRAM_COOKIES):
            return INSTAGRAM_COOKIES
    return None


async def fetch_info(url: str) -> VideoInfo:
    loop = asyncio.get_event_loop()

    def _extract():
        opts = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": True,
            "extractor_args": YT_EXTRACTOR_ARGS,
        }
        cookies = _cookies_for(url)
        if cookies:
            opts["cookiefile"] = cookies
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    info = await asyncio.wait_for(
        loop.run_in_executor(None, _extract), timeout=30
    )

    platform = detect_platform(url) or "Unknown"
    return VideoInfo(
        title=info.get("title", "Unknown"),
        duration=info.get("duration", 0),
        thumbnail=info.get("thumbnail"),
        platform=platform,
        url=url,
    )


def _build_video_opts(quality: str, out_template: str, url: str = "") -> dict:
    height = int(quality)
    opts = {
        "quiet": True,
        "noplaylist": True,
        "outtmpl": out_template,
        "extractor_args": YT_EXTRACTOR_ARGS,
        "format": (
            f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]"
            f"/bestvideo[height<={height}]+bestaudio"
            f"/best[height<={height}]"
            f"/best"
        ),
        "merge_output_format": "mp4",
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
    }
    cookies = _cookies_for(url)
    if cookies:
        opts["cookiefile"] = cookies
    return opts


def _build_audio_opts(out_template: str, url: str = "") -> dict:
    opts = {
        "quiet": True,
        "noplaylist": True,
        "outtmpl": out_template,
        "extractor_args": YT_EXTRACTOR_ARGS,
        "format": "bestaudio/best",
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ],
    }
    cookies = _cookies_for(url)
    if cookies:
        opts["cookiefile"] = cookies
    return opts


async def download_video(
    url: str,
    quality: str = "720",
    audio_only: bool = False,
    user_id: int = 0,
) -> DownloadResult:
    loop = asyncio.get_event_loop()
    ts = int(time.time())
    out_template = os.path.join(TEMP_DIR, f"{user_id}_{ts}.%(ext)s")

    if audio_only:
        opts = _build_audio_opts(out_template, url)
    else:
        opts = _build_video_opts(quality, out_template, url)

    def _download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "video")
            filename = ydl.prepare_filename(info)
            if audio_only:
                base = os.path.splitext(filename)[0]
                for ext in ("mp3", "m4a", "ogg", "opus"):
                    candidate = f"{base}.{ext}"
                    if os.path.exists(candidate):
                        return candidate, title
            else:
                base = os.path.splitext(filename)[0]
                for ext in ("mp4", "mkv", "webm"):
                    candidate = f"{base}.{ext}"
                    if os.path.exists(candidate):
                        return candidate, title
                if os.path.exists(filename):
                    return filename, title
            return filename, title

    file_path, title = await asyncio.wait_for(
        loop.run_in_executor(None, _download),
        timeout=DOWNLOAD_TIMEOUT,
    )

    return DownloadResult(file_path=file_path, title=title, is_audio=audio_only)


def cleanup(file_path: str) -> None:
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up: {file_path}")
    except Exception as e:
        logger.warning(f"Could not delete {file_path}: {e}")


