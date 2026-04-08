# Drive Download セットアップガイド

Google Driveのフォルダを、フォルダ構造そのままローカルにダウンロードできるツールです。
ブラウザDLで起きるzip分割・構造崩壊の問題を解決します。

---

## セットアップ方法

### 事前準備（あなたが手動でやること）

1. 別途共有された `service_account.json` をデスクトップなど分かりやすい場所に保存する
2. Claude Code を開く

### Claude Code に以下を貼り付ける

以下を **そのままコピーして** Claude Code に貼り付けてください。自動でセットアップが始まります:

---

```
Drive Download ツールをセットアップして。以下の手順を全部自動でやって:

1. リポジトリをクローン:
   git clone https://github.com/BLITZ-AI-agent-team/drive-download.git

2. 依存パッケージをインストール:
   pip install google-api-python-client google-auth

3. service_account.json をリポジトリ直下にコピー（デスクトップにあるはず。なければ場所を聞いて）

4. スキルをグローバルに登録:
   mkdir -p ~/.claude/skills/drive-download
   cp drive-download/.claude/skills/drive-download/SKILL.md ~/.claude/skills/drive-download/SKILL.md

5. 全部終わったら「セットアップ完了」と教えて
```

---

セットアップは以上です。完了したら、次から以下のように使えます:

## 使い方

Claude Code でこう話しかけるだけ:

```
このGoogleドライブのフォルダをダウンロードして
https://drive.google.com/drive/u/0/folders/XXXXX
```

---

## Claude Code を使わない場合（ターミナルで実行）

### セットアップ

1. **Git と Python をインストール**（まだの場合）
   - Git: https://git-scm.com/downloads
   - Python: https://www.python.org/downloads/ （3.10以上）

2. **ターミナルを開いて以下を順番に実行**

```bash
# ホームフォルダに移動（ここにツールが入ります）
cd ~

# ツールをダウンロード
git clone https://github.com/BLITZ-AI-agent-team/drive-download.git

# 必要なライブラリをインストール
cd drive-download
pip install google-api-python-client google-auth
```

3. **`service_account.json` を配置**

別途共有された `service_account.json` を `drive-download` フォルダの中に置いてください。

```
Finder/エクスプローラーで:
  drive-download/           ← このフォルダの中に
    service_account.json    ← このファイルを置く
    src/
    README.md
```

### ダウンロードの実行方法

#### 1. Google Drive の URL を取得する

ダウンロードしたいフォルダを Google Drive で開き、ブラウザのアドレスバーから URL をコピーします。

#### 2. ターミナルで実行

```bash
cd ~/drive-download
python -m src.module7.main "ここにコピーしたURLを貼り付け"
```

例:
```bash
python -m src.module7.main "https://drive.google.com/drive/u/0/folders/1Lr2Yy7I4X44q4gOp_XXXXX"
```

#### 3. ダウンロード先

ファイルは自動的に以下のフォルダに保存されます:

```
~/drive-download/downloads/フォルダ名/
```

例えば「INV_FESL」というフォルダをDLした場合:
```
~/drive-download/downloads/INV_FESL/
  ├── サイド/
  │   ├── 動画1.MP4
  │   └── 動画2.MP4
  ├── メイン/
  │   └── 動画3.MP4
  └── テロップ/
      └── テロップ01.psd
```

Google Drive 上のフォルダ構造がそのまま再現されます。
指定やフォルダ作成は不要で、自動的にこの場所に整理されます。

---

## 注意事項

- **新しいフォ��ダを初めてダウンロードする場合**、そのフォルダがサービスアカウントに共有されている必要があります。共有されていないと「File not found」エラーになります。
- 共有方法: Google Driveで対象フォルダを右クリック → 共有 → `aiagent-dev@aiagent-dev-489706.iam.gserviceaccount.com` を閲覧者として追加
- 一度共有すれば、そのフォルダ内のファイルは何度でもダウンロードできます。

---

## よくある質問

**Q: 同じフォルダを2回ダウンロードしたらどうなる？**
差分チェックが働き、変更のないファイルはスキップされます。更新されたファイルだけ再ダウンロードします。

**Q: Google スプレッドシートやドキュメントはどうなる？**
自動的に変換されます: Docs→PDF、Sheets→xlsx、Slides→pptx
