"""3-A: YouTube検索 - キーワード検索 + チャンネル限定対応"""

import os
import logging
from googleapiclient.discovery import build

logger = logging.getLogger("module3")


class YouTubeSearcher:
    def __init__(self, api_key=None):
        from dotenv import load_dotenv
        load_dotenv()
        key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not key:
            raise ValueError("YOUTUBE_API_KEY が設定されていません")
        self.youtube = build("youtube", "v3", developerKey=key)

    def search(self, query, max_results=10, channel_id=None, order="relevance"):
        """キーワードで動画を検索

        Args:
            query: 検索キーワード
            max_results: 最大件数
            channel_id: チャンネルIDで限定（Noneなら全体検索）
            order: 並び順 (relevance, date, viewCount, rating)
        """
        params = {
            "q": query,
            "part": "snippet",
            "type": "video",
            "maxResults": max_results,
            "order": order,
        }
        if channel_id:
            params["channelId"] = channel_id

        response = self.youtube.search().list(**params).execute()
        results = []
        for item in response.get("items", []):
            snippet = item["snippet"]
            video_id = item["id"]["videoId"]
            results.append({
                "video_id": video_id,
                "title": snippet["title"],
                "channel": snippet["channelTitle"],
                "description": snippet["description"],
                "thumbnail": snippet["thumbnails"].get("high", {}).get("url", ""),
                "published_at": snippet["publishedAt"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
            })

        logger.info(f"検索完了: '{query}' → {len(results)}件")
        return results

    def get_channel_id(self, channel_name):
        """チャンネル名からチャンネルIDを取得"""
        response = self.youtube.search().list(
            q=channel_name, part="snippet", type="channel", maxResults=1
        ).execute()
        items = response.get("items", [])
        if items:
            return items[0]["snippet"]["channelId"]
        return None

    def get_video_details(self, video_id):
        """動画の詳細情報を取得（再生数、いいね数等）"""
        response = self.youtube.videos().list(
            id=video_id, part="snippet,statistics,contentDetails"
        ).execute()
        items = response.get("items", [])
        if not items:
            return None
        item = items[0]
        stats = item.get("statistics", {})
        return {
            "video_id": video_id,
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "view_count": int(stats.get("viewCount", 0)),
            "like_count": int(stats.get("likeCount", 0)),
            "duration": item["contentDetails"]["duration"],
            "url": f"https://www.youtube.com/watch?v={video_id}",
        }
