"""Upload launch-day Shorts (06, 07) as public and schedule 02-05 on YouTube."""

from __future__ import annotations

import json
from pathlib import Path

from publish_youtube import get_access_token, upload_short

ITEMS = [
    {
        "id": "06_dify",
        "video": "out/06_dify_audio.mp4",
        "title": "Visual AI workflow & RAG builder you can self-host (Dify) #Shorts",
        "description": (
            "Dify gives you a visual canvas for LLM workflows, RAG pipelines, and agent tools—plus full "
            "self-hosting so you own your data and prompts.\n\n"
            "Repo: https://github.com/langgenius/dify\n\n"
            "#ai #opensource #rag #llm #shorts #dababonpro"
        ),
        "privacy": "public",
        "publish_at": None,
    },
    {
        "id": "07_langgraph",
        "video": "out/07_langgraph_audio.mp4",
        "title": "Build stateful multi-agent loops you can control (LangGraph) #Shorts",
        "description": (
            "Simple prompt chains break on real tasks. LangGraph models your AI agents as stateful graphs "
            "with loops, retries, and human-in-the-loop checkpoints.\n\n"
            "Repo: https://github.com/langchain-ai/langgraph\n\n"
            "#aiagents #langgraph #python #opensource #shorts #dababonpro"
        ),
        "privacy": "public",
        "publish_at": None,
    },
    {
        "id": "02_openhands",
        "video": "out/02_openhands_audio.mp4",
        "title": "An open-source AI software engineer in a sandbox (OpenHands) #Shorts",
        "description": (
            "OpenHands (formerly OpenDevin) runs inside an isolated sandbox where it can write code, "
            "run terminal commands, and browse docs to fix real issues—fully open source.\n\n"
            "Repo: https://github.com/All-Hands-AI/OpenHands\n\n"
            "#aiagents #coding #opensource #shorts #dababonpro"
        ),
        "privacy": "private",
        "publish_at": "2026-11-23T01:00:00Z",  # Mon 09:00 SGT
    },
    {
        "id": "03_aider",
        "video": "out/03_aider_audio.mp4",
        "title": "AI pair programming right inside your Git terminal (Aider) #Shorts",
        "description": (
            "No bloated IDE needed. Aider edits multiple files across your local Git repo and writes "
            "clean commits automatically—right from your terminal.\n\n"
            "Repo: https://github.com/aider-chat/aider\n\n"
            "#git #developertools #ai #coding #shorts #dababonpro"
        ),
        "privacy": "private",
        "publish_at": "2026-11-25T01:00:00Z",  # Wed 09:00 SGT
    },
    {
        "id": "04_smolagents",
        "video": "out/04_smolagents_audio.mp4",
        "title": "Build code-writing AI agents in ~1,000 lines (Smolagents) #Shorts",
        "description": (
            "Heavy agent frameworks add too much boilerplate. Hugging Face's Smolagents keeps the core "
            "library around ~1,000 lines and lets agents write Python actions directly.\n\n"
            "Repo: https://github.com/huggingface/smolagents\n\n"
            "#huggingface #aiagents #python #opensource #shorts #dababonpro"
        ),
        "privacy": "private",
        "publish_at": "2026-11-27T01:00:00Z",  # Fri 09:00 SGT
    },
    {
        "id": "05_baml",
        "video": "out/05_baml_audio.mp4",
        "title": "Stop fighting broken JSON outputs from LLMs (BAML) #Shorts",
        "description": (
            "If you've ever had a production app crash because an LLM returned invalid JSON, check out BAML. "
            "It gives you type-safe, schema-validated structured outputs across models.\n\n"
            "Repo: https://github.com/BoundaryML/baml\n\n"
            "#llm #typescript #python #aiengineering #shorts #dababonpro"
        ),
        "privacy": "private",
        "publish_at": "2026-11-28T01:00:00Z",  # Sat 09:00 SGT
    },
]


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    token = get_access_token(root / "yt_client_secrets.json", root / "youtube_token.json")
    results = []
    for item in ITEMS:
        res = upload_short(
            access_token=token,
            video_path=root / item["video"],
            title=item["title"],
            description=item["description"],
            privacy=item["privacy"],
            publish_at=item["publish_at"],
        )
        entry = {
            "id": item["id"],
            "video_id": res.get("id"),
            "privacy": res.get("status", {}).get("privacyStatus"),
            "publish_at": res.get("status", {}).get("publishAt"),
        }
        results.append(entry)
        print(entry)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
