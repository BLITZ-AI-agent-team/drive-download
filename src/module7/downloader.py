"""選択的ダウンローダー - フォルダ階層を再現しながらDL"""

import os
import logging
from datetime import datetime, timezone

from .drive_client import DriveClient

logger = logging.getLogger("module7")

GOOGLE_DOCS_EXPORT = {
    "application/vnd.google-apps.document": ("application/pdf", ".pdf"),
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
    ),
    "application/vnd.google-apps.presentation": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pptx",
    ),
}


def _needs_download(local_path, remote_size, remote_modified):
    """差分チェック: ローカルファイルが存在し、サイズと更新日時が一致すればスキップ"""
    if not os.path.exists(local_path):
        return True
    local_size = os.path.getsize(local_path)
    if remote_size is not None and local_size != int(remote_size):
        return True
    local_mtime = datetime.fromtimestamp(os.path.getmtime(local_path), tz=timezone.utc)
    if remote_modified and remote_modified > local_mtime:
        return True
    return False


def _parse_modified_time(modified_time_str):
    """Google Drive の modifiedTime (RFC3339) をパース"""
    if not modified_time_str:
        return None
    return datetime.fromisoformat(modified_time_str.replace("Z", "+00:00"))


def download_folder(folder_id, dest_dir, service_account_path=None):
    """指定フォルダの中身を再帰的にDLし、フォルダ階層をローカルに再現する"""
    client = DriveClient(service_account_path)

    folder_meta = client.get_file_metadata(folder_id)
    folder_name = folder_meta["name"]
    root_dest = os.path.join(dest_dir, folder_name)
    os.makedirs(root_dest, exist_ok=True)

    logger.info(f"フォルダ '{folder_name}' のファイルリストを取得中...")
    files = client.list_folder_recursive(folder_id)
    logger.info(f"対象ファイル数: {len(files)}")

    stats = {"downloaded": 0, "skipped": 0, "failed": 0, "total_bytes": 0}

    for item in files:
        rel_path = item["_rel_path"]
        mime_type = item["mimeType"]

        # Google Docs系はエクスポート
        if mime_type in GOOGLE_DOCS_EXPORT:
            export_mime, ext = GOOGLE_DOCS_EXPORT[mime_type]
            local_path = os.path.join(root_dest, rel_path + ext)
            try:
                logger.info(f"エクスポート: {rel_path}{ext}")
                client.export_google_doc(item["id"], local_path, export_mime)
                stats["downloaded"] += 1
            except Exception as e:
                logger.error(f"エクスポート失敗: {rel_path} - {e}")
                stats["failed"] += 1
            continue

        # Google Docs系以外でサイズがないものはスキップ
        if mime_type.startswith("application/vnd.google-apps."):
            logger.warning(f"スキップ（未対応Google形式）: {rel_path} ({mime_type})")
            stats["skipped"] += 1
            continue

        local_path = os.path.join(root_dest, rel_path)
        remote_size = item.get("size")
        remote_modified = _parse_modified_time(item.get("modifiedTime"))

        if not _needs_download(local_path, remote_size, remote_modified):
            logger.info(f"スキップ（差分なし）: {rel_path}")
            stats["skipped"] += 1
            continue

        try:
            size_mb = int(remote_size) / 1024 / 1024 if remote_size else 0
            logger.info(f"ダウンロード: {rel_path} ({size_mb:.1f} MB)")
            client.download_file(item["id"], local_path)
            stats["downloaded"] += 1
            stats["total_bytes"] += int(remote_size) if remote_size else 0
        except Exception as e:
            logger.error(f"ダウンロード失敗: {rel_path} - {e}")
            stats["failed"] += 1

    return {
        "folder_name": folder_name,
        "dest_path": root_dest,
        **stats,
        "total_files": len(files),
    }


def download_file(file_id, dest_dir, service_account_path=None):
    """単一ファイルをDL"""
    client = DriveClient(service_account_path)
    meta = client.get_file_metadata(file_id)
    local_path = os.path.join(dest_dir, meta["name"])

    remote_modified = _parse_modified_time(meta.get("modifiedTime"))
    if not _needs_download(local_path, meta.get("size"), remote_modified):
        logger.info(f"スキップ（差分なし）: {meta['name']}")
        return {"downloaded": 0, "skipped": 1, "failed": 0, "file_name": meta["name"]}

    os.makedirs(dest_dir, exist_ok=True)
    client.download_file(file_id, local_path)
    logger.info(f"ダウンロード完了: {meta['name']}")
    return {"downloaded": 1, "skipped": 0, "failed": 0, "file_name": meta["name"]}
