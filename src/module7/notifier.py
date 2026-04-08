"""Chatwork 通知クライアント"""

import os
import logging
import urllib.request
import urllib.parse
import json

logger = logging.getLogger("module7")


def notify_chatwork(message, room_id=None, api_token=None):
    """Chatwork APIでメッセージを送信"""
    token = api_token or os.getenv("CHATWORK_API_TOKEN")
    rid = room_id or os.getenv("CHATWORK_ROOM_ID")

    if not token or not rid:
        logger.warning("Chatwork通知スキップ: CHATWORK_API_TOKEN / CHATWORK_ROOM_ID 未設定")
        return False

    url = f"https://api.chatwork.com/v2/rooms/{rid}/messages"
    data = urllib.parse.urlencode({"body": message, "self_unread": 1}).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"X-ChatWorkToken": token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            logger.info(f"Chatwork通知送信完了 (status={resp.status})")
            return True
    except Exception as e:
        logger.error(f"Chatwork通知失敗: {e}")
        return False


def format_download_result(result):
    """ダウンロード結果を通知用メッセージにフォーマット"""
    status = "完了" if result.get("failed", 0) == 0 else "一部エラーあり"
    total_mb = result.get("total_bytes", 0) / 1024 / 1024

    lines = [
        f"[info][title]Module 7 - ダウンロード{status}[/title]",
        f"フォルダ: {result.get('folder_name', result.get('file_name', '不明'))}",
        f"DL: {result.get('downloaded', 0)}件 / スキップ: {result.get('skipped', 0)}件 / 失敗: {result.get('failed', 0)}件",
        f"合計: {total_mb:.1f} MB",
        f"保存先: {result.get('dest_path', '不明')}",
        "[/info]",
    ]
    return "\n".join(lines)
