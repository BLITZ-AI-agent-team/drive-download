"""3-B Tier 1: TVer/ABEMA OBS自動録画 (Playwright + OBS WebSocket)"""

import os
import time
import logging
import subprocess
import json

logger = logging.getLogger("module3")

TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "temp_videos")


def start_obs_recording(output_path):
    """OBS WebSocketで録画を開始"""
    # obsws-pythonのログでパスワードが出力されるのを防ぐ
    logging.getLogger("obsws_python.reqs").setLevel(logging.WARNING)
    logging.getLogger("obsws_python.baseclient").setLevel(logging.WARNING)
    try:
        import obsws_python as obs
        client = obs.ReqClient(host="localhost", port=4455, password=os.getenv("OBS_WS_PASSWORD", ""))
        client.set_profile_parameter("Output", "FilePath", os.path.dirname(output_path))
        client.start_record()
        logger.info("OBS録画開始")
        return client
    except Exception as e:
        logger.error(f"OBS接続失敗: {e}")
        return None


def stop_obs_recording(client):
    """OBS WebSocketで録画を停止"""
    try:
        result = client.stop_record()
        logger.info(f"OBS録画停止: {result.output_path}")
        return result.output_path
    except Exception as e:
        logger.error(f"OBS録画停止失敗: {e}")
        return None


def record_tver(url, duration_sec=None):
    """TVerの番組をPlaywright + OBSで録画

    Args:
        url: TVerの番組URL
        duration_sec: 録画時間（秒）。Noneの場合は動画の長さに合わせる
    """
    os.makedirs(TEMP_DIR, exist_ok=True)
    output_path = os.path.join(TEMP_DIR, f"tver_{int(time.time())}.mp4")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("playwrightがインストールされていません: pip install playwright && playwright install")
        return None

    with sync_playwright() as p:
        # DRM対策: HWアクセラレーション無効
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-accelerated-video-decode",
            ],
        )
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        time.sleep(5)  # ページ読み込み待ち

        # 再生ボタンを押す（TVerのUI構造に依存）
        try:
            page.click('button[aria-label="再生"]', timeout=10000)
        except Exception:
            logger.info("再生ボタンが見つからない、自動再生の可能性")

        # OBS録画開始
        obs_client = start_obs_recording(output_path)
        if not obs_client:
            browser.close()
            return None

        # 録画待ち
        if duration_sec:
            logger.info(f"録画中... {duration_sec}秒待機")
            time.sleep(duration_sec)
        else:
            logger.info("録画中... 手動で停止してください（Ctrl+C）")
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                pass

        # OBS録画停止
        recorded_path = stop_obs_recording(obs_client)
        browser.close()

        if recorded_path and os.path.exists(recorded_path):
            logger.info(f"録画完了: {recorded_path}")
            return {
                "file_path": recorded_path,
                "url": url,
                "source": "tver",
            }

    return None


def record_abema(url, duration_sec=None):
    """ABEMAの番組をPlaywright + OBSで録画（TVerとほぼ同じフロー）"""
    os.makedirs(TEMP_DIR, exist_ok=True)
    output_path = os.path.join(TEMP_DIR, f"abema_{int(time.time())}.mp4")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("playwrightがインストールされていません")
        return None

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-accelerated-video-decode",
            ],
        )
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        time.sleep(5)

        obs_client = start_obs_recording(output_path)
        if not obs_client:
            browser.close()
            return None

        if duration_sec:
            logger.info(f"録画中... {duration_sec}秒待機")
            time.sleep(duration_sec)
        else:
            logger.info("録画中... 手動で停止してください（Ctrl+C）")
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                pass

        recorded_path = stop_obs_recording(obs_client)
        browser.close()

        if recorded_path and os.path.exists(recorded_path):
            logger.info(f"録画完了: {recorded_path}")
            return {
                "file_path": recorded_path,
                "url": url,
                "source": "abema",
            }

    return None


def watch_folder(folder_path, callback, interval=30):
    """手動配置フォルダを監視し、新しいファイルがあればコールバックを実行（Tier 3）"""
    os.makedirs(folder_path, exist_ok=True)
    processed = set()

    logger.info(f"フォルダ監視開始: {folder_path}")
    while True:
        for f in os.listdir(folder_path):
            full_path = os.path.join(folder_path, f)
            if full_path in processed:
                continue
            if not f.lower().endswith((".mp4", ".mov", ".mkv", ".avi")):
                continue
            # ファイルが書き込み中でないか確認
            try:
                size1 = os.path.getsize(full_path)
                time.sleep(2)
                size2 = os.path.getsize(full_path)
                if size1 != size2:
                    continue  # まだ書き込み中
            except OSError:
                continue

            logger.info(f"新規ファイル検出: {f}")
            processed.add(full_path)
            callback(full_path)

        time.sleep(interval)
