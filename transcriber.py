"""文字起こし（Whisper）

- Apple Silicon Mac: mlx-whisper（GPU/Metal）
- それ以外: faster-whisper（CPU / int8）
音声のデコードは PyAV で行うため、ffmpeg のインストールは不要です。
"""
from __future__ import annotations

import gc
import platform
import threading
from pathlib import Path

import numpy as np

import config

INITIAL_PROMPT = "これは大学のキャリアセンターで行われた、キャリアカウンセラーと学生の相談の会話記録です。"

_lock = threading.Lock()
_model = None
_backend: str | None = None


def is_apple_silicon() -> bool:
    return platform.system() == "Darwin" and platform.machine() == "arm64"


def backend_name() -> str:
    if config.MOCK:
        return "mock"
    if is_apple_silicon():
        try:
            import mlx_whisper  # noqa: F401
            return "mlx-whisper"
        except ImportError:
            return "faster-whisper"
    return "faster-whisper"


def model_name() -> str:
    if config.WHISPER_MODEL != "auto":
        return config.WHISPER_MODEL
    return "large-v3-turbo"


def _hf_repo(name: str) -> str:
    """mlx-whisper 用の HuggingFace リポジトリ名"""
    if "/" in name:
        return name
    return f"mlx-community/whisper-{name}"


def model_downloaded() -> bool:
    """モデルがローカルキャッシュにあるか（初回は要ダウンロード）"""
    if config.MOCK:
        return True
    name = model_name()
    cache = Path.home() / ".cache" / "huggingface" / "hub"
    if backend_name() == "mlx-whisper":
        folder = "models--" + _hf_repo(name).replace("/", "--")
        return (cache / folder).exists()
    # faster-whisper は Systran/faster-whisper-<name> をキャッシュする
    folder = f"models--Systran--faster-whisper-{name}"
    if "/" in name:
        folder = "models--" + name.replace("/", "--")
    return (cache / folder).exists()


def load_audio(path: str | Path, sr: int = 16000) -> np.ndarray:
    """webm / m4a / mp3 / wav などを 16kHz モノラル float32 に変換"""
    import av

    chunks: list[np.ndarray] = []
    with av.open(str(path)) as container:
        stream = container.streams.audio[0]
        resampler = av.AudioResampler(format="s16", layout="mono", rate=sr)
        for frame in container.decode(stream):
            for out in resampler.resample(frame):
                chunks.append(out.to_ndarray())
        for out in resampler.resample(None):
            chunks.append(out.to_ndarray())
    if not chunks:
        return np.zeros(0, dtype=np.float32)
    audio = np.concatenate(chunks, axis=1).reshape(-1)
    return audio.astype(np.float32) / 32768.0


def _load_model():
    global _model, _backend
    if _model is not None:
        return _model
    _backend = backend_name()
    if _backend == "mlx-whisper":
        import mlx_whisper  # noqa: F401
        _model = _hf_repo(model_name())  # mlx-whisper はリポジトリ名を渡すだけ
    else:
        from faster_whisper import WhisperModel
        _model = WhisperModel(model_name(), device="cpu", compute_type="int8")
    return _model


def unload_model():
    global _model
    _model = None
    gc.collect()


def transcribe(path: str | Path) -> list[dict]:
    """音声ファイル → セグメント一覧 [{start, end, text}]"""
    if config.MOCK:
        return _mock_segments()

    audio = load_audio(path)
    if len(audio) < 16000 // 2:
        return []

    with _lock:
        model = _load_model()
        segments: list[dict] = []
        if _backend == "mlx-whisper":
            import mlx_whisper
            result = mlx_whisper.transcribe(
                audio,
                path_or_hf_repo=model,
                language=config.LANGUAGE,
                initial_prompt=INITIAL_PROMPT,
                condition_on_previous_text=False,
                fp16=True,
            )
            for s in result.get("segments", []):
                text = (s.get("text") or "").strip()
                if text:
                    segments.append({"start": float(s["start"]), "end": float(s["end"]), "text": text})
        else:
            gen, _info = model.transcribe(
                audio,
                language=config.LANGUAGE,
                beam_size=5,
                vad_filter=True,
                initial_prompt=INITIAL_PROMPT,
                condition_on_previous_text=False,
            )
            for s in gen:
                text = s.text.strip()
                if text:
                    segments.append({"start": float(s.start), "end": float(s.end), "text": text})
        if config.UNLOAD_WHISPER_AFTER_USE:
            unload_model()
    return segments


def _mock_segments() -> list[dict]:
    lines = [
        "こんにちは。今日はどんなことを相談したいですか。",
        "はい、あの、就活を始めたんですけど、何から手をつければいいか分からなくて。",
        "なるほど。何から手をつければいいか分からない、と。今はどんなことをしていますか。",
        "一応、就活サイトには登録しました。でも、自己分析とか言われても、正直よく分からなくて。",
        "自己分析が分からない、というのはもう少し具体的に言うとどんな感じですか。",
        "自分の強みとか聞かれても、特にないなって思っちゃうんです。まあ、いいんですけど。",
        "そうなんですね。では、まずは自己分析の進め方を一緒に見ていきましょうか。",
        "はい、お願いします。",
    ]
    t = 0.0
    out = []
    for line in lines:
        d = 2.0 + len(line) * 0.12
        out.append({"start": round(t, 2), "end": round(t + d, 2), "text": line})
        t += d + 0.8
    return out
