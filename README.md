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

### 5. ホットキーを設定（推奨）

Raycast の設定から `Gemini Translate Agent` にホットキーを割り当てると素早く起動できます。

## 使い方

1. 翻訳したいテキストを選択して `⌘ C` でコピー
2. ホットキーを押す（または Raycast で `Gemini Translate Agent` を検索して起動）
3. Raycast に翻訳結果が表示される

## 機能

- 言語を自動判別して日本語↔英語を相互翻訳
- コードスニペット・URL・固有名詞はそのまま保持
- 外部ライブラリ不要（標準ライブラリのみ使用）

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `Permission denied` | 実行権限なし | `chmod +x gemini_translate.py` |
| `APIエラー (403)` | API キー誤り | `.env` の値を確認 |
| `APIエラー (429)` | レートリミット超過 | 1 分待って再試行 |
| `ネットワークエラー` | 接続なし | Wi-Fi・VPN 設定を確認 |
| Raycast に表示されない | ディレクトリ未登録 | セットアップ手順 4 を再実施 |
