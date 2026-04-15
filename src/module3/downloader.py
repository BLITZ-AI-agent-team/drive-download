"""3-B: 動画ダウンロード（yt-dlp）- YouTube / Vimeo 対応"""

import os
import logging
import yt_dlp

logger = logging.getLogger("module3")

TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "temp_videos")


def download_video(url, output_dir=None, quality="720p"):
    """URLから動画をダウンロードし、ローカルに一時保存する"""
    dest = output_dir or TEMP_DIR
    os.makedirs(dest, exist_ok=True)

    format_str = "bestvideo[height<=720]+bestaudio/best[height<=720]" if quality == "720p" else "bestvideo[height<=1080]+bestaudio/best[height<=1080]"

    ydl_opts = {
        "format": format_str,
        "outtmpl": os.path.join(dest, "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": False,
        "no_warnings": False,
        "extract_flat": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        # merge_output_format で mp4 にしているので拡張子を補正
        base, _ = os.path.splitext(file_path)
        mp4_path = base + ".mp4"
        actual_path = mp4_path if os.path.exists(mp4_path) else file_path

        result = {
            "file_path": actual_path,
            "title": info.get("title", ""),
            "url": url,
            "duration_sec": info.get("duration"),
            "channel": info.get("channel") or info.get("uploader", ""),
            "upload_date": info.get("upload_date", ""),
            "description": info.get("description", ""),
            "thumbnail": info.get("thumbnail", ""),
            "resolution": f"{info.get('width', '?')}x{info.get('height', '?')}",
            "file_size_bytes": os.path.getsize(actual_path) if os.path.exists(actual_path) else 0,
        }
        logger.info(f"ダウンロード完了: {result['title']} ({result['file_size_bytes'] / 1024 / 1024:.1f} MB)")
        return result


def download_playlist(playlist_url, output_dir=None, quality="720p", max_videos=None):
    """プレイリストから複数動画をダウンロード"""
    dest = output_dir or TEMP_DIR
    os.makedirs(dest, exist_ok=True)

    # まずプレイリスト情報を取得
    with yt_dlp.YoutubeDL({"extract_flat": True, "quiet": True}) as ydl:
        playlist_info = ydl.extract_info(playlist_url, download=False)

    entries = playlist_info.get("entries", [])
    if max_videos:
        entries = entries[:max_videos]

    results = []
    for i, entry in enumerate(entries):
        video_url = entry.get("url") or entry.get("webpage_url")
        if not video_url:
            continue
        logger.info(f"[{i + 1}/{len(entries)}] ダウンロード中...")
        try:
            result = download_video(video_url, dest, quality)
            results.append(result)
        except Exception as e:
            logger.error(f"スキップ: {entry.get('title', '不明')} - {e}")

    return results
