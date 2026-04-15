"""3-C: 解析パイプライン - シーン分割 → 文字起こし → タグ付け → DB保存"""

import os
import sys
import logging
import subprocess
import json
from datetime import datetime

logger = logging.getLogger("module3")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.shared.db.client import DirectionDB
from src.shared.embedding import get_embedding


def detect_scenes(video_path, threshold=27.0):
    """PySceneDetectでシーン分割し、各シーンの開始/終了タイムコードを返す"""
    from scenedetect import detect, ContentDetector
    scene_list = detect(video_path, ContentDetector(threshold=threshold))
    scenes = []
    for i, (start, end) in enumerate(scene_list):
        scenes.append({
            "scene_index": i + 1,
            "start_sec": start.get_seconds(),
            "end_sec": end.get_seconds(),
            "start_tc": str(start),
            "end_tc": str(end),
            "duration_sec": end.get_seconds() - start.get_seconds(),
        })
    logger.info(f"シーン検出完了: {len(scenes)}シーン")
    return scenes


def extract_audio(video_path, output_path=None):
    """FFmpegで音声を抽出（16kHz モノラル WAV）"""
    if output_path is None:
        base, _ = os.path.splitext(video_path)
        output_path = base + "_audio.wav"
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        output_path,
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    logger.info(f"音声抽出完了: {output_path}")
    return output_path


def transcribe_audio(audio_path):
    """FFmpeg内蔵Whisperで音声を文字起こし（ローカル処理、API不要）"""
    WHISPER_MODEL = os.path.join(os.path.dirname(__file__), "..", "..", "models", "ggml-small.bin")

    if not os.path.exists(WHISPER_MODEL):
        logger.error(f"Whisperモデルが見つかりません: {WHISPER_MODEL}")
        return []

    output_json = audio_path + ".whisper.json"

    # WindowsのドライブレターのコロンがFFmpegフィルタセパレータと衝突するため
    # カレントディレクトリからの相対パスを使用する
    cwd = os.getcwd()
    try:
        work_dir = os.path.dirname(os.path.abspath(audio_path))
        os.chdir(work_dir)
        rel_audio = os.path.basename(audio_path)
        rel_model = os.path.relpath(WHISPER_MODEL, work_dir).replace("\\", "/")
        rel_output = os.path.basename(output_json)

        cmd = f"""ffmpeg -y -i "{rel_audio}" -af "whisper=model='{rel_model}':language=ja:format=json:destination='{rel_output}'" -f null - 2>NUL"""
        ret = os.system(cmd)
    finally:
        os.chdir(cwd)

    abs_output = os.path.join(work_dir, rel_output)
    if ret != 0 or not os.path.exists(abs_output):
        logger.error("Whisper文字起こし失敗")
        return []

    # JSON出力を読み込み
    segments = []
    with open(abs_output, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                seg = json.loads(line)
                segments.append({
                    "start_sec": seg.get("start", 0) / 1000.0,
                    "end_sec": seg.get("end", 0) / 1000.0,
                    "text": seg.get("text", "").strip(),
                })
            except json.JSONDecodeError:
                continue

    # 一時ファイル削除
    os.remove(abs_output)
    logger.info(f"文字起こし完了（Whisperローカル）: {len(segments)}セグメント")
    return segments


def extract_grid_image(video_path, start_sec, end_sec, output_path, cols=4, rows=4):
    """シーンから4x4グリッド画像を生成"""
    duration = end_sec - start_sec
    if duration <= 0:
        return None

    n_frames = cols * rows
    interval = duration / (n_frames + 1)

    frames = []
    for i in range(n_frames):
        t = start_sec + interval * (i + 1)
        frame_path = output_path.replace(".jpg", f"_frame_{i}.jpg")
        cmd = [
            "ffmpeg", "-y", "-ss", str(t), "-i", video_path,
            "-frames:v", "1", "-q:v", "3", frame_path,
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0 and os.path.exists(frame_path):
            frames.append(frame_path)

    if not frames:
        return None

    # ImageMagickまたはPILでグリッド合成
    try:
        from PIL import Image
        images = [Image.open(f) for f in frames]
        w, h = images[0].size
        grid = Image.new("RGB", (w * cols, h * rows))
        for idx, img in enumerate(images):
            x = (idx % cols) * w
            y = (idx // cols) * h
            grid.paste(img.resize((w, h)), (x, y))
        grid.save(output_path, quality=85)
        # 一時フレームを削除
        for f in frames:
            os.remove(f)
        logger.info(f"グリッド画像生成: {output_path}")
        return output_path
    except ImportError:
        logger.warning("PILがありません。グリッド画像生成をスキップ")
        return frames[0] if frames else None


def auto_tag_scene(grid_image_path, transcript_text, max_retries=3):
    """Geminiでシーンにタグを自動付与（リトライ付き）"""
    import time as _time
    import google.genai as genai
    from dotenv import load_dotenv
    load_dotenv()

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    contents = []
    if grid_image_path and os.path.exists(grid_image_path):
        img_file = client.files.upload(file=grid_image_path)
        contents.append(img_file)

    prompt = f"""この映像シーンを分析し、以下のカテゴリでタグを付けてください。
JSON形式で出力してください。各カテゴリに1〜3個のタグを付けてください。

カテゴリ:
- composition: シーンの構成（例: オープニング, エンディング, 場面転換, 対談, 人物紹介, プロフィール, 解説）
- direction: 演出手法（例: テロップ多め, 図解, グラフ解説, 写真挿入, ナレーション, インタビュー）
- mood: 雰囲気（例: 派手, 落ち着き, 緊張感, コミカル, 感動的, クール）
- telop_style: テロップスタイル（例: ポップ, シンプル, ニュース風, バラエティ風, なし）
- camera_work: カメラワーク（例: 固定, パン, ズーム, 引き, 寄り, 俯瞰, 手持ち）

文字起こし: {transcript_text[:500] if transcript_text else 'なし'}

出力形式:
{{"composition": ["タグ1"], "direction": ["タグ1", "タグ2"], "mood": ["タグ1"], "telop_style": ["タグ1"], "camera_work": ["タグ1"]}}
"""
    contents.append(prompt)

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=contents)
            text = response.text if response.text else ""
            if not text:
                logger.warning("Gemini応答が空でした")
                return {}
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            tags = json.loads(text.strip())
            logger.info(f"タグ付け完了: {tags}")
            return tags
        except json.JSONDecodeError:
            logger.warning(f"タグJSON解析失敗: {text[:200]}")
            return {}
        except Exception as e:
            wait = (attempt + 1) * 10
            logger.warning(f"Gemini API エラー（リトライ {attempt+1}/{max_retries}、{wait}秒待機）: {e}")
            _time.sleep(wait)

    logger.error("タグ付け: 最大リトライ回数超過")
    return {}


def run_pipeline(video_path, metadata=None):
    """解析パイプライン全体を実行

    Args:
        video_path: 動画ファイルのパス
        metadata: 追加メタデータ (title, url, channel, upload_date 等)
    """
    metadata = metadata or {}
    file_name = os.path.basename(video_path)
    grids_dir = os.path.join(os.path.dirname(video_path), "grids")
    os.makedirs(grids_dir, exist_ok=True)

    logger.info(f"=== 解析開始: {file_name} ===")

    # 1. DB登録
    db = DirectionDB()
    db.connect()

    asset = db.upsert_media_asset(
        file_path=video_path,
        file_name=file_name,
        source_type="reference",
        duration_sec=metadata.get("duration_sec"),
        resolution=metadata.get("resolution"),
        file_size_bytes=metadata.get("file_size_bytes"),
    )
    asset_id = asset["id"] if asset else None

    if not asset_id:
        existing = db.find_asset_by_path(video_path)
        asset_id = existing["id"] if existing else None

    if not asset_id:
        logger.error("DB登録失敗")
        db.close()
        return None

    # 2. シーン分割
    logger.info("シーン分割中...")
    scenes = detect_scenes(video_path)

    # 3. 音声抽出 & 文字起こし
    logger.info("音声抽出中...")
    audio_path = extract_audio(video_path)
    logger.info("文字起こし中...")
    transcript_segments = transcribe_audio(audio_path)

    # 4. 各シーンを処理
    import time as _time
    for i, scene in enumerate(scenes):
        # グリッド画像生成
        grid_path = os.path.join(grids_dir, f"scene_{scene['scene_index']:03d}_grid.jpg")
        extract_grid_image(video_path, scene["start_sec"], scene["end_sec"], grid_path)

        # このシーンに該当する文字起こしを抽出
        scene_text = " ".join(
            seg["text"] for seg in transcript_segments
            if seg.get("start_sec", 0) >= scene["start_sec"]
            and seg.get("start_sec", 0) < scene["end_sec"]
        )

        # タグ付け
        tags = auto_tag_scene(grid_path, scene_text)

        # API レート制限対策（3シーンごとに5秒待機）
        if i > 0 and i % 3 == 0:
            _time.sleep(5)

        # テキストのembedding生成
        text_embedding = None
        if scene_text:
            try:
                text_embedding = get_embedding(scene_text)
            except Exception as e:
                logger.warning(f"Embedding生成失敗: {e}")

        # DB保存: シーン
        scene_id = db.insert_scene(
            asset_id=asset_id,
            scene_index=scene["scene_index"],
            start_tc=scene["start_tc"],
            end_tc=scene["end_tc"],
            start_sec=scene["start_sec"],
            end_sec=scene["end_sec"],
            duration_sec=scene["duration_sec"],
            grid_image_path=grid_path if os.path.exists(grid_path) else None,
            classification=tags.get("composition", [None])[0],
        )

        # DB保存: 文字起こし
        if scene_text:
            db.insert_transcript(
                asset_id=asset_id,
                text=scene_text,
                start_tc=scene["start_tc"],
                end_tc=scene["end_tc"],
                start_sec=scene["start_sec"],
                end_sec=scene["end_sec"],
                text_embedding=text_embedding,
                scene_id=scene_id,
            )

        # DB保存: タグ
        for category, tag_list in tags.items():
            for tag_name in tag_list:
                try:
                    with db.conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO scene_tags (scene_id, category, tag_name, source)
                            VALUES (%s, %s, %s, 'auto')
                            ON CONFLICT (scene_id, category, tag_name) DO NOTHING
                        """, (scene_id, category, tag_name))
                    db.conn.commit()
                except Exception as e:
                    db.conn.rollback()
                    logger.warning(f"タグ保存失敗: {category}:{tag_name} - {e}")

    # 5. 参考動画メタデータ保存
    try:
        with db.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO reference_metadata (asset_id, program_name, channel, source_url, tier)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                asset_id,
                metadata.get("title"),
                metadata.get("channel"),
                metadata.get("url"),
                "youtube",
            ))
        db.conn.commit()
    except Exception as e:
        db.conn.rollback()
        logger.warning(f"メタデータ保存失敗: {e}")

    # 音声ファイル削除
    if os.path.exists(audio_path):
        os.remove(audio_path)

    db.close()
    logger.info(f"=== 解析完了: {file_name} ({len(scenes)}シーン) ===")
    return {"asset_id": str(asset_id), "scenes": len(scenes), "file": file_name}
