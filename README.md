# Video Tool

動画制作のための2つのツールをまとめたリポジトリ。

## 含まれるツール

### 1. Drive Download（Module 7）

Google Driveのフォルダ/ファイルをローカルにダウンロードするツール。
フォルダ階層を完全再現し、差分チェックで重複ダウンロードを防止します。

**解決する課題:**
- ブラウザからGoogle Driveのフォルダをダウンロードすると、大きいフォルダがzipに分割され、解凍すると構造が壊れる
- このツールは Google Drive API で1ファイルずつダウンロードし、元の階層構造をそのまま再現

### 2. Video Reference（Module 3）

参考動画のリサーチ・ダウンロード・解析・ライブラリ検索を行うツール。

**機能:**
- YouTube/Vimeoから参考動画を検索・ダウンロード（APIキー不要）
- TVer/ABEMAから OBS で自動録画
- シーン分割・文字起こし・AIタグ付け
- 蓄積した動画ライブラリを自然言語・タグ・キーワードで検索

## セットアップ

詳しいセットアップ手順は [SETUP_GUIDE.md](./SETUP_GUIDE.md) を参照してください。

## 使い方

### Drive Download（Claude Code から）

```
このGoogleドライブのフォルダをダウンロードして
https://drive.google.com/drive/u/0/folders/XXXXX
```

### Video Reference（Claude Code から）

```
バラエティ番組のオープニングの参考動画を探して
```

```
派手なオープニングのシーンない？
```
