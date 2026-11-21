# DababonPro Reels Studio

Automated content production & strategy kit for **DababonPro** AI educational Reels (Facebook Reels, Instagram Reels, YouTube Shorts, LinkedIn, TikTok).

## 1. Recommended Page Bio (Facebook & Instagram)

Replace the pure agency bio with one that bridges **AI education** and **DababonPro IT Solutions**:

> Practical AI tools, open-source workflows, and systems engineering — by DababonPro IT Solutions.

## 2. Weekly Content Cadence (5 Reels / Week)

- **Mon / Wed / Fri — GitHub Repo Spotlight (18–22s):** High-save format. Dark-mode repo card, 1-line hook, smooth scroll over README/demo, native trending audio or lo-fi track.
- **Tue — Tool-in-Action Story (30–45s):** Real problem solved end-to-end (screen recording or workflow walkthrough).
- **Thu — Concept Explainer (30–45s):** Character/slide explainer (*MCP vs. APIs*, *When to use agents vs. scripts*).

## 3. Generate a Repo Spotlight Reel

Requires Python 3.11+, `playwright`, `pillow`, and `ffmpeg`.

```powershell
python scripts/generate_repo_reel.py `
  --repo https://github.com/mendableai/firecrawl `
  --hook "Turn any website into clean LLM-ready Markdown" `
  --tag "AI Infrastructure • Open Source" `
  --out out/01_firecrawl.mp4
```

Optional flags:
- `--audio path/to/track.mp3` — mix background music with fade-out.
- `--duration 18` — video length in seconds (default `18`).
- `--fps 30` — frame rate (default `30`).
- `--batch content/week-01-batch.json` — render all repo reels in a batch file.

## 4. Cross-Posting Checklist

1. **Facebook + Instagram:** Schedule together in **Meta Business Suite** (add native trending audio if rendered silent).
2. **YouTube Shorts:** Upload the same `1080x1920` `.mp4` with `#Shorts` and the repo link in the description/pinned comment.
3. **LinkedIn:** Post natively with a 3-line business-outcome caption (who this saves time/money for).
4. **TikTok:** Upload with the same hook as on-screen text for search indexing.
