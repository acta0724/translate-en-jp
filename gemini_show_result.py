#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Gemini Show Result
# @raycast.mode fullOutput
# @raycast.packageName AI Tools
# @raycast.icon 🤖
# @raycast.description 翻訳結果を表示する

import sys
from pathlib import Path

RESULT_FILE = Path("/tmp/raycast_translation.txt")

if not RESULT_FILE.exists():
    print("❌ 翻訳結果がありません。先に翻訳を実行してください。")
    sys.exit(1)

print(RESULT_FILE.read_text())
