"""Generate 9:16 (1080x1920) GitHub Repo Spotlight Reels for DababonPro."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

WIDTH = 1080
HEIGHT = 1920
BG_COLOR = (11, 15, 23)
CARD_BG = (13, 17, 23)
TITLEBAR_BG = (22, 27, 34)
BORDER_COLOR = (48, 54, 61)
ACCENT_BG = (31, 111, 235)
TEXT_PRIMARY = (240, 246, 252)
TEXT_MUTED = (139, 148, 158)

WIN_X = 64
WIN_W = WIDTH - (WIN_X * 2)  # 952
WIN_Y = 390
WIN_H = 1220
TITLEBAR_H = 56
VIEWPORT_H = WIN_H - TITLEBAR_H


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
        ]
        if bold
        else [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
        ]
    )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join([*current, word])
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def capture_repo_screenshot(repo_url: str, out_png: Path, capture_width: int = 952, max_height: int = 3400) -> None:
    """Capture a clean dark-mode GitHub repo screenshot."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": capture_width, "height": 1400},
            device_scale_factor=1,
            color_scheme="dark",
        )
        page = context.new_page()
        resp = page.goto(repo_url, wait_until="networkidle", timeout=45000)
        if resp is not None and resp.status >= 400:
            raise RuntimeError(f"HTTP {resp.status} fetching {repo_url}")
        if "Page not found" in page.title():
            raise RuntimeError(f"GitHub 404 Page not found: {repo_url}")
        page.add_style_tag(
            content="""
            header, .AppHeader, .js-header-wrapper,
            .BorderGrid-cell:has(.js-social-count),
            #repository-container-header nav {
                /* keep layout clean, hide sticky chrome if needed */
            }
            .AppHeader { display: none !important; }
            """
        )
        page.wait_for_timeout(800)
        full_height = page.evaluate("() => document.body.scrollHeight")
        clip_h = min(int(full_height), max_height)
        page.screenshot(
            path=str(out_png),
            full_page=True,
            clip={"x": 0, "y": 0, "width": capture_width, "height": clip_h},
        )
        browser.close()


def build_base_frame(repo_url: str, tag: str, hook: str) -> Image.Image:
    """Create the static 1080x1920 background, header hook, window chrome, and footer."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_tag = load_font(26, bold=True)
    font_hook = load_font(48, bold=True)
    font_url = load_font(24, bold=False)
    font_footer = load_font(26, bold=True)

    # Top pill tag
    tag_bbox = draw.textbbox((0, 0), tag, font=font_tag)
    tag_w = (tag_bbox[2] - tag_bbox[0]) + 44
    tag_h = 50
    tag_x = (WIDTH - tag_w) // 2
    tag_y = 140
    draw.rounded_rectangle([tag_x, tag_y, tag_x + tag_w, tag_y + tag_h], radius=25, fill=(24, 38, 64), outline=ACCENT_BG, width=2)
    draw.text((WIDTH // 2, tag_y + tag_h // 2), tag, font=font_tag, fill=(147, 197, 253), anchor="mm")

    # Hook text
    lines = wrap_text(draw, hook, font_hook, max_width=WIDTH - 140)[:2]
    y_cursor = 225
    for line in lines:
        draw.text((WIDTH // 2, y_cursor), line, font=font_hook, fill=TEXT_PRIMARY, anchor="mt")
        y_cursor += 62

    # macOS window frame
    draw.rounded_rectangle(
        [WIN_X - 2, WIN_Y - 2, WIN_X + WIN_W + 2, WIN_Y + WIN_H + 2],
        radius=22,
        fill=CARD_BG,
        outline=BORDER_COLOR,
        width=2,
    )
    draw.rounded_rectangle(
        [WIN_X, WIN_Y, WIN_X + WIN_W, WIN_Y + TITLEBAR_H + 12],
        radius=20,
        fill=TITLEBAR_BG,
    )
    draw.rectangle([WIN_X, WIN_Y + TITLEBAR_H - 4, WIN_X + WIN_W, WIN_Y + TITLEBAR_H + 12], fill=TITLEBAR_BG)

    # Traffic lights
    dot_y = WIN_Y + TITLEBAR_H // 2
    for idx, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = WIN_X + 28 + (idx * 24)
        draw.ellipse([cx - 7, dot_y - 7, cx + 7, dot_y + 7], fill=color)

    # Address bar label
    parsed = urlparse(repo_url)
    short_url = f"{parsed.netloc}{parsed.path}".rstrip("/")
    draw.text((WIN_X + WIN_W // 2, dot_y), short_url, font=font_url, fill=TEXT_MUTED, anchor="mm")

    # Footer CTA (above Reels bottom UI)
    draw.text(
        (WIDTH // 2, WIN_Y + WIN_H + 58),
        "DababonPro  •  Save this repo for later",
        font=font_footer,
        fill=TEXT_MUTED,
        anchor="mm",
    )
    return img


def ease_in_out(t: float) -> float:
    return 0.5 * (1.0 - math.cos(math.pi * max(0.0, min(1.0, t))))


def render_reel(
    repo_url: str,
    tag: str,
    hook: str,
    out_path: Path,
    duration: int = 18,
    fps: int = 30,
    audio_path: Path | None = None,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        shot_path = Path(tmpdir) / "repo.png"
        capture_repo_screenshot(repo_url, shot_path, capture_width=WIN_W)

        repo_img = Image.open(shot_path).convert("RGB")
        if repo_img.width != WIN_W:
            new_h = int(repo_img.height * (WIN_W / repo_img.width))
            repo_img = repo_img.resize((WIN_W, new_h), Image.Resampling.LANCZOS)

        max_scroll = max(0, repo_img.height - VIEWPORT_H)
        base_frame = build_base_frame(repo_url, tag, hook)

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{WIDTH}x{HEIGHT}",
            "-r",
            str(fps),
            "-i",
            "-",
        ]
        if audio_path and audio_path.exists():
            fade_out_start = max(0.5, duration - 1.5)
            cmd.extend([
                "-i",
                str(audio_path),
                "-af",
                f"afade=t=in:st=0:d=0.5,afade=t=out:st={fade_out_start:.2f}:d=1.5",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
            ])
        cmd.extend([
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-movflags",
            "+faststart",
            str(out_path),
        ])

        ffmpeg_log = Path(tmpdir) / "ffmpeg.log"
        with ffmpeg_log.open("w", encoding="utf-8") as log_f:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log_f)
            assert proc.stdin is not None

            total_frames = duration * fps
            hold_start = int(1.5 * fps)
            hold_end = int(1.5 * fps)
            scroll_frames = max(1, total_frames - hold_start - hold_end)

            for frame_idx in range(total_frames):
                if frame_idx < hold_start:
                    progress = 0.0
                elif frame_idx >= total_frames - hold_end:
                    progress = 1.0
                else:
                    progress = ease_in_out((frame_idx - hold_start) / scroll_frames)

                scroll_y = int(round(max_scroll * progress))
                crop = repo_img.crop((0, scroll_y, WIN_W, scroll_y + VIEWPORT_H))
                frame = base_frame.copy()
                frame.paste(crop, (WIN_X, WIN_Y + TITLEBAR_H))
                proc.stdin.write(frame.tobytes())

            proc.stdin.close()
            ret = proc.wait()
        if ret != 0:
            stderr = ffmpeg_log.read_text(encoding="utf-8", errors="replace")
            raise RuntimeError(f"ffmpeg failed ({ret}): {stderr}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 9:16 GitHub Repo Spotlight Reels.")
    parser.add_argument("--repo", help="GitHub repository URL")
    parser.add_argument("--hook", help="Top hook text")
    parser.add_argument("--tag", default="AI Tool • Open Source", help="Top pill badge text")
    parser.add_argument("--out", help="Output MP4 path")
    parser.add_argument("--duration", type=int, default=18, help="Duration in seconds")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--audio", help="Optional background audio file (.mp3/.wav)")
    parser.add_argument("--batch", help="Path to JSON batch file")
    args = parser.parse_args()

    audio = Path(args.audio) if args.audio else None

    if args.batch:
        items = json.loads(Path(args.batch).read_text(encoding="utf-8"))
        for item in items:
            out_path = Path(item["out"])
            print(f"Rendering {item['id']} -> {out_path} ...")
            render_reel(
                repo_url=item["repo"],
                tag=item.get("tag", "AI Tool • Open Source"),
                hook=item["hook"],
                out_path=out_path,
                duration=int(item.get("duration", args.duration)),
                fps=args.fps,
                audio_path=audio,
            )
            print(f"Done: {out_path}")
        return

    if not args.repo or not args.hook or not args.out:
        parser.error("Provide --repo, --hook, and --out (or use --batch).")

    render_reel(
        repo_url=args.repo,
        tag=args.tag,
        hook=args.hook,
        out_path=Path(args.out),
        duration=args.duration,
        fps=args.fps,
        audio_path=audio,
    )
    print(f"Done: {args.out}")


if __name__ == "__main__":
    main()
