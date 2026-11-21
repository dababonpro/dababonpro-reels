"""Render a 9:16 Reel from your own voice recording (.m4a/.mp3/.wav) with auto-cleanup,
local Whisper word-level yellow-pill captions, and optional --intro-clip."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel
from PIL import Image

from generate_repo_reel import (
    HEIGHT,
    TITLEBAR_H,
    VIEWPORT_H,
    WIDTH,
    WIN_W,
    WIN_X,
    WIN_Y,
    build_base_frame,
    capture_repo_screenshot,
    ease_in_out,
)
from generate_story_reel import draw_kinetic_caption, render_scene_card


def clean_voice_audio(src_audio: Path, out_mp3: Path) -> float:
    """Trim silence, high-pass filter, and normalize voiceover audio; return duration in seconds."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src_audio),
            "-af", "highpass=f=80,silenceremove=start_periods=1:start_silence=0.15:start_threshold=-45dB,loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:a", "libmp3lame", "-b:a", "192k", str(out_mp3),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(out_mp3)],
        capture_output=True, text=True, check=True,
    )
    return float(probe.stdout.strip())


def transcribe_words(audio_mp3: Path, model_size: str = "tiny.en") -> list[dict]:
    """Transcribe audio locally with faster-whisper (via 16kHz WAV to bypass PyAV) and return uppercase word timings."""
    wav_16k = audio_mp3.with_suffix(".16k.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(audio_mp3), "-ar", "16000", "-ac", "1", "-f", "wav", str(wav_16k)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    with wave.open(str(wav_16k), "rb") as wf:
        pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(pcm, word_timestamps=True)
    words: list[dict] = []
    for seg in segments:
        for w in seg.words or []:
            txt = w.word.strip()
            if txt:
                words.append({"text": txt.upper(), "start": float(w.start), "end": float(w.end)})
    return words


def main() -> None:
    parser = argparse.ArgumentParser(description="Render 9:16 Reel from your own voice recording.")
    parser.add_argument("--voice-audio", required=True, help="Path to your voice recording (.m4a/.mp3/.wav)")
    parser.add_argument("--out", required=True, help="Output MP4 path")
    parser.add_argument("--repo", help="GitHub repo URL (for scrolling repo background)")
    parser.add_argument("--hook", default="", help="Top hook text (required with --repo)")
    parser.add_argument("--tag", default="DababonPro • Breakdown", help="Top pill badge")
    parser.add_argument("--storyboard", help="Optional storyboard JSON (splits evenly across recording)")
    parser.add_argument("--intro-clip", help="Optional 5-8s MP4 intro clip to prepend (cropped to 9:16)")
    parser.add_argument("--whisper-model", default="tiny.en", help="Whisper model size (tiny.en/base/small)")
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()

    if not args.repo and not args.storyboard:
        parser.error("Provide either --repo or --storyboard.")

    root = Path(__file__).resolve().parent.parent
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    music_mp3 = root / "assets" / "audio" / "synth_tech_loop.mp3"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        clean_mp3 = tmp / "voice_clean.mp3"
        dur = clean_voice_audio(Path(args.voice_audio), clean_mp3)
        words = transcribe_words(clean_mp3, model_size=args.whisper_model)

        mixed_mp3 = tmp / "mixed.mp3"
        if music_mp3.exists():
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", str(clean_mp3), "-stream_loop", "-1", "-i", str(music_mp3),
                    "-filter_complex", "[1:a]volume=-24dB[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[out]",
                    "-map", "[out]", "-t", f"{dur:.3f}", "-c:a", "libmp3lame", "-b:a", "192k", str(mixed_mp3),
                ],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        else:
            mixed_mp3 = clean_mp3

        body_mp4 = tmp / "body.mp4" if args.intro_clip else out_path
        total_frames = max(1, int(round(dur * args.fps)))

        if args.repo:
            shot_path = tmp / "repo.png"
            capture_repo_screenshot(args.repo, shot_path, capture_width=WIN_W)
            repo_img = Image.open(shot_path).convert("RGB")
            if repo_img.width != WIN_W:
                repo_img = repo_img.resize((WIN_W, int(repo_img.height * (WIN_W / repo_img.width))), Image.Resampling.LANCZOS)
            max_scroll = max(0, repo_img.height - VIEWPORT_H)
            base_frame = build_base_frame(args.repo, args.tag, args.hook)
        else:
            scenes = json.loads(Path(args.storyboard).read_text(encoding="utf-8"))
            cards = [render_scene_card(sc, root) for sc in scenes]

        ffmpeg_log = tmp / "ffmpeg.log"
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{WIDTH}x{HEIGHT}", "-r", str(args.fps), "-i", "-", "-i", str(mixed_mp3),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(body_mp4),
        ]
        with ffmpeg_log.open("w", encoding="utf-8") as log_f:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log_f)
            assert proc.stdin is not None
            for f_idx in range(total_frames):
                t = f_idx / args.fps
                if args.repo:
                    progress = ease_in_out(f_idx / max(1, total_frames - 1))
                    sy = int(round(max_scroll * progress))
                    frame = base_frame.copy()
                    frame.paste(repo_img.crop((0, sy, WIN_W, sy + VIEWPORT_H)), (WIN_X, WIN_Y + TITLEBAR_H))
                else:
                    sc_idx = min(len(cards) - 1, int((f_idx / total_frames) * len(cards)))
                    frame = cards[sc_idx].copy()
                frame = draw_kinetic_caption(frame, words, t)
                proc.stdin.write(frame.tobytes())
            proc.stdin.close()
            ret = proc.wait()
        if ret != 0:
            raise RuntimeError(ffmpeg_log.read_text(encoding="utf-8", errors="replace"))

        if args.intro_clip:
            intro_norm = tmp / "intro_916.mp4"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", str(args.intro_clip),
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(intro_norm),
                ],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            concat_txt = tmp / "concat.txt"
            concat_txt.write_text(f"file '{intro_norm.as_posix()}'\nfile '{body_mp4.as_posix()}'\n", encoding="utf-8")
            subprocess.run(
                ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", "-movflags", "+faststart", str(out_path)],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

    print(f"Done: {out_path} ({dur:.1f}s)")


if __name__ == "__main__":
    main()
