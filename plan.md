# Raycast Gemini Translation Agent — Claude Code 実装仕様書

> この仕様書は、Claude Code が迷わず実装できるよう、ファイル構成・コード・設定値をすべて具体的に記述しています。

---

## 0. 前提条件

| 項目 | 要件 |
|------|------|
| OS | macOS (Raycast が動作する環境) |
| Python | 3.10 以上 (`python3 --version` で確認) |
| Raycast | 最新版インストール済み |
| Gemini API キー | Google AI Studio で取得済み |

---

## 1. ディレクトリ構成

```
~/RaycastScripts/
└── translation-agent/
    ├── gemini_translate.py   # メインスクリプト（Raycast が直接実行）
    └── .env                  # API キー格納（Git 管理対象外）
```

**作成コマンド（Claude Code はこの順で実行すること）:**

```bash
mkdir -p ~/RaycastScripts/translation-agent
cd ~/RaycastScripts/translation-agent
touch gemini_translate.py .env
chmod +x gemini_translate.py
```

---

## 2. `.env` ファイル

```env
GEMINI_API_KEY=your_api_key_here
```

> `your_api_key_here` を実際のキーに置き換える。ファイルのパーミッションを `600` に設定すること。
>
> ```bash
> chmod 600 ~/RaycastScripts/translation-agent/.env
> ```

---

## 3. `gemini_translate.py` 完全実装

以下のコードをそのままファイルに書き込む。

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Gemini Translate Agent
# @raycast.mode fullOutput
# @raycast.packageName AI Tools
# @raycast.icon 🤖
# Optional parameters:
# @raycast.argument1 {"type": "text", "placeholder": "翻訳するテキスト（空白時はクリップボードから取得）", "optional": true}
# @raycast.description Gemini APIを使って日英翻訳を行うエージェント
# @raycast.author your_name

import sys
import json
import subprocess
import urllib.request
import urllib.error
import os
from pathlib import Path

# ── 設定 ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
ENV_FILE   = SCRIPT_DIR / ".env"
API_URL    = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
TIMEOUT    = 30   # 秒
TEMPERATURE = 0.3 # 翻訳精度重視（0.0〜1.0）
MAX_TOKENS  = 8192
# ────────────────────────────────────────────────────────────────────────────


def load_api_key() -> str:
    """
    API キーを .env ファイルから読み込む。
    見つからない場合は環境変数 GEMINI_API_KEY を参照する。
    """
    # .env ファイルから読み込み
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                key = line.split("=", 1)[1].strip()
                if key and key != "your_api_key_here":
                    return key

    # 環境変数にフォールバック
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key

    print("❌ エラー: API キーが設定されていません。")
    print(f"   {ENV_FILE} に GEMINI_API_KEY=<your_key> を記載してください。")
    sys.exit(1)


def get_input_text() -> str:
    """
    入力テキストを取得する。
    優先順位: Raycast 引数 → クリップボード
    """
    # Raycast 引数
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return sys.argv[1].strip()

    # クリップボード（macOS: pbpaste）
    try:
        result = subprocess.run(
            ["pbpaste"],
            capture_output=True,
            text=True,
            timeout=5
        )
        clipboard_text = result.stdout.strip()
        if clipboard_text:
            return clipboard_text
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    print("❌ エラー: 翻訳するテキストがありません。")
    print("   テキストを選択してから実行するか、引数に直接入力してください。")
    sys.exit(1)


def build_prompt(input_text: str) -> str:
    """
    エージェント用のプロンプトを構築する。
    言語を自動判別し、日本語↔英語を相互翻訳する。
    """
    return f"""You are a professional translator and proofreader specializing in technical content.

Your task:
- Detect the language of the input text automatically.
- If the input is Japanese → translate to natural English.
- If the input is English (or any other language) → translate to natural Japanese.

Rules (strictly follow all of them):
1. Output ONLY the translated text. No explanations, no greetings, no meta-commentary.
2. Preserve the original tone (formal/informal/technical).
3. For IT/technical terms, use appropriate katakana or keep the original English term based on context.
4. Preserve code snippets, URLs, and proper nouns as-is.
5. If the text is already in the target language, output it as-is without modification.

Input text:
{input_text}"""


def call_gemini_api(api_key: str, prompt: str) -> str:
    """
    Gemini API を呼び出して翻訳結果を返す。
    標準ライブラリ (urllib) のみ使用。
    """
    endpoint = f"{API_URL}?key={api_key}"

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": TEMPERATURE,
            "maxOutputTokens": MAX_TOKENS,
        }
    }

    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            body = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            error_json = json.loads(error_body)
            message = error_json.get("error", {}).get("message", error_body)
        except json.JSONDecodeError:
            message = error_body

        if e.code == 400:
            print(f"❌ APIエラー (400): リクエストが不正です。\n   詳細: {message}")
        elif e.code == 403:
            print("❌ APIエラー (403): API キーが無効か権限がありません。")
            print("   Google AI Studio でキーを確認してください。")
        elif e.code == 429:
            print("❌ APIエラー (429): レートリミット超過。しばらく待ってから再試行してください。")
        else:
            print(f"❌ APIエラー ({e.code}): {message}")
        sys.exit(1)

    except urllib.error.URLError as e:
        print("❌ ネットワークエラー: インターネット接続を確認してください。")
        print(f"   詳細: {e.reason}")
        sys.exit(1)

    except TimeoutError:
        print(f"❌ タイムアウト: {TIMEOUT}秒以内に応答がありませんでした。")
        sys.exit(1)

    # レスポンスからテキストを抽出
    try:
        translated = (
            body["candidates"][0]["content"]["parts"][0]["text"].strip()
        )
        return translated
    except (KeyError, IndexError) as e:
        print(f"❌ レスポンス解析エラー: 予期しない応答形式です。")
        print(f"   レスポンス: {json.dumps(body, ensure_ascii=False, indent=2)}")
        sys.exit(1)


def copy_to_clipboard(text: str) -> bool:
    """翻訳結果をクリップボードにコピーする。"""
    try:
        subprocess.run(
            ["pbcopy"],
            input=text.encode("utf-8"),
            timeout=5,
            check=True
        )
        return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return False


def main():
    api_key    = load_api_key()
    input_text = get_input_text()
    prompt     = build_prompt(input_text)
    result     = call_gemini_api(api_key, prompt)

    # クリップボードにコピー
    copied = copy_to_clipboard(result)

    # Raycast の fullOutput モードに表示
    print(result)
    print()
    if copied:
        print("✅ クリップボードにコピーしました")
    else:
        print("⚠️  クリップボードへのコピーに失敗しました")


if __name__ == "__main__":
    main()
```

---

## 4. Raycast への登録手順

1. Raycast を開き `⌘ ,` で設定を開く
2. **Extensions** → **Script Commands** → **Add Directories**
3. `~/RaycastScripts/translation-agent` を選択
4. `gemini_translate.py` が一覧に表示されれば登録完了

---

## 5. 動作確認チェックリスト

Claude Code は実装後、以下を順番に確認すること。

```bash
# 1. 実行権限の確認
ls -la ~/RaycastScripts/translation-agent/gemini_translate.py
# → -rwxr-xr-x であること（先頭に x がある）

# 2. 引数渡しで直接テスト
cd ~/RaycastScripts/translation-agent
python3 gemini_translate.py "Hello, world!"
# → 「こんにちは、世界！」などの日本語が出力される

# 3. 日本語 → 英語テスト
python3 gemini_translate.py "本日はお忙しい中お時間をいただきありがとうございます。"
# → 自然な英語が出力される

# 4. クリップボードテスト（pbpaste で確認）
pbpaste
# → 翻訳結果がクリップボードに入っている
```

---

## 6. トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `Permission denied` | 実行権限なし | `chmod +x gemini_translate.py` |
| `APIエラー (403)` | API キー誤り | `.env` の値を確認 |
| `APIエラー (429)` | レートリミット | 1 分待って再試行 |
| `ネットワークエラー` | 接続なし | Wi-Fi・VPN 設定を確認 |
| Raycast に表示されない | ディレクトリ未登録 | 手順 4 を再実施 |
| 文字化け | 文字コード問題 | Python 3.10+ であることを確認 |

---

## 7. カスタマイズポイント

### 翻訳先言語を固定する場合

`build_prompt()` 内の判別ロジックを削除し、以下のように書き換える。

```python
# 常に日本語へ翻訳
return f"""You are a professional translator.
Translate the following text into natural Japanese.
Output ONLY the translated text.

Text: {input_text}"""
```

### モデルを変更する場合

`API_URL` の `gemini-1.5-flash` を変更する。

| モデル | 特徴 |
|--------|------|
| `gemini-1.5-flash` | 高速・低コスト（デフォルト推奨） |
| `gemini-1.5-pro` | 高精度・複雑な文章向け |

```python
# API_URL の変更例（pro モデルへ切り替え）
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
```

---

## 8. ファイル一覧サマリー

| ファイル | 役割 | 編集要否 |
|----------|------|----------|
| `gemini_translate.py` | メインスクリプト | 不要（そのまま使用可） |
| `.env` | API キー格納 | **必須**（キーを記入） |