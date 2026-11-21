"""Generate Format B (Dynamic Cuts + Neural Voiceover + Kinetic Captions) 9:16 Story Reels."""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import tempfile
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1080
HEIGHT = 1920
BG_COLOR = (11, 15, 23)
CARD_BG = (13, 17, 23)
TITLEBAR_BG = (22, 27, 34)
BORDER_COLOR = (48, 54, 61)
ACCENT = (56, 189, 248)
GREEN = (63, 185, 80)
TEXT_PRIMARY = (240, 246, 252)
TEXT_MUTED = (139, 148, 158)

CARD_X = 64
CARD_W = WIDTH - 128
CARD_Y = 430
CARD_H = 980


def load_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if mono:
        candidates = [
            "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ]
    elif bold:
        candidates = [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: int) -> list[str]:
    lines: list[str] = []
    for para in text.splitlines():
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur: list[str] = []
        for w in words:
            trial = " ".join([*cur, w])
            if draw.textbbox((0, 0), trial, font=font)[2] <= max_w or not cur:
                cur.append(w)
            else:
                lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))
    return lines


async def synth_scene_tts(text: str, out_mp3: Path, voice: str, rate: str, pitch: str) -> tuple[float, list[dict]]:
    """Synthesize speech and return (duration_sec, word_timings)."""
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    words: list[dict] = []
    audio_chunks = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.extend(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            words.append({
                "text": chunk["text"].upper(),
                "start": chunk["offset"] / 10_000_000.0,
                "end": (chunk["offset"] + chunk["duration"]) / 10_000_000.0,
            })
    out_mp3.write_bytes(bytes(audio_chunks))

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(out_mp3)],
        capture_output=True,
        text=True,
        check=True,
    )
    dur = float(probe.stdout.strip())
    return dur, words


def render_scene_card(scene: dict, root: Path) -> Image.Image:
    """Render the static background + top badge/headline + center visual card for one scene."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_tag = load_font(24, bold=True)
    font_head = load_font(46, bold=True)
    font_mono = load_font(26, mono=True)
    font_title = load_font(24, bold=True)
    font_footer = load_font(24, bold=True)

    # Top pill tag
    tag = scene.get("tag", "DababonPro • AI Workflow")
    tw = draw.textbbox((0, 0), tag, font=font_tag)[2] + 44
    tx = (WIDTH - tw) // 2
    draw.rounded_rectangle([tx, 130, tx + tw, 178], radius=24, fill=(18, 36, 62), outline=(31, 111, 235), width=2)
    draw.text((WIDTH // 2, 154), tag, font=font_tag, fill=(147, 197, 253), anchor="mm")

    # Scene headline
    y = 215
    for line in wrap_text(draw, scene["headline"], font_head, WIDTH - 140)[:3]:
        draw.text((WIDTH // 2, y), line, font=font_head, fill=TEXT_PRIMARY, anchor="mt")
        y += 58

    # Center macOS card
    draw.rounded_rectangle([CARD_X - 2, CARD_Y - 2, CARD_X + CARD_W + 2, CARD_Y + CARD_H + 2], radius=22, fill=CARD_BG, outline=BORDER_COLOR, width=2)
    draw.rounded_rectangle([CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + 54], radius=20, fill=TITLEBAR_BG)
    draw.rectangle([CARD_X, CARD_Y + 34, CARD_X + CARD_W, CARD_Y + 54], fill=TITLEBAR_BG)
    for idx, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = CARD_X + 26 + idx * 24
        draw.ellipse([cx - 7, CARD_Y + 20, cx + 7, CARD_Y + 34], fill=col)
    draw.text((CARD_X + CARD_W // 2, CARD_Y + 27), scene.get("window_title", "terminal — dababonpro-reels"), font=font_title, fill=TEXT_MUTED, anchor="mm")

    body_x = CARD_X + 36
    body_y = CARD_Y + 86
    body_w = CARD_W - 72
    body_h = CARD_H - 110

    if scene.get("image"):
        src = Image.open(root / scene["image"]).convert("RGB")
        scale = min(body_w / src.width, body_h / src.height)
        nw, nh = int(src.width * scale), int(src.height * scale)
        src = src.resize((nw, nh), Image.Resampling.LANCZOS)
        img.paste(src, (body_x + (body_w - nw) // 2, body_y + (body_h - nh) // 2))
    else:
        cy = body_y
        for raw_line in scene.get("terminal", []):
            for line in wrap_text(draw, raw_line, font_mono, body_w):
                color = GREEN if line.startswith("$") or line.startswith("[ok]") else (ACCENT if line.startswith("#") else TEXT_PRIMARY)
                draw.text((body_x, cy), line, font=font_mono, fill=color)
                cy += 38

    draw.text((WIDTH // 2, HEIGHT - 110), "DababonPro  •  github.com/dababonpro", font=font_footer, fill=TEXT_MUTED, anchor="mm")
    return img


def draw_kinetic_caption(frame: Image.Image, words: list[dict], local_t: float) -> Image.Image:
    if not words:
        return frame
    active_idx = -1
    for i, w in enumerate(words):
        if w["start"] <= local_t <= w["end"] + 0.12:
            active_idx = i
            break
    if active_idx == -1:
        # Pick closest previous word
        for i, w in enumerate(words):
            if w["start"] <= local_t:
                active_idx = i
    if active_idx == -1:
        return frame

    chunk_start = (active_idx // 3) * 3
    chunk = words[chunk_start : chunk_start + 3]
    draw = ImageDraw.Draw(frame)
    font = load_font(60, bold=True)

    gap = 20
    widths = [draw.textbbox((0, 0), c["text"], font=font)[2] for c in chunk]
    total_w = sum(widths) + gap * (len(chunk) - 1)
    x = (WIDTH - total_w) // 2
    y = 1500

    pad_x, pad_y = 16, 12
    for idx, item in enumerate(chunk):
        is_active = (chunk_start + idx) == active_idx
        w_text = item["text"]
        tw = widths[idx]
        if is_active:
            bx0, by0, bx1, by1 = draw.textbbox((x, y), w_text, font=font)
            draw.rounded_rectangle([bx0 - pad_x, by0 - pad_y, bx1 + pad_x, by1 + pad_y], radius=16, fill=(250, 204, 21))
            draw.text((x, y), w_text, font=font, fill=(11, 15, 23))
        else:
            draw.text((x, y), w_text, font=font, fill=TEXT_PRIMARY, stroke_width=6, stroke_fill=(0, 0, 0))
        x += tw + gap
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Format B Story Reel with TTS + kinetic captions.")
    parser.add_argument("--storyboard", required=True, help="Path to storyboard JSON")
    parser.add_argument("--out", required=True, help="Output MP4 path")
    parser.add_argument("--voice", default="en-US-ChristopherNeural", help="Edge TTS voice")
    parser.add_argument("--rate", default="+6%", help="TTS speech rate")
    parser.add_argument("--pitch", default="-8Hz", help="TTS pitch offset")
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    scenes = json.loads(Path(args.storyboard).read_text(encoding="utf-8"))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    music_mp3 = root / "assets" / "audio" / "synth_tech_loop.mp3"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        concat_list = tmp / "audio_list.txt"
        scene_meta = []

        async def build_all_tts() -> None:
            lines = []
            for idx, sc in enumerate(scenes):
                mp3 = tmp / f"sc_{idx:02d}.mp3"
                dur, words = await synth_scene_tts(sc["narration"], mp3, args.voice, args.rate, args.pitch)
                pad = 0.25
                padded_mp3 = tmp / f"sc_{idx:02d}_pad.mp3"
                subprocess.run(
                    ["ffmpeg", "-y", "-i", str(mp3), "-af", f"apad=pad_dur={pad}", "-t", f"{dur + pad:.3f}", str(padded_mp3)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                lines.append(f"file '{padded_mp3.as_posix()}'")
                scene_meta.append({"dur": dur + pad, "words": words, "card": render_scene_card(sc, root)})
            concat_list.write_text("\n".join(lines), encoding="utf-8")

        asyncio.run(build_all_tts())

        voice_mp3 = tmp / "voice_full.mp3"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c:a", "libmp3lame", "-b:a", "192k", str(voice_mp3)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Mix voiceover + -22dB synth music bed
        mixed_mp3 = tmp / "mixed.mp3"
        total_dur = sum(m["dur"] for m in scene_meta)
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(voice_mp3),
                "-stream_loop", "-1", "-i", str(music_mp3),
                "-filter_complex", f"[1:a]volume=-22dB[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[out]",
                "-map", "[out]", "-t", f"{total_dur:.3f}",
                "-c:a", "libmp3lame", "-b:a", "192k", str(mixed_mp3),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        ffmpeg_log = tmp / "ffmpeg_vid.log"
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{WIDTH}x{HEIGHT}", "-r", str(args.fps), "-i", "-",
            "-i", str(mixed_mp3),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
            str(out_path),
        ]
        with ffmpeg_log.open("w", encoding="utf-8") as log_f:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log_f)
            assert proc.stdin is not None
            for meta in scene_meta:
                n_frames = max(1, int(round(meta["dur"] * args.fps)))
                for f_idx in range(n_frames):
                    local_t = f_idx / args.fps
                    frame = meta["card"].copy()
                    frame = draw_kinetic_caption(frame, meta["words"], local_t)
                    proc.stdin.write(frame.tobytes())
            proc.stdin.close()
            ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"ffmpeg failed: {ffmpeg_log.read_text(encoding='utf-8', errors='replace')}")

    print(f"Done: {out_path} ({total_dur:.1f}s)")


if __name__ == "__main__":
    main()
