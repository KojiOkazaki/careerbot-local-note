"""Careerbot Local Note — ローカル専用サーバー

このサーバーは 127.0.0.1（このPC自身）でのみ待ち受け、
音声・文字起こし・相談記録を外部に送信することはありません。
"""
from __future__ import annotations

import json
import re
import shutil
import tempfile
import time
import uuid
import webbrowser
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import config
import llm
import prompts
import transcriber

APP_VERSION = "0.1.0"
BASE = Path(__file__).resolve().parent
app = FastAPI(title="Careerbot Local Note", docs_url=None, redoc_url=None)


# ---------- セッション（1回の相談 = 1フォルダ）----------

def _sdir(session_id: str) -> Path:
    if not re.fullmatch(r"[0-9]{8}_[0-9]{6}_[0-9a-f]{6}", session_id):
        raise HTTPException(400, "invalid session id")
    return config.DATA_DIR / session_id


def _load(session_id: str) -> dict:
    p = _sdir(session_id) / "session.json"
    if not p.exists():
        raise HTTPException(404, "session not found")
    return json.loads(p.read_text(encoding="utf-8"))


def _save(session: dict) -> None:
    d = _sdir(session["id"])
    d.mkdir(parents=True, exist_ok=True)
    (d / "session.json").write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
    (d / "transcript.md").write_text(transcript_markdown(session), encoding="utf-8")
    if session.get("summary"):
        (d / "summary.md").write_text(session["summary"], encoding="utf-8")
    if session.get("review"):
        (d / "review.md").write_text(session["review"], encoding="utf-8")


def _fmt_time(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"


SPEAKER_LABEL = {"C": "カウンセラー", "S": "学生", "?": "不明", "": ""}


def transcript_markdown(session: dict) -> str:
    lines = [f"# 相談記録（文字起こし） {session['created']}", ""]
    if session.get("counselor"):
        lines.append(f"担当: {session['counselor']}")
        lines.append("")
    for seg in session["segments"]:
        who = SPEAKER_LABEL.get(seg.get("speaker", ""), "")
        prefix = f"{who}：" if who else ""
        lines.append(f"[{_fmt_time(seg['start'])}] {prefix}{seg['text']}")
    return "\n".join(lines) + "\n"


def labeled_text(session: dict) -> str:
    """LLMに渡す用：話者付きの本文"""
    out = []
    for seg in session["segments"]:
        who = SPEAKER_LABEL.get(seg.get("speaker", ""), "")
        out.append(f"{who}：{seg['text']}" if who else seg["text"])
    return "\n".join(out)


# ---------- API ----------

@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/status")
def api_status():
    l = llm.status()
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    sessions = sorted([p.name for p in config.DATA_DIR.iterdir() if (p / "session.json").exists()], reverse=True)
    return {
        "version": APP_VERSION,
        "mock": config.MOCK,
        "ram_gb": round(llm.ram_gb(), 1),
        "llm": {"backend": config.LLM_BACKEND, **l},
        "whisper": {
            "backend": transcriber.backend_name(),
            "model": transcriber.model_name(),
            "downloaded": transcriber.model_downloaded(),
        },
        "data_dir": str(config.DATA_DIR),
        "save_audio": config.SAVE_AUDIO,
        "external_endpoints": [],   # 外部通信先は存在しない
        "sessions": sessions,
    }


@app.post("/api/transcribe")
async def api_transcribe(file: UploadFile = File(...), counselor: str = Form("")):
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    sdir = _sdir(session_id)
    sdir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    audio_path = sdir / f"audio{suffix}"
    with audio_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    t0 = time.time()
    try:
        segments = await run_in_threadpool(transcriber.transcribe, audio_path)
    except Exception as e:  # noqa: BLE001
        shutil.rmtree(sdir, ignore_errors=True)
        raise HTTPException(500, f"文字起こしに失敗しました: {e}")
    finally:
        if not config.SAVE_AUDIO and audio_path.exists():
            audio_path.unlink()

    session = {
        "id": session_id,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "counselor": counselor.strip(),
        "segments": [{"i": i + 1, "speaker": "", **s} for i, s in enumerate(segments)],
        "summary": "",
        "review": "",
        "transcribe_seconds": round(time.time() - t0, 1),
    }
    _save(session)
    return session


@app.get("/api/sessions/{session_id}")
def api_get_session(session_id: str):
    return _load(session_id)


@app.put("/api/sessions/{session_id}/segments")
def api_put_segments(session_id: str, body: dict):
    session = _load(session_id)
    incoming = {s["i"]: s for s in body.get("segments", [])}
    for seg in session["segments"]:
        if seg["i"] in incoming:
            src = incoming[seg["i"]]
            seg["speaker"] = src.get("speaker", seg["speaker"])
            seg["text"] = src.get("text", seg["text"])
    _save(session)
    return {"ok": True}


@app.delete("/api/sessions/{session_id}")
def api_delete_session(session_id: str):
    sdir = _sdir(session_id)
    if sdir.exists():
        shutil.rmtree(sdir)
    return {"ok": True}


# ---------- LLM 処理 ----------

BATCH = 60
_LABEL_RE = re.compile(r"\[(\d+)\]\s*([CS?])")


def _label_speakers(session: dict) -> dict:
    segs = session["segments"]
    system = prompts.SPEAKER_SYSTEM.format(counselor_hint=prompts.counselor_hint(session.get("counselor", "")))
    for start in range(0, len(segs), BATCH):
        batch = segs[start:start + BATCH]
        context = ""
        if start > 0:
            prev = segs[max(0, start - 5):start]
            context = "直前の判定済みの行:\n" + "\n".join(
                f"[{s['i']}] {s.get('speaker') or '?'} {s['text']}" for s in prev) + "\n\n"
        user = context + "判定する行:\n" + "\n".join(f"[{s['i']}] {s['text']}" for s in batch)
        reply = llm.chat(system, user, temperature=0.0, max_tokens=len(batch) * 12 + 100)
        found = {int(n): lab for n, lab in _LABEL_RE.findall(reply)}
        for s in batch:
            s["speaker"] = found.get(s["i"], s.get("speaker") or "?")
    _save(session)
    return session


@app.post("/api/sessions/{session_id}/label")
async def api_label(session_id: str):
    session = _load(session_id)
    if not session["segments"]:
        raise HTTPException(400, "文字起こし結果がありません")
    try:
        return await run_in_threadpool(_label_speakers, session)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"話者推定に失敗しました（LLMに接続できていますか）: {e}")


@app.post("/api/sessions/{session_id}/summary")
async def api_summary(session_id: str):
    session = _load(session_id)
    try:
        text = await run_in_threadpool(llm.chat, prompts.SUMMARY_SYSTEM, labeled_text(session), 0.2, 3000)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"要約に失敗しました（LLMに接続できていますか）: {e}")
    session["summary"] = text
    _save(session)
    return session


@app.post("/api/sessions/{session_id}/review")
async def api_review(session_id: str):
    session = _load(session_id)
    try:
        text = await run_in_threadpool(llm.chat, prompts.REVIEW_SYSTEM, labeled_text(session), 0.3, 4000)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"振り返りの生成に失敗しました（LLMに接続できていますか）: {e}")
    session["review"] = text
    _save(session)
    return session


app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


def main():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    url = f"http://{config.HOST}:{config.PORT}"
    print("=" * 60)
    print(f" Careerbot Local Note {APP_VERSION}")
    print(f" 画面: {url}  （このPCの中だけで動いています）")
    print(f" 保存先: {config.DATA_DIR}")
    if config.MOCK:
        print(" ※ MOCKモード: Whisper/LLM は使いません")
    print("=" * 60)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="warning")


if __name__ == "__main__":
    main()
