"""Zero-dependency ElevenLabs TTS helper returning MP3 audio + exact word timings."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path


def _alignment_to_words(alignment: dict) -> list[dict]:
    chars = alignment.get("characters", [])
    starts = alignment.get("character_start_times_seconds", [])
    ends = alignment.get("character_end_times_seconds", [])

    words: list[dict] = []
    cur_chars: list[str] = []
    w_start: float | None = None
    w_end: float = 0.0

    for ch, st, en in zip(chars, starts, ends):
        if ch.isspace():
            if cur_chars and w_start is not None:
                words.append({"text": "".join(cur_chars).upper(), "start": w_start, "end": w_end})
                cur_chars = []
                w_start = None
        else:
            if w_start is None:
                w_start = float(st)
            cur_chars.append(ch)
            w_end = float(en)

    if cur_chars and w_start is not None:
        words.append({"text": "".join(cur_chars).upper(), "start": w_start, "end": w_end})
    return words


def synth_elevenlabs_tts(
    text: str,
    out_mp3: Path,
    api_key: str | None = None,
    voice_id: str | None = None,
    model_id: str = "eleven_multilingual_v2",
) -> tuple[float, list[dict]]:
    key = (api_key or os.environ.get("ELEVENLABS_API_KEY", "")).strip()
    vid = (voice_id or os.environ.get("ELEVENLABS_VOICE_ID", "")).strip()
    if not key or not vid:
        raise RuntimeError("Missing ELEVENLABS_API_KEY or ELEVENLABS_VOICE_ID in .env")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}/with-timestamps"
    payload = json.dumps({
        "text": text,
        "model_id": model_id,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.78},
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "xi-api-key": key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"ElevenLabs API error {exc.code}: {exc.read().decode('utf-8', errors='replace')}") from exc

    out_mp3.write_bytes(base64.b64decode(data["audio_base64"]))
    words = _alignment_to_words(data.get("alignment", {}))

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(out_mp3)],
        capture_output=True, text=True, check=True,
    )
    return float(probe.stdout.strip()), words
