"""Mux synth beat onto Reels 02-05 and schedule them across next week."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from publish_reel import load_env, publish_facebook_reel

SGT = timezone(timedelta(hours=8))

REELS = [
    {
        "id": "02_openhands",
        "in_mp4": "out/02_openhands.mp4",
        "out_mp4": "out/02_openhands_audio.mp4",
        "publish_at": datetime(2026, 11, 23, 9, 0, tzinfo=SGT),
        "caption": (
            "OpenHands (formerly OpenDevin) runs inside an isolated sandbox where it can write code, "
            "run terminal commands, and browse docs to fix real issues—fully open source.\n\n"
            "Repo: github.com/All-Hands-AI/OpenHands\n\n"
            "#aiagents #coding #opensource #softwareengineering #github #dababonpro"
        ),
    },
    {
        "id": "03_aider",
        "in_mp4": "out/03_aider.mp4",
        "out_mp4": "out/03_aider_audio.mp4",
        "publish_at": datetime(2026, 11, 25, 9, 0, tzinfo=SGT),
        "caption": (
            "No bloated IDE needed. Aider edits multiple files across your local Git repo and writes "
            "clean commits automatically—right from your terminal.\n\n"
            "Repo: github.com/aider-chat/aider\n\n"
            "#git #developertools #ai #coding #cli #dababonpro"
        ),
    },
    {
        "id": "04_smolagents",
        "in_mp4": "out/04_smolagents.mp4",
        "out_mp4": "out/04_smolagents_audio.mp4",
        "publish_at": datetime(2026, 11, 27, 9, 0, tzinfo=SGT),
        "caption": (
            "Heavy agent frameworks add too much boilerplate. Hugging Face's Smolagents keeps the core "
            "library around ~1,000 lines and lets agents write Python actions directly instead of fragile JSON blobs.\n\n"
            "Repo: github.com/huggingface/smolagents\n\n"
            "#huggingface #aiagents #python #opensource #ml #dababonpro"
        ),
    },
    {
        "id": "05_baml",
        "in_mp4": "out/05_baml.mp4",
        "out_mp4": "out/05_baml_audio.mp4",
        "publish_at": datetime(2026, 11, 28, 9, 0, tzinfo=SGT),
        "caption": (
            "If you've ever had a production app crash because an LLM returned invalid JSON, check out BAML. "
            "It gives you type-safe, schema-validated structured outputs across models.\n\n"
            "Repo: github.com/BoundaryML/baml\n\n"
            "#llm #typescript #python #aiengineering #devtools #dababonpro"
        ),
    },
]


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    load_env(root / ".env")
    page_id = os.environ["META_PAGE_ID"].strip()
    token = os.environ["META_PAGE_ACCESS_TOKEN"].strip()
    version = os.environ.get("META_GRAPH_VERSION", "v21.0").strip()
    audio_mp3 = root / "assets" / "audio" / "synth_tech_loop.mp3"

    results = []
    for item in REELS:
        in_path = root / item["in_mp4"]
        out_path = root / item["out_mp4"]
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(in_path),
                "-i",
                str(audio_mp3),
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                str(out_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        res = publish_facebook_reel(
            video_path=out_path,
            description=item["caption"],
            page_id=page_id,
            token=token,
            graph_version=version,
            scheduled_unix=int(item["publish_at"].timestamp()),
        )
        results.append({
            "id": item["id"],
            "scheduled_for": item["publish_at"].isoformat(),
            "response": res,
        })
        print(f"{item['id']} -> {item['publish_at'].isoformat()} -> {res}")

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
