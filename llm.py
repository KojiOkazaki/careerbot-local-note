"""ローカルLLM（Ollama / LM Studio）への接続

要約・話者推定・振り返り分析はすべてこのPC内のLLMで処理します。
"""
from __future__ import annotations

import requests

import config


def ram_gb() -> float:
    try:
        import psutil
        return psutil.virtual_memory().total / (1024 ** 3)
    except Exception:
        return 0.0


def model_name() -> str:
    if config.LLM_MODEL != "auto":
        return config.LLM_MODEL
    if config.LLM_BACKEND == "lmstudio":
        return "google/gemma-4-e4b"
    return "gemma4:e2b" if ram_gb() < 12 else "gemma4:e4b"


def _base() -> str:
    return config.OLLAMA_URL if config.LLM_BACKEND == "ollama" else config.LMSTUDIO_URL


def status() -> dict:
    """接続状態とモデルの有無を返す"""
    if config.MOCK:
        return {"connected": True, "model": model_name(), "model_available": True, "models": [model_name()]}
    info = {"connected": False, "model": model_name(), "model_available": False, "models": []}
    try:
        if config.LLM_BACKEND == "ollama":
            r = requests.get(f"{_base()}/api/tags", timeout=3)
            r.raise_for_status()
            names = [m["name"] for m in r.json().get("models", [])]
        else:
            r = requests.get(f"{_base()}/models", timeout=3)
            r.raise_for_status()
            names = [m["id"] for m in r.json().get("data", [])]
        info["connected"] = True
        info["models"] = names
        want = model_name()
        info["model_available"] = any(n == want or n.split(":")[0] == want for n in names)
    except Exception:
        pass
    return info


def chat(system: str, user: str, temperature: float = 0.3, max_tokens: int = 4000) -> str:
    if config.MOCK:
        return _mock_reply(system)
    if config.LLM_BACKEND == "ollama":
        return _ollama(system, user, temperature, max_tokens)
    return _lmstudio(system, user, temperature, max_tokens)


def _ollama(system: str, user: str, temperature: float, max_tokens: int) -> str:
    body = {
        "model": model_name(),
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": False,
        "keep_alive": "10m",
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    # 思考モードがあるモデルはオフにする（オンだと数倍遅い）。非対応モデルなら外して再送
    r = requests.post(f"{_base()}/api/chat", json={**body, "think": False}, timeout=1800)
    if r.status_code == 400:
        r = requests.post(f"{_base()}/api/chat", json=body, timeout=1800)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def _lmstudio(system: str, user: str, temperature: float, max_tokens: int) -> str:
    body = {
        "model": model_name(),
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    r = requests.post(f"{_base()}/chat/completions", json=body, timeout=1800)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def _mock_reply(system: str) -> str:
    if "行番号" in system:
        return "\n".join(f"[{i}] {'C' if i % 2 == 1 else 'S'}" for i in range(1, 9))
    if "振り返り" in system:
        return (
            "## 主訴と本質的な課題\n- 主訴：就活の進め方が分からない\n- 本質的な課題（推測）：自己肯定感の低さ\n\n"
            "## 深掘りできたかもしれない発言\n- 「特にないなって思っちゃうんです。まあ、いいんですけど。」\n"
            "  → 「まあ、いいんですけど」で流された。ここに感情が乗っている可能性\n\n"
            "## カウンセラーの関わり\n- 言い換え・要約による傾聴ができている\n- やや早く手段（自己分析の進め方）に移行した\n\n"
            "## 次回聞くとよいこと\n- 「強みがない」と感じるようになった経緯\n\n## 良かった点\n- 開かれた質問で始めている"
        )
    return (
        "## 主訴\n就活を始めたが何から手をつければよいか分からない\n\n## 学生の状況\n就活サイトに登録済み。自己分析の意味がつかめず、自分の強みが「特にない」と感じている\n\n"
        "## 相談の経過\n主訴の確認 → 現状の確認 → 自己分析へのつまずきの具体化\n\n## カウンセラーの対応\n自己分析の進め方を一緒に確認することを提案\n\n"
        "## 合意事項・次回まで\n自己分析の進め方を確認する"
    )
