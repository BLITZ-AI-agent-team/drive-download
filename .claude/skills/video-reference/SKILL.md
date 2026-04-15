---
name: video-reference
description: 参考動画のリサーチ・ダウンロード・解析・ライブラリ検索。YouTube/TVer/ABEMAから動画を取り込み、シーン分割・タグ付けしてDBに蓄積。蓄積した動画を自然言語やタグで検索できる。
triggers:
  - 参考動画を探して
  - 参考動画リサーチ
  - 動画を検索して
  - こういうシーンない？
  - 参考ライブラリ
  - /video-reference
---

# 参考動画リサーチ・解析スキル

## 概要

YouTube/TVer/ABEMAから参考動画を取り込み、シーン分割・文字起こし・タグ付けしてDBに蓄積する。
蓄積した動画ライブラリを「派手なオープニング」のような自然言語やタグで検索できる。

## 機能

1. **YouTube検索** — キーワードで参考動画を探す（APIキー不要）
2. **動画DL** — YouTube/Vimeoから720pでダウンロード
3. **解析パイプライン** — シーン分割→文字起こし→タグ付け→DB保存
4. **ライブラリ検索** — 蓄積データを自然言語・タグ・キーワードで検索
5. **OBS録画** — TVer/ABEMAの番組を自動録画（Playwright+OBS）

## 前提条件

- Python 3.10+
- FFmpeg（Whisper対応ビルド）
- Whisperモデル: `models/ggml-small.bin`
- GEMINI_API_KEY（`.env` に設定）
- Neon PostgreSQL（DATABASE_URL を `.env` に設定）

## 実行手順

### A: 参考動画を探して取り込む場合

#### Step 1: ユーザーのイメージを聞く

「どんな動画を探していますか？」と確認。例:
- 「バラエティ番組の派手なオープニング」
- 「対談シーンのカメラワーク」
- 「テロップが多めの演出」

#### Step 2: YouTube検索

```bash
cd {プロジェクトルート} && python -c "
import yt_dlp
ydl_opts = {'extract_flat': True, 'quiet': True}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    results = ydl.extract_info('ytsearch10:{検索キーワード}', download=False)
    for i, e in enumerate(results['entries'], 1):
        print(f'[{i}] {e[\"title\"]}')
        print(f'    https://www.youtube.com/watch?v={e[\"id\"]}')
"
```

検索結果をユーザーに見せて、どれを取り込むか確認。

#### Step 3: DL + 解析

```bash
cd {プロジェクトルート} && python -c "
import os
from dotenv import dotenv_values, load_dotenv
load_dotenv()
mine = dotenv_values('C:/Users/BLITZ74/dev/mine/.env')
os.environ['GEMINI_API_KEY'] = mine.get('GEMINI_API_KEY', '')

from src.module3.downloader import download_video
from src.module3.analyzer import run_pipeline

result = download_video('{動画URL}')
analysis = run_pipeline(result['file_path'], metadata=result)
print(analysis)
"
```

大きな動画（30分以上）はバックグラウンド実行を使用。

#### Step 4: 結果報告

- シーン数、タグ一覧、文字起こしのサマリーをユーザーに報告

### B: 蓄積ライブラリから検索する場合

#### Step 1: ユーザーの検索意図を確認

「何を探していますか？」と聞く。

#### Step 2: 検索実行

**自然言語検索（あいまい検索）:**
```bash
cd {プロジェクトルート} && python -c "
import os
from dotenv import dotenv_values, load_dotenv
load_dotenv()
mine = dotenv_values('C:/Users/BLITZ74/dev/mine/.env')
os.environ['GEMINI_API_KEY'] = mine.get('GEMINI_API_KEY', '')

from src.module3.library import search_by_text_query
results = search_by_text_query('{検索クエリ}', limit=10)
for r in results:
    print(f'{r[\"file_name\"]} [{r[\"start_tc\"]}-{r[\"end_tc\"]}] sim:{r[\"similarity\"]} {r[\"text\"][:80]}')
"
```

**タグ検索:**
```bash
cd {プロジェクトルート} && python -c "
from src.module3.library import search_by_tags
results = search_by_tags({'composition': 'オープニング', 'mood': '派手'}, limit=10)
for r in results:
    print(f'{r[\"file_name\"]} scene:{r[\"scene_index\"]} tags:{r[\"tags\"]}')
"
```

**キーワード検索:**
```bash
cd {プロジェクトルート} && python -c "
from src.module3.library import search_by_keyword
results = search_by_keyword('{キーワード}', limit=10)
for r in results:
    print(f'{r[\"file_name\"]} [{r[\"start_tc\"]}-{r[\"end_tc\"]}] {r[\"text\"][:80]}')
"
```

#### Step 3: 結果表示

グリッド画像がある場合はRead toolで表示。ファイルパスとタイムコードを伝える。

## タグカテゴリ一覧

| カテゴリ | 例 |
|---------|---|
| composition | オープニング, エンディング, 場面転換, 対談, 人物紹介, 解説 |
| direction | テロップ多め, 図解, グラフ解説, 写真挿入, ナレーション |
| mood | 派手, 落ち着き, コミカル, 感動的, クール |
| telop_style | ポップ, シンプル, ニュース風, バラエティ風 |
| camera_work | 固定, パン, ズーム, 引き, 寄り, 俯瞰, 手持ち |
