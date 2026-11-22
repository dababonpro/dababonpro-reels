"""Ingest a YouTube lecture/talk into a clean transcript + metadata (fast subtitles first, Whisper fallback)."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


def find_ytdlp() -> str:
    py_tube_exe = Path(r"C:\Github_Personal\py-tube\venv\Scripts\yt-dlp.exe")
    if py_tube_exe.exists():
        return str(py_tube_exe)
    found = shutil.which("yt-dlp")
    if found:
        return found
    raise FileNotFoundError("yt-dlp not found. Install yt-dlp or ensure C:\\Github_Personal\\py-tube exists.")


def vtt_to_text(vtt_path: Path) -> str:
    lines: list[str] = []
    seen: set[str] = set()
    for raw in vtt_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:") or "-->" in line:
            continue
        clean = re.sub(r"<[^>]+>", "", line).strip()
        if clean and clean not in seen:
            seen.add(clean)
            lines.append(clean)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a YouTube video's metadata and transcript.")
    parser.add_argument("--url", required=True, help="YouTube video URL")
    parser.add_argument("--out-dir", default="private/ingest", help="Output base directory")
    args = parser.parse_args()

    ytdlp = find_ytdlp()
    root = Path(__file__).resolve().parent.parent
    out_base = root / args.out_dir
    out_base.mkdir(parents=True, exist_ok=True)

    meta_raw = subprocess.run(
        [ytdlp, "--dump-json", "--no-playlist", "--extractor-args", "youtube:player_client=android", args.url],
        capture_output=True, text=True, check=True,
    )
    meta = json.loads(meta_raw.stdout.splitlines()[0])
    vid = meta["id"]
    work_dir = out_base / vid
    work_dir.mkdir(parents=True, exist_ok=True)

    (work_dir / "meta.json").write_text(
        json.dumps({
            "id": vid,
            "title": meta.get("title"),
            "channel": meta.get("channel") or meta.get("uploader"),
            "duration": meta.get("duration"),
            "webpage_url": meta.get("webpage_url"),
        }, indent=2),
        encoding="utf-8",
    )

    # Try fast subtitle download first
    subprocess.run(
        [
            ytdlp, "--skip-download", "--write-auto-sub", "--write-sub",
            "--sub-lang", "en", "--sub-format", "vtt",
            "--extractor-args", "youtube:player_client=android",
            "-o", str(work_dir / "%(id)s.%(ext)s"), args.url,
        ],
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    vtts = list(work_dir.glob(f"{vid}*.vtt"))
    transcript_path = work_dir / "transcript.txt"
    if vtts:
        transcript_path.write_text(vtt_to_text(vtts[0]), encoding="utf-8")
        source = "subtitles"
    else:
        # Fallback: download audio + transcribe with py-tube's whisper or faster-whisper
        audio_out = work_dir / f"{vid}.mp3"
        subprocess.run(
            [
                ytdlp, "-x", "--audio-format", "mp3",
                "--extractor-args", "youtube:player_client=android",
                "-o", str(work_dir / "%(id)s.%(ext)s"), args.url,
            ],
            check=True,
        )
        whisper_exe = Path(r"C:\Github_Personal\py-tube\venv\Scripts\whisper.exe")
        if whisper_exe.exists():
            subprocess.run([str(whisper_exe), str(audio_out), "--model", "base", "--output_dir", str(work_dir), "--output_format", "txt"], check=True)
            txt_file = work_dir / f"{vid}.txt"
            if txt_file.exists():
                transcript_path.write_text(txt_file.read_text(encoding="utf-8"), encoding="utf-8")
        source = "whisper"

    print(json.dumps({"id": vid, "title": meta.get("title"), "channel": meta.get("channel"), "source": source, "transcript": str(transcript_path)}, indent=2))


if __name__ == "__main__":
    main()
