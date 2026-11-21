---
name: dababonpro-reels
description: End-to-end workflow for generating 9:16 AI/dev educational Reels, brand assets, and publishing/scheduling to Facebook Reels, YouTube Shorts, and TikTok.
---

# DababonPro Faceless Reels Pipeline

Use this skill to research topics, generate 9:16 vertical videos, and publish or schedule them across **Facebook Reels**, **YouTube Shorts**, and **TikTok**.

## Repository Layout

- `scripts/generate_brand_assets.py` — Generates `profile.png` (`1024x1024`), `cover.png` (`1640x624`), `youtube_banner.png` (`2560x1440`), and `youtube_watermark.png` (`150x150`).
- `scripts/generate_repo_reel.py` — Captures dark-mode GitHub repos via Playwright (with HTTP 404 guard), composites a 1080x1920 macOS frame, and pipes frames to FFmpeg.
- `scripts/generate_synth_beat.py` — Generates a royalty-free lo-fi/synthwave loop (`assets/audio/synth_tech_loop.mp3`).
- `scripts/publish_reel.py` — Publishes or schedules Reels to a Facebook Page via Meta Graph API (auto-exchanges System User token for Page-scoped token).
- `scripts/publish_youtube.py` — Uploads/schedules YouTube Shorts via YouTube Data API v3 (zero-dependency OAuth2).
- `STRATEGY.md` — 2026 short-form length, hook, pacing, audio, and KPI targets.

## Procedure

1. **Draft & Review Scripts First (Before Rendering)**
   - For explainer or story series, draft all scripts in a single Markdown doc first (e.g., `content/explainers/SERIES_SCRIPTS.md`) before generating TTS or MP4s to save render/token cost.
   - Use simple everyday analogies, a consistent mental model (model generates text; tools/instructions let an assistant search or act), and one short spoken CTA + on-screen series badge.
   - **Editorial accuracy gate:** Remove absolute claims (*"always"*, *"every time"*, *"stops all errors"*), qualify limits honestly, and check 25–30s spoken pacing before converting to storyboards.
2. **Pick & Validate Repos (for Repo Spotlights)**
   - Verify each GitHub URL returns HTTP 200 before rendering (`generate_repo_reel.py` enforces this automatically).
   - Write a `< 60` char hook focused on a frustration or concrete utility (*"Stop fighting..."* / *"Turn any X into Y"*).
3. **Render 9:16 Videos**
   - Single video:
     ```powershell
     python scripts/generate_repo_reel.py --repo <url> --tag "<Category • Open Source>" --hook "<Hook>" --audio assets/audio/synth_tech_loop.mp3 --out out/<slug>.mp4
     ```
   - Batch:
     ```powershell
     python scripts/generate_repo_reel.py --batch content/week-01-batch.json --audio assets/audio/synth_tech_loop.mp3
     ```
4. **Verify Before Publishing (Required Gate)**
   - Run `python scripts/verify_reel.py out/*.mp4` to confirm `1080x1920`, `h264`/`yuv420p`, duration `8–60s`, and non-silent audio (`> -60 dB`).
5. **Publish / Schedule**
   - **Facebook:** `python scripts/publish_reel.py --video <mp4> --caption "<caption>" [--schedule <unix_ts>]`
   - **YouTube Shorts:** `python scripts/publish_youtube.py --video <mp4> --title "<Title> #Shorts" --description "<desc>" --privacy public` (or `--privacy private --publish-at <ISO-UTC>`)
   - **TikTok:** Upload manually via `tiktok.com/tiktokstudio/upload` (leave Location blank, keep High-quality uploads ON, AI-generated content OFF for real repo captures).
6. **Measure & Iterate**
   - Review **Viewed vs. Swiped Away %** (`> 65%`), **Avg % Viewed** (`> 85%`), and **Saves / Likes** (`> 2x`) per [STRATEGY.md](../../STRATEGY.md).
