#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Gemini Translate Agent
# @raycast.mode silent
# @raycast.packageName AI Tools
# @raycast.icon 🤖
# @raycast.description Gemini APIを使って選択中のテキストを日英翻訳するエージェント
# @raycast.author your_name

import sys
import json
import subprocess
import urllib.request
import urllib.error
import os
import ssl
import time
from pathlib import Path

# macOS Python の SSL 証明書問題を回避
try:
    import certifi
    ssl_context = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    ssl_context = ssl.create_default_context()

# ── 設定 ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
ENV_FILE   = SCRIPT_DIR / ".env"
API_URL    = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
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


def get_selected_text() -> str:
    """
    選択中のテキストを取得する。
    現在のクリップボードを保存し、Cmd+C で選択テキストをコピー後に復元する。
    """
    # 現在のクリップボードを保存
    try:
        original_clipboard = subprocess.run(
            ["pbpaste"], capture_output=True, text=True, timeout=5
        ).stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        original_clipboard = ""

    # 選択中のテキストをコピー（元のアプリを明示的にターゲット）
    try:
        subprocess.run(
            ["osascript", "-e", """
                tell application "System Events"
                    set frontApp to name of first application process whose frontmost is true
                end tell
                delay 0.3
                tell application "System Events"
                    tell process frontApp
                        keystroke "c" using {command down}
                    end tell
                end tell
            """],
            timeout=5,
            check=True
        )
        time.sleep(0.3)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        print("❌ エラー: 選択テキストの取得に失敗しました。")
        sys.exit(1)

    # コピーされたテキストを取得
    try:
        selected = subprocess.run(
            ["pbpaste"], capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        selected = ""

    if not selected or selected == original_clipboard.strip():
        # クリップボードを復元
        if original_clipboard:
            subprocess.run(["pbcopy"], input=original_clipboard.encode(), timeout=5)
        print("❌ エラー: テキストが選択されていません。")
        print("   翻訳したいテキストを選択してからホットキーを押してください。")
        sys.exit(1)

    return selected


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
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl_context) as response:
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
    except (KeyError, IndexError):
        print("❌ レスポンス解析エラー: 予期しない応答形式です。")
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
    input_text = get_selected_text()
    prompt     = build_prompt(input_text)
    result     = call_gemini_api(api_key, prompt)

    # クリップボードにコピー
    copy_to_clipboard(result)

    # 結果を一時ファイルに保存
    Path("/tmp/raycast_translation.txt").write_text(result)

    # Raycast URL スキームで gemini_show_result を起動
    subprocess.run(
        ["open", "raycast://script-commands/run?name=Gemini%20Show%20Result"],
        timeout=5
    )

    print("✅ 翻訳完了")


if __name__ == "__main__":
    main()
