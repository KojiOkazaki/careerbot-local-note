"""Careerbot Local Note 設定ファイル

変更が必要そうな項目はすべてここにあります。コードを触る必要はありません。
"""
import os
from pathlib import Path

# ---- 画面（Chromeで開くアドレス）----
HOST = "127.0.0.1"          # このPC以外からは接続できません
PORT = 8765

# ---- LLM（要約・話者推定・振り返り）----
# "ollama"（推奨）または "lmstudio"
LLM_BACKEND = "ollama"
OLLAMA_URL = "http://127.0.0.1:11434"
LMSTUDIO_URL = "http://127.0.0.1:1234/v1"

# "auto" にすると、このPCのメモリ量で自動選択します
#   メモリ 12GB 未満 → gemma4:e2b   （約3GB。8GBのPC向け）
#   メモリ 12GB 以上 → gemma4:e4b   （16GBのPC向け）
# 明示する場合は "gemma4:e4b" や "gemma4:12b" のように書きます
LLM_MODEL = "auto"

# ---- 文字起こし（Whisper）----
# "auto" にすると環境に合わせて自動選択します
#   Apple Silicon Mac → mlx-whisper の large-v3-turbo（高精度・高速）
#   それ以外          → faster-whisper の large-v3-turbo（CPU・int8）
# 軽くしたい場合は "medium" や "small" に変更できます
WHISPER_MODEL = "auto"
LANGUAGE = "ja"

# 文字起こし後にWhisperをメモリから降ろす（8GB PCでは True 推奨）
UNLOAD_WHISPER_AFTER_USE = True

# ---- 保存 ----
# 相談記録の保存先（このPC内）。大学の規程に従って管理してください
DATA_DIR = Path(os.environ.get("LOCAL_NOTE_DATA_DIR", Path.home() / "CareerbotLocalNote"))

# 録音音声そのものを残すか（False = 文字起こし後にすぐ削除）
SAVE_AUDIO = False

# ---- 開発用 ----
# LOCAL_NOTE_MOCK=1 で起動すると、Whisper/LLM無しで画面を確認できます
MOCK = os.environ.get("LOCAL_NOTE_MOCK") == "1"
