"""
Core download logic powered by yt-dlp.
Tries multiple YouTube clients in sequence until one works.
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

YT_CLIENTS = [
    ["android"],
    ["android_vr"],
    ["android_embedded"],
    ["ios"],
    ["web"],
    ["mweb"],
]


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


def _is_youtube(url: str) -> bool:
    return "youtube" in url or "youtu.be" in url


def _cookies_for(url: str) -> Optional[str]:
    if "instagram" in url:
        if os.path.exists(INSTAGRAM_COOKIES):
            return INSTAGRAM_COOKIES
    return None


def _make_opts(base: dict, url: str, client: list) -> dict:
    opts = dict(base)
    opts["extractor_args"] = {"youtube": {"player_client": client}}
    cookies = _cookies_for(url)
    if cookies:
        opts["cookiefile"] = cookies
    return opts


async def fetch_info(url: str) -> VideoInfo:
    loop = asyncio.get_event_loop()
    is_yt = _is_youtube(url)
    clients = YT_CLIENTS if is_yt else [["web"]]

    base_opts = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
    }

    last_error = None
    for client in clients:
        if is_yt:
            opts = _make_opts(base_opts, url, client)
        else:
            opts = dict(base_opts)
            cookies = _cookies_for(url)
            if cookies:
                opts["cookiefile"] = cookies

        def _extract(o=opts):
            with yt_dlp.YoutubeDL(o) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            info = await asyncio.wait_for(
                loop.run_in_executor(None, _extract), timeout=30
            )
            formats = info.get("formats") or []
            has_video = any(
                f.get("vcodec", "none") != "none" or f.get("acodec", "none") != "none"
                for f in formats
            )
            if not has_video and is_yt:
                logger.warning(f"Client {client} returned no formats, trying next...")
                last_error = "No video formats"
                continue

            platform = detect_platform(url) or "Unknown"
            logger.info(f"fetch_info success with client {client}")
            return VideoInfo(
                title=info.get("title", "Unknown"),
                duration=info.get("duration", 0),
                thumbnail=info.get("thumbnail"),
                platform=platform,
                url=url,
            )
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Client {client} failed: {e}")
            continue

    raise Exception(last_error or "All clients failed")


def _base_video_format(height: int) -> str:
    return (
        f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]"
        f"/bestvideo[height<={height}]+bestaudio"
        f"/best[height<={height}]"
        f"/best"
    )


async def download_video(
    url: str,
    quality: str = "720",
    audio_only: bool = False,
    user_id: int = 0,
) -> DownloadResult:
    loop = asyncio.get_event_loop()
    ts = int(time.time())
    out_template = os.path.join(TEMP_DIR, f"{user_id}_{ts}.%(ext)s")
    is_yt = _is_youtube(url)
    clients = YT_CLIENTS if is_yt else [["web"]]

    if audio_only:
        base_opts = {
            "quiet": True,
            "noplaylist": True,
            "outtmpl": out_template,
            "format": "bestaudio/best",
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ],
        }
    else:
        height = int(quality)
        base_opts = {
            "quiet": True,
            "noplaylist": True,
            "outtmpl": out_template,
            "format": _base_video_format(height),
            "merge_output_format": "mp4",
            "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
        }

    last_error = None
    for client in clients:
        if is_yt:
            opts = _make_opts(base_opts, url, client)
        else:
            opts = dict(base_opts)
            cookies = _cookies_for(url)
            if cookies:
                opts["cookiefile"] = cookies

        def _download(o=opts):
            with yt_dlp.YoutubeDL(o) as ydl:
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

        try:
            file_path, title = await asyncio.wait_for(
                loop.run_in_executor(None, _download),
                timeout=DOWNLOAD_TIMEOUT,
            )
            if file_path and os.path.exists(file_path):
                logger.info(f"download success with client {client}")
                return DownloadResult(file_path=file_path, title=title, is_audio=audio_only)
            last_error = "File not found after download"
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Download client {client} failed: {e}")
            continue

    raise Exception(last_error or "All download clients failed")


def cleanup(file_path: str) -> None:
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up: {file_path}")
    except Exception as e:
        logger.warning(f"Could not delete {file_path}: {e}")
