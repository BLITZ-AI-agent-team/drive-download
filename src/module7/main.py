"""Module 7 CLI エントリポイント"""

import argparse
import logging
import os
import re
import sys
from datetime import datetime

from .downloader import download_folder, download_file
from .notifier import notify_chatwork, format_download_result


def setup_logging(log_dir=None):
    """日付別ログファイル + コンソール出力"""
    log_dir = log_dir or os.path.join(os.path.dirname(__file__), "..", "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"module7_{datetime.now():%Y-%m-%d}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def extract_id_from_url(url_or_id):
    """Google Drive URL からフォルダ/ファイル ID を抽出"""
    # folders/XXXX パターン
    m = re.search(r"folders/([a-zA-Z0-9_-]+)", url_or_id)
    if m:
        return m.group(1), "folder"

    # file/d/XXXX パターン
    m = re.search(r"file/d/([a-zA-Z0-9_-]+)", url_or_id)
    if m:
        return m.group(1), "file"

    # id=XXXX パターン
    m = re.search(r"id=([a-zA-Z0-9_-]+)", url_or_id)
    if m:
        return m.group(1), "unknown"

    # ID直接指定と仮定
    return url_or_id, "unknown"


def main():
    parser = argparse.ArgumentParser(description="Module 7 - Google Drive 選択的ダウンロード")
    parser.add_argument("target", help="Google DriveのフォルダURL、ファイルURL、またはID")
    parser.add_argument(
        "-d", "--dest",
        default=os.path.join(os.path.dirname(__file__), "..", "..", "downloads"),
        help="ローカル保存先ディレクトリ (デフォルト: プロジェクト/downloads/)",
    )
    parser.add_argument("--sa-key", help="サービスアカウントJSONのパス")
    parser.add_argument("--no-notify", action="store_true", help="Chatwork通知をスキップ")
    parser.add_argument("--log-dir", help="ログディレクトリ")
    args = parser.parse_args()

    setup_logging(args.log_dir)
    logger = logging.getLogger("module7")

    target_id, target_type = extract_id_from_url(args.target)
    dest = os.path.abspath(args.dest)
    logger.info(f"対象: {target_id} (type={target_type})")
    logger.info(f"保存先: {dest}")

    try:
        if target_type == "file":
            result = download_file(target_id, dest, args.sa_key)
        else:
            # folder or unknown → まずフォルダとして試行
            result = download_folder(target_id, dest, args.sa_key)

        logger.info(f"完了: DL={result['downloaded']} スキップ={result['skipped']} 失敗={result['failed']}")

        if not args.no_notify:
            msg = format_download_result(result)
            notify_chatwork(msg)

    except Exception as e:
        logger.error(f"致命的エラー: {e}", exc_info=True)
        if not args.no_notify:
            notify_chatwork(f"[info][title]Module 7 - エラー[/title]{e}[/info]")
        sys.exit(1)


if __name__ == "__main__":
    main()
