# Drive Download

Google Driveのフォルダ/ファイルをローカルにダウンロードするツール。
フォルダ階層を完全再現し、差分チェックで重複ダウンロードを防止します。

## 解決する課題

ブラウザからGoogle Driveのフォルダをダウンロードすると:
- 大きいフォルダがzipファイルに分割される
- 解凍すると元のフォルダ構造が壊れる

このツールは Google Drive API で1ファイルずつダウンロードし、元の階層構造をそのまま再現します。

## セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/BLITZ-AI-agent-team/drive-download.git
cd drive-download
```

### 2. 依存パッケージをインストール

```bash
pip install google-api-python-client google-auth
```

### 3. サービスアカウントキーを配置

`service_account.json` をプロジェクトルートに配置してください（別途共有）。

### 4. ダウンロード対象を共有

ダウンロードしたいフォルダ/ファイルを、以下のメールアドレスに共有してください（閲覧者でOK）:

```
aiagent-dev@aiagent-dev-489706.iam.gserviceaccount.com
```

## 使い方

### Claude Code から（推奨）

```
「このGoogleドライブのフォルダをダウンロードして」
https://drive.google.com/drive/u/0/folders/XXXXX
```

### コマンドラインから

```bash
# フォルダをダウンロード（URL指定）
python -m src.module7.main "https://drive.google.com/drive/u/0/folders/XXXXX"

# 保存先を指定
python -m src.module7.main "https://drive.google.com/drive/u/0/folders/XXXXX" -d /path/to/save

# フォルダIDで直接指定
python -m src.module7.main "1Lr2Yy7I4X44q4gOp_MUjwXVB_7C4X_U1"
```

### オプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `-d`, `--dest` | 保存先ディレクトリ | `./downloads/` |
| `--sa-key` | サービスアカウントJSONのパス | `./service_account.json` |
| `--no-notify` | Chatwork通知をスキップ | 通知あり |
| `--log-dir` | ログ出力先 | `./logs/` |

## 機能

- **フォルダ階層の完全再現**: サブフォルダを含む全構造をローカルに再現
- **差分チェック**: ファイルサイズ+更新日時で判定、同一ファイルはスキップ
- **共有ドライブ対応**: Shared Drive内のファイルもダウンロード可能
- **Google Docs自動変換**: Docs→PDF, Sheets→xlsx, Slides→pptx
- **日付別ログ**: `logs/module7_YYYY-MM-DD.log` に実行記録を保存
