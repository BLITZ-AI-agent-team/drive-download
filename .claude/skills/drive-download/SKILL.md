---
name: drive-download
description: Google Driveのフォルダ/ファイルをローカルにダウンロード。フォルダ階層を完全再現し、差分チェックで重複DLを防止する。
triggers:
  - ドライブからダウンロード
  - Googleドライブダウンロード
  - drive download
  - フォルダをダウンロード
  - ファイルをダウンロード
  - /drive-download
---

# Google Drive 選択的ダウンロード スキル

## 概要

Google Driveの指定フォルダ/ファイルを、フォルダ階層を保ったままローカルにダウンロードする。
ブラウザDLで起きるzip分割・構造崩壊の問題を解決する。

## 機能

- フォルダ指定 → サブフォルダ含む全ファイルをDL、階層を完全再���
- ファイル単体指定 → そのファイルだけDL
- 差分チェック（サイズ+更新日時）→ 既存同一ファイルはスキップ
- 共有ドライブ（Shared Drive）対応
- Google Docs/Sheets/Slides → PDF/xlsx/pptx に自動エクスポート

## 前提条件

- Python 3.10+
- `google-api-python-client`, `google-auth` がインストール済み
- `service_account.json` がプロジェクトルートに配置済み
- 対象フォルダ/ファイルがサービスアカウントに共有されていること

サービスアカウントemail（共有時に使用）:
```
aiagent-dev@aiagent-dev-489706.iam.gserviceaccount.com
```

## 実行手順

### Step 1: ユーザーから情報を取得

以下を確認する（AskUserQuestionツールを使用）:

1. **ダウンロード対象**: Google DriveのURLまたはフォルダ/ファイルID
2. **保存先**（任意）: ローカルの保存先パス。未指定なら `プロジェクトルート/downloads/` を使用

### Step 2: 対象の確認

ダウンロード前に、対象の情報をユーザーに表示する:

```bash
cd {プロジェクトルート} && python -c "
from src.module7.drive_client import DriveClient
client = DriveClient()
meta = client.get_file_metadata('{TARGET_ID}')
print(f'名前: {meta[\"name\"]}')
print(f'タイプ: {meta[\"mimeType\"]}')
files = client.list_folder_recursive('{TARGET_ID}')
print(f'ファイル数: {len(files)}')
total = sum(int(f.get('size', 0)) for f in files)
print(f'合計サイズ: {total / 1024 / 1024:.1f} MB')
"
```

ユーザーに確認を取ってから次へ進む。

### Step 3: ダウンロード実行

```bash
cd {プロジェクトルート} && python -m src.module7.main "{URL_OR_ID}" -d "{保存先}" --no-notify
```

- 大量ファイルの場合はバックグラウンド実行（`run_in_background: true`）を使用
- 進捗はログファイル `logs/module7_YYYY-MM-DD.log` で確認可能

### Step 4: 結果報告

ダウンロード完了後、以下をユーザーに報告:

- ダウンロー��件数 / スキップ件数 / 失敗件数
- 合計サイズ
- ��存先パス
- フォルダ構造（サブフ���ルダがあれば表示）

失敗があった場合はエラー内容も表示する。

## トラブルシューティング

### 「File not found」エラー

対象が共有ドライブにある場合、サービスアカウントに共有されていない可能性がある。
ユー��ーに以下を案内:

1. Google Driveで対象フォルダを開く
2. 右クリック → 共有
3. `aiagent-dev@aiagent-dev-489706.iam.gserviceaccount.com` を追加（閲覧者でOK）

### Google Docs系ファイル

Google Docs/Sheets/Slidesは直接DLできないため、自動的に以下に変換される:
- Google Docs → PDF
- Google Sheets → xlsx
- Google Slides → pptx

## 使用例

```
ユーザー: このGoogleドライブのフォルダをダウンロードして
         https://drive.google.com/drive/u/0/folders/XXXXX

Claude:   フォルダ「INV_FESL」を確認しました。
          - ファイル数: 82
          - 合計: 9.6 GB
          - サブフォ��ダ: サイド, テロップ, メイン, 下カメ
          ダウンロードしますか？

ユーザー: お願い

Claude:   ダウンロード中... (バックグラウンド実行)
          ...
          完了！
          - DL: 82件 / スキップ: 0件 / 失敗: 0件
          - 保存先: C:\Users\...\downloads\INV_FESL\
```
