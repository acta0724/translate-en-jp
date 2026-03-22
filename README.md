# Gemini Translate Agent for Raycast

Raycast から Gemini API を使って日本語↔英語を相互翻訳するスクリプトです。

## 必要なもの

- macOS（Raycast が動作する環境）
- Python 3.10 以上
- [Raycast](https://www.raycast.com/) 最新版
- [Google AI Studio](https://aistudio.google.com/) で取得した Gemini API キー

## セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/acta0724/translate-en-jp.git
cd translate-en-jp
```

### 2. API キーを設定

`.env` ファイルを作成し、取得した API キーを記載します。

```bash
echo "GEMINI_API_KEY=your_api_key_here" > .env
chmod 600 .env
```

### 3. 実行権限を付与

```bash
chmod +x gemini_translate.py
```

### 4. Raycast に登録

1. Raycast を開き `⌘ ,` で設定を開く
2. **Extensions** → **Script Commands** → **Add Directories**
3. このリポジトリのディレクトリを選択
4. `Gemini Translate Agent` が一覧に表示されれば登録完了

## 使い方

### Raycast から使う

Raycast を開き `Gemini Translate Agent` を検索して起動します。

- **引数あり**: テキストフィールドに翻訳したいテキストを入力して実行
- **引数なし**: クリップボードのテキストを自動取得して翻訳

翻訳結果は画面に表示され、自動的にクリップボードにコピーされます。

### コマンドラインから使う

```bash
# 英語 → 日本語
python3 gemini_translate.py "Hello, world!"

# 日本語 → 英語
python3 gemini_translate.py "本日はお忙しい中お時間をいただきありがとうございます。"

# クリップボードから翻訳（引数なし）
python3 gemini_translate.py
```

## 機能

- 言語を自動判別して日本語↔英語を相互翻訳
- コードスニペット・URL・固有名詞はそのまま保持
- 翻訳結果を自動的にクリップボードにコピー
- 外部ライブラリ不要（標準ライブラリのみ使用）

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `Permission denied` | 実行権限なし | `chmod +x gemini_translate.py` |
| `APIエラー (403)` | API キー誤り | `.env` の値を確認 |
| `APIエラー (429)` | レートリミット超過 | 1 分待って再試行 |
| `ネットワークエラー` | 接続なし | Wi-Fi・VPN 設定を確認 |
| Raycast に表示されない | ディレクトリ未登録 | セットアップ手順 4 を再実施 |
