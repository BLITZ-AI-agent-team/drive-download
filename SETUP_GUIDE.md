# Video Tool セットアップガイド

2つのツールが含まれています。必要なものだけセットアップすればOK:

- **Drive Download** — Google Driveのフォルダをローカルにダウンロード
- **Video Reference** — 参考動画をDL・解析・蓄積してAI検索

---

## セットアップ方法（Claude Code ユーザー）

Claude Code に以下を貼り付けてください。必要なものを自動でセットアップします。

### Drive Download だけ使う場合

事前準備: 別途共有された `service_account.json` をデスクトップに保存

```
Video Tool の Drive Download をセットアップして。以下を全部自動でやって:

1. リポジトリをクローン:
   git clone https://github.com/BLITZ-AI-agent-team/video-tool.git

2. 依存パッケージをインストール:
   pip install google-api-python-client google-auth

3. service_account.json をリポジトリ直下にコピー（デスクトップにあるはず。なければ場所を聞いて）

4. スキルをグローバルに登録:
   mkdir -p ~/.claude/skills/drive-download
   cp video-tool/.claude/skills/drive-download/SKILL.md ~/.claude/skills/drive-download/SKILL.md

5. 全部終わったら「Drive Download セットアップ完了」と教えて
```

### Video Reference も使う場合（上記に加えて）

```
追加で Video Reference もセットアップして。以下を全部自動でやって:

1. 依存パッケージをインストール:
   pip install yt-dlp scenedetect opencv-python Pillow google-genai psycopg2 pgvector python-dotenv playwright obsws-python
   playwright install chromium

2. Whisperモデルをダウンロード（466MB）:
   mkdir -p models
   curl -L -o models/ggml-small.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin

3. .env.example を .env にコピー:
   cp .env.example .env

4. スキルをグローバルに登録:
   mkdir -p ~/.claude/skills/video-reference
   cp video-tool/.claude/skills/video-reference/SKILL.md ~/.claude/skills/video-reference/SKILL.md

5. 以下を私に聞いて、.env に設定:
   - DATABASE_URL（Neon PostgreSQL の接続文字列）
   - GEMINI_API_KEY
   - OBS_WS_PASSWORD（TVer/ABEMA録画しないなら空でOK）

6. 全部終わったら「Video Reference セットアップ完了」と教えて
```

---

## 使い方

### Drive Download

Claude Code に話しかけるだけ:

```
このGoogleドライブのフォルダをダウンロードして
https://drive.google.com/drive/u/0/folders/XXXXX
```

ダウンロード先: `~/video-tool/downloads/フォルダ名/` （フォルダ階層そのまま再現）

### Video Reference

**参考動画を探して取り込む:**
```
バラエティ番組のオープニングの参考動画を探して
```

**蓄積した動画から検索:**
```
派手なオープニングのシーンない？
```

```
対談シーンのカメラワーク参考になりそうなやつ探して
```

---

## Claude Code を使わない場合（ターミナルで実行）

### 事前準備

1. **Git と Python をインストール**
   - Git: https://git-scm.com/downloads
   - Python 3.10+: https://www.python.org/downloads/

2. **FFmpeg（Whisper対応ビルド）をインストール**
   - Windows: https://www.gyan.dev/ffmpeg/builds/ から `ffmpeg-git-full` をダウンロード
   - `ffmpeg -filters | grep whisper` で whisper フィルタが表示されれば OK

3. **ターミナルで以下を実行:**

```bash
# リポジトリ取得
cd ~
git clone https://github.com/BLITZ-AI-agent-team/video-tool.git
cd video-tool

# Drive Download だけ使う場合
pip install google-api-python-client google-auth

# Video Reference も使う場合（上記に追加）
pip install yt-dlp scenedetect opencv-python Pillow google-genai psycopg2 pgvector python-dotenv playwright obsws-python
playwright install chromium

# Whisperモデルのダウンロード
mkdir -p models
curl -L -o models/ggml-small.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin

# 設定ファイル
cp .env.example .env
# .env を開いて必要な項目を入力
```

4. **`service_account.json` をプロジェクトルートに配置**（別途共有されたもの）

### Drive Download の実行

```bash
python -m src.module7.main "https://drive.google.com/drive/u/0/folders/XXXXX"
```

保存先は `./downloads/フォルダ名/` です。

### Video Reference の実行

```bash
# YouTube検索
python -m src.module3.main search "バラエティ番組 オープニング"

# 動画をDL + 解析
python -m src.module3.main download "https://www.youtube.com/watch?v=XXXXX"

# ライブラリ検索
python -m src.module3.main library --query "派手なオープニング"
python -m src.module3.main library --keyword "テロップ"
```

---

## 必要なサービス・APIキー

### Drive Download に必要

- **サービスアカウントキー**（別途共有）

### Video Reference に必要

| サービス | 用途 | 取得方法 |
|---------|------|---------|
| **Neon PostgreSQL** | 解析結果のDB保存 | [neon.com](https://neon.com) でGoogleログイン → プロジェクト作成 → 接続文字列をコピー |
| **Gemini API** | タグ付け・Embedding | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) でAPIキー作成 |

どちらも無料で使えます。

### TVer/ABEMA録画を使う場合（オプション）

- **OBS Studio** — https://obsproject.com
- **OBS WebSocket設定** — OBS → ツール → WebSocketサーバー設定で認証有効化、パスワードを `.env` の `OBS_WS_PASSWORD` に設定
- **OBSのシーン設定** — ウィンドウキャプチャを追加してChromiumを指定

---

## 注意事項

- 撮影素材類のフォルダは**既に共有設定済み**なので、そのままダウンロードできます
- **新しい別のフォルダ**を初めてダウンロードする場合のみ、サービスアカウントへの共有が必要です
- 共有方法: Google Driveで対象フォルダを右クリック → 共有 → `aiagent-dev@aiagent-dev-489706.iam.gserviceaccount.com` を閲覧者として追加

---

## よくある質問

**Q: 同じフォルダを2回ダウンロードしたらどうなる？**
差分チェックが働き、変更のないファイルはスキップされます。

**Q: Google スプレッドシートやドキュメントはどうなる？**
自動的に変換されます: Docs→PDF、Sheets→xlsx、Slides→pptx

**Q: Video Reference の Neon PostgreSQL って何？**
解析結果（シーン情報・タグ・文字起こし）を保存するクラウドDBです。無料枠（0.5GB）で500本程度の動画を蓄積できます。

**Q: Gemini API の料金は？**
無料枠（1日1,000リクエスト程度）で、参考動画を1日10本程度解析する範囲では無料で収まります。超えても月$8程度。

**Q: 文字起こしは何を使っている？**
FFmpeg内蔵のWhisperをローカルで実行するので無料・APIキー不要です。
