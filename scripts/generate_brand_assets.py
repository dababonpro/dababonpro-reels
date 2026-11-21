"""Generate DababonPro Facebook/Instagram profile picture and cover photo."""

from __future__ import annotations

from pathlib import Path
from playwright.sync_api import sync_playwright

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

PROFILE_HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1024px;
    height: 1024px;
    background: #070b12;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    position: relative;
    overflow: hidden;
  }
  .grid {
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(56,139,253,0.06) 1px, transparent 1px),
      linear-gradient(90deg, rgba(56,139,253,0.06) 1px, transparent 1px);
    background-size: 48px 48px;
  }
  .glow {
    position: absolute;
    width: 820px;
    height: 820px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(31,111,235,0.34) 0%, rgba(14,165,233,0.10) 45%, transparent 72%);
  }
  .hud-svg {
    position: absolute;
    inset: 0;
    width: 1024px;
    height: 1024px;
  }
  .core {
    position: relative;
    width: 720px;
    height: 720px;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 2;
  }
  .prompt-badge {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 8px 22px;
    border-radius: 999px;
    background: rgba(13, 25, 48, 0.85);
    border: 1.5px solid rgba(56, 189, 248, 0.55);
    color: #7dd3fc;
    font-family: "Consolas", "Cascadia Code", monospace;
    font-size: 26px;
    font-weight: 700;
    letter-spacing: 2px;
    margin-bottom: 22px;
    box-shadow: 0 0 24px rgba(56, 189, 248, 0.22);
  }
  .wordmark {
    font-size: 112px;
    font-weight: 800;
    letter-spacing: -3px;
    line-height: 1;
    color: #f0f6fc;
    text-shadow: 0 0 36px rgba(56, 139, 253, 0.45);
  }
  .wordmark span {
    color: #38bdf8;
  }
  .sub {
    margin-top: 22px;
    font-family: "Consolas", "Cascadia Code", monospace;
    font-size: 24px;
    font-weight: 600;
    letter-spacing: 5px;
    text-transform: uppercase;
    color: #8b949e;
  }
</style>
</head>
<body>
  <div class="grid"></div>
  <div class="glow"></div>
  <svg class="hud-svg" viewBox="0 0 1024 1024" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- Outer segmented tech HUD ring -->
    <circle cx="512" cy="512" r="415" stroke="#1f6feb" stroke-opacity="0.35" stroke-width="3" stroke-dasharray="48 20 12 20" />
    <circle cx="512" cy="512" r="385" stroke="#38bdf8" stroke-opacity="0.5" stroke-width="2" stroke-dasharray="140 80" />
    <circle cx="512" cy="512" r="355" stroke="#30363d" stroke-width="2" />
    <!-- Circuit traces -->
    <path d="M120 340 H210 L250 380" stroke="#38bdf8" stroke-opacity="0.45" stroke-width="3" stroke-linecap="round"/>
    <circle cx="250" cy="380" r="6" fill="#38bdf8" fill-opacity="0.8"/>
    <path d="M904 340 H814 L774 380" stroke="#38bdf8" stroke-opacity="0.45" stroke-width="3" stroke-linecap="round"/>
    <circle cx="774" cy="380" r="6" fill="#38bdf8" fill-opacity="0.8"/>
    <path d="M140 690 H230 L270 650" stroke="#1f6feb" stroke-opacity="0.55" stroke-width="3" stroke-linecap="round"/>
    <circle cx="270" cy="650" r="6" fill="#3fb950" fill-opacity="0.85"/>
    <path d="M884 690 H794 L754 650" stroke="#1f6feb" stroke-opacity="0.55" stroke-width="3" stroke-linecap="round"/>
    <circle cx="754" cy="650" r="6" fill="#3fb950" fill-opacity="0.85"/>
  </svg>
  <div class="core">
    <div class="prompt-badge">&gt;_ AI.DEV</div>
    <div class="wordmark">Dababon<span>Pro</span></div>
    <div class="sub">OPEN SOURCE • AGENTS</div>
  </div>
</body>
</html>
"""

COVER_HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1640px;
    height: 624px;
    background: #0b0f17;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    position: relative;
    overflow: hidden;
    color: #f0f6fc;
  }
  .grid {
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 48px 48px;
  }
  .glow-left {
    position: absolute;
    left: 160px;
    top: -120px;
    width: 700px;
    height: 700px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(31,111,235,0.22) 0%, transparent 70%);
  }
  .glow-right {
    position: absolute;
    right: 120px;
    bottom: -180px;
    width: 650px;
    height: 650px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(56,139,253,0.16) 0%, transparent 70%);
  }
  .safe-zone {
    position: relative;
    width: 1120px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    z-index: 1;
  }
  .pill {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    padding: 10px 26px;
    border-radius: 999px;
    background: rgba(31, 111, 235, 0.16);
    border: 1.5px solid rgba(56, 139, 253, 0.55);
    color: #93c5fd;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 28px;
  }
  .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #3fb950;
  }
  h1 {
    font-size: 92px;
    font-weight: 800;
    letter-spacing: -2px;
    line-height: 1.05;
    margin-bottom: 20px;
  }
  h1 span {
    color: #388bfd;
  }
  p {
    font-size: 32px;
    font-weight: 500;
    color: #8b949e;
    letter-spacing: 0.3px;
  }
</style>
</head>
<body>
  <div class="grid"></div>
  <div class="glow-left"></div>
  <div class="glow-right"></div>
  <div class="safe-zone">
    <div class="pill"><span class="dot"></span>DababonPro IT Solutions</div>
    <h1>Dababon<span>Pro</span></h1>
    <p>AI Tools &nbsp;•&nbsp; Open-Source Workflows &nbsp;•&nbsp; Systems Engineering</p>
  </div>
</body>
</html>
"""


YOUTUBE_BANNER_HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 2560px;
    height: 1440px;
    background: #0b0f17;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    position: relative;
    overflow: hidden;
    color: #f0f6fc;
  }
  .grid {
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(56,139,253,0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(56,139,253,0.04) 1px, transparent 1px);
    background-size: 64px 64px;
  }
  .glow-center {
    position: absolute;
    width: 1400px;
    height: 800px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(31,111,235,0.22) 0%, transparent 70%);
  }
  /* YouTube safe zone for all devices: 1546 x 423 centered */
  .safe-zone {
    position: relative;
    width: 1400px;
    height: 380px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    z-index: 1;
  }
  .pill {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    padding: 8px 24px;
    border-radius: 999px;
    background: rgba(31, 111, 235, 0.16);
    border: 1.5px solid rgba(56, 139, 253, 0.55);
    color: #93c5fd;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 22px;
  }
  .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #3fb950;
  }
  h1 {
    font-size: 88px;
    font-weight: 800;
    letter-spacing: -2px;
    line-height: 1.05;
    margin-bottom: 16px;
  }
  h1 span {
    color: #388bfd;
  }
  p {
    font-size: 28px;
    font-weight: 500;
    color: #8b949e;
  }
</style>
</head>
<body>
  <div class="grid"></div>
  <div class="glow-center"></div>
  <div class="safe-zone">
    <div class="pill"><span class="dot"></span>DababonPro IT Solutions</div>
    <h1>Dababon<span>Pro</span></h1>
    <p>AI Tools &nbsp;•&nbsp; Open-Source Workflows &nbsp;•&nbsp; Systems Engineering</p>
  </div>
</body>
</html>
"""


YOUTUBE_WATERMARK_HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 150px;
    height: 150px;
    background: #070b12;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    border: 3px solid #388bfd;
    border-radius: 22px;
  }
  .mark {
    font-size: 62px;
    font-weight: 800;
    letter-spacing: -2px;
    color: #f0f6fc;
  }
  .mark span { color: #38bdf8; }
</style>
</head>
<body>
  <div class="mark">D<span>P</span></div>
</body>
</html>
"""


GITHUB_SOCIAL_HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1280px;
    height: 640px;
    background: #070b12;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    position: relative;
    overflow: hidden;
    color: #f0f6fc;
  }
  .grid {
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(56,139,253,0.05) 1px, transparent 1px),
      linear-gradient(90deg, rgba(56,139,253,0.05) 1px, transparent 1px);
    background-size: 48px 48px;
  }
  .glow {
    position: absolute;
    width: 900px;
    height: 520px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(31,111,235,0.26) 0%, transparent 70%);
  }
  .card {
    position: relative;
    z-index: 1;
    width: 1120px;
    padding: 56px 64px;
    border-radius: 28px;
    background: rgba(13, 17, 23, 0.88);
    border: 2px solid #30363d;
    display: flex;
    flex-direction: column;
    gap: 24px;
    box-shadow: 0 24px 80px rgba(0,0,0,0.55);
  }
  .pill {
    align-self: flex-start;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 8px 20px;
    border-radius: 999px;
    background: rgba(31,111,235,0.16);
    border: 1.5px solid rgba(56,189,248,0.55);
    color: #7dd3fc;
    font-family: "Consolas", monospace;
    font-size: 20px;
    font-weight: 700;
  }
  h1 {
    font-size: 68px;
    font-weight: 800;
    letter-spacing: -2px;
    line-height: 1.08;
  }
  h1 span { color: #38bdf8; }
  p {
    font-size: 28px;
    color: #8b949e;
    line-height: 1.4;
  }
  .chips {
    display: flex;
    gap: 14px;
    margin-top: 8px;
  }
  .chip {
    padding: 8px 18px;
    border-radius: 10px;
    background: #161b22;
    border: 1px solid #30363d;
    color: #c9d1d9;
    font-family: "Consolas", monospace;
    font-size: 18px;
  }
</style>
</head>
<body>
  <div class="grid"></div>
  <div class="glow"></div>
  <div class="card">
    <div class="pill">&gt;_ dababonpro/dababonpro-reels</div>
    <h1>Automated <span>9:16 Reels</span> &amp; AI Skill</h1>
    <p>Playwright + FFmpeg + Neural TTS pipeline for Facebook Reels, YouTube Shorts, and TikTok.</p>
    <div class="chips">
      <div class="chip">Meta Graph API</div>
      <div class="chip">YouTube Data API v3</div>
      <div class="chip">SKILL.md</div>
      <div class="chip">MP4 Verifier</div>
    </div>
  </div>
</body>
</html>
"""


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Profile picture (1024x1024)
        page = browser.new_page(viewport={"width": 1024, "height": 1024}, device_scale_factor=1)
        page.set_content(PROFILE_HTML)
        profile_out = ASSETS_DIR / "profile.png"
        page.screenshot(path=str(profile_out))
        page.close()

        # Cover photo (1640x624)
        page = browser.new_page(viewport={"width": 1640, "height": 624}, device_scale_factor=1)
        page.set_content(COVER_HTML)
        cover_out = ASSETS_DIR / "cover.png"
        page.screenshot(path=str(cover_out))
        page.close()

        # YouTube banner (2560x1440)
        page = browser.new_page(viewport={"width": 2560, "height": 1440}, device_scale_factor=1)
        page.set_content(YOUTUBE_BANNER_HTML)
        yt_out = ASSETS_DIR / "youtube_banner.png"
        page.screenshot(path=str(yt_out))
        page.close()

        # YouTube watermark (150x150)
        page = browser.new_page(viewport={"width": 150, "height": 150}, device_scale_factor=1)
        page.set_content(YOUTUBE_WATERMARK_HTML)
        wm_out = ASSETS_DIR / "youtube_watermark.png"
        page.screenshot(path=str(wm_out))
        page.close()

        # GitHub social preview (1280x640)
        page = browser.new_page(viewport={"width": 1280, "height": 640}, device_scale_factor=1)
        page.set_content(GITHUB_SOCIAL_HTML)
        gh_out = ASSETS_DIR / "github_social_preview.png"
        page.screenshot(path=str(gh_out))
        page.close()

        browser.close()

    print(f"Generated: {profile_out}")
    print(f"Generated: {cover_out}")
    print(f"Generated: {yt_out}")
    print(f"Generated: {wm_out}")
    print(f"Generated: {gh_out}")


if __name__ == "__main__":
    main()
