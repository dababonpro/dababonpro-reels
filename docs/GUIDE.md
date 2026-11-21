# End-to-End Setup & Automation Guide

This guide documents the complete setup for running **DababonPro** across Facebook Reels, YouTube Shorts, and TikTok from a single local repository.

## 1. Prerequisites

- Python 3.11+ with `playwright` and `pillow`
- `ffmpeg` on `PATH`

## 2. Brand Assets (`assets/`)

Run `python scripts/generate_brand_assets.py` to generate cohesive dark-mode (`#0b0f17` + `#388bfd`) assets:
- `profile.png` (`1024x1024`) — Facebook, YouTube, TikTok avatar
- `cover.png` (`1640x624`) — Facebook Page cover (mobile safe-zone centered)
- `youtube_banner.png` (`2560x1440`) — YouTube Studio banner (`1546x423` safe-zone centered)
- `youtube_watermark.png` (`150x150`) — YouTube desktop video watermark

## 3. Meta Graph API Setup (Facebook Reels)

1. In `developers.facebook.com`, create an app with the **Manage everything on your Page** use case and enable `pages_manage_posts`, `pages_read_engagement`, and `pages_show_list`.
2. In `business.facebook.com/latest/settings`, create an **Admin System User**, assign both **Pages → DababonPro (Full control)** and **Accounts → Apps → DababonPro (Full control)**, then generate a token with those 3 permissions.
3. Save `META_PAGE_ID` and `META_PAGE_ACCESS_TOKEN` in `.env` and verify with:
   ```powershell
   python scripts/publish_reel.py --check
   ```

## 4. YouTube Data API v3 Setup (Shorts)

1. In `console.cloud.google.com`, enable **YouTube Data API v3**, configure the OAuth consent screen (External, add your email as a Test User), and create a **Desktop app** OAuth Client ID.
2. Save the downloaded JSON as `yt_client_secrets.json` in the repo root.
3. Run 1-time auth in an interactive terminal (select the Brand Channel, not personal):
   ```powershell
   python scripts/publish_youtube.py --auth-only
   ```

## 5. TikTok Setup

TikTok's Content Posting API requires app review for public posts and does not support API scheduling. Upload the same unwatermarked `.mp4` files via `tiktok.com/tiktokstudio/upload` with **Location** blank and **High-quality uploads** enabled.
