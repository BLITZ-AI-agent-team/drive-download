"""Module 3 CLIエントリポイント"""

import argparse
import logging
import os
import sys

from .downloader import download_video, download_playlist
from .analyzer import run_pipeline
from .searcher import YouTubeSearcher
from .library import search_combined


def setup_logging(log_dir=None):
    log_dir = log_dir or os.path.join(os.path.dirname(__file__), "..", "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    from datetime import datetime
    log_file = os.path.join(log_dir, f"module3_{datetime.now():%Y-%m-%d}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def cmd_search(args):
    """YouTube検索"""
    searcher = YouTubeSearcher()
    results = searcher.search(args.query, max_results=args.max, channel_id=args.channel)
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r['title']}")
        print(f"    チャンネル: {r['channel']}")
        print(f"    URL: {r['url']}")
        print(f"    サムネイル: {r['thumbnail']}")


def cmd_download(args):
    """動画ダウンロード → 解析パイプライン実行"""
    logger = logging.getLogger("module3")
    result = download_video(args.url, quality=args.quality)
    logger.info(f"DL完了: {result['title']}")

    if not args.no_analyze:
        logger.info("解析パイプライン開始...")
        analysis = run_pipeline(result["file_path"], metadata=result)
        if analysis:
            logger.info(f"解析完了: {analysis['scenes']}シーン")


def cmd_analyze(args):
    """既存の動画ファイルを解析"""
    run_pipeline(args.file)


def cmd_library(args):
    """ライブラリ検索"""
    results = search_combined(
        query=args.query,
        keyword=args.keyword,
    )
    for search_type, items in results.items():
        print(f"\n=== {search_type} ===")
        for i, r in enumerate(items, 1):
            print(f"[{i}] {r['file_name']} ({r.get('start_tc', '')} - {r.get('end_tc', '')})")
            print(f"    {r.get('text', '')[:100]}")
            if r.get("similarity"):
                print(f"    類似度: {r['similarity']}")


def main():
    parser = argparse.ArgumentParser(description="Module 3 - 参考動画リサーチ・解析")
    sub = parser.add_subparsers(dest="command")

    # search
    p_search = sub.add_parser("search", help="YouTube検索")
    p_search.add_argument("query", help="検索キーワード")
    p_search.add_argument("--max", type=int, default=10, help="最大件数")
    p_search.add_argument("--channel", help="チャンネルID（限定検索）")

    # download
    p_dl = sub.add_parser("download", help="動画をDL＋解析")
    p_dl.add_argument("url", help="動画URL")
    p_dl.add_argument("--quality", default="720p", choices=["720p", "1080p"])
    p_dl.add_argument("--no-analyze", action="store_true", help="解析をスキップ")

    # analyze
    p_analyze = sub.add_parser("analyze", help="既存動画を解析")
    p_analyze.add_argument("file", help="動画ファイルパス")

    # library
    p_lib = sub.add_parser("library", help="ライブラリ検索")
    p_lib.add_argument("--query", help="自然言語検索")
    p_lib.add_argument("--keyword", help="キーワード検索")

    args = parser.parse_args()
    setup_logging()

    if args.command == "search":
        cmd_search(args)
    elif args.command == "download":
        cmd_download(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "library":
        cmd_library(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
