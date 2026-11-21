# DababonPro Reels Studio

Automated 9:16 AI educational Reels & Shorts pipeline, brand kit, and reusable AI agent skill (`skills/dababonpro-reels/SKILL.md`) for **Facebook Reels**, **YouTube Shorts**, and **TikTok**.

## Quickstart

**Prerequisites (native):** Python 3.11+ and `ffmpeg` on `PATH` (e.g. `winget install Gyan.FFmpeg`, `brew install ffmpeg`, or `apt install ffmpeg`).

```powershell
git clone https://github.com/dababonpro/dababonpro-reels.git
cd dababonpro-reels
pip install -r requirements.txt
playwright install chromium
```

Or with Docker (includes Python, `ffmpeg`, fonts, and Chromium):

```powershell
docker build -t dababonpro-reels .
# PowerShell:
docker run --rm -v "${PWD}/out:/app/out" dababonpro-reels scripts/generate_story_reel.py --storyboard content/examples/sample-story.json --out out/sample_story.mp4
```

*(On Linux/macOS bash, use `"$(pwd)/out:/app/out"`.)*

## Generate Videos

### Format A — GitHub Repo Spotlight (Scroll + Synth Audio)
```powershell
python scripts/generate_repo_reel.py `
  --repo https://github.com/firecrawl/firecrawl `
  --hook "Turn any website into clean LLM-ready Markdown" `
  --tag "AI Infrastructure • Open Source" `
  --audio assets/audio/synth_tech_loop.mp3 `
  --out out/01_firecrawl_audio.mp4
```

### Format B — Dynamic Story Reel (Neural TTS + Kinetic Captions)
```powershell
python scripts/generate_story_reel.py `
  --storyboard content/examples/sample-story.json `
  --out out/sample_story.mp4
```

### Verify Before Publishing
```powershell
python scripts/verify_reel.py out/*.mp4
```

## Publish & Docs

- **Setup & API Credentials:** [docs/GUIDE.md](docs/GUIDE.md)
- **Content Strategy & KPIs:** [STRATEGY.md](STRATEGY.md)
- **AI Agent Skill:** [skills/dababonpro-reels/SKILL.md](skills/dababonpro-reels/SKILL.md)
