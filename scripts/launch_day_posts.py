"""Generate and publish 2 launch-day Reels (Dify, LangGraph) + 1 Welcome text post."""

from __future__ import annotations

import json
import os
from pathlib import Path

from generate_repo_reel import render_reel
from publish_reel import load_env, post_form, publish_facebook_reel, resolve_page_token

LAUNCH_REELS = [
    {
        "id": "06_dify",
        "repo": "https://github.com/langgenius/dify",
        "tag": "AI Platform • Open Source",
        "hook": "Visual AI workflow & RAG builder you can self-host",
        "out": "out/06_dify_audio.mp4",
        "caption": (
            "Dify gives you a visual canvas for LLM workflows, RAG pipelines, and agent tools—plus full "
            "self-hosting so you own your data and prompts.\n\n"
            "Repo: github.com/langgenius/dify\n\n"
            "#ai #opensource #rag #llm #selfhosted #dababonpro"
        ),
    },
    {
        "id": "07_langgraph",
        "repo": "https://github.com/langchain-ai/langgraph",
        "tag": "Agent Orchestration • Open Source",
        "hook": "Build stateful multi-agent loops you can actually control",
        "out": "out/07_langgraph_audio.mp4",
        "caption": (
            "Simple prompt chains break on real tasks. LangGraph models your AI agents as stateful graphs "
            "with loops, retries, and human-in-the-loop checkpoints.\n\n"
            "Repo: github.com/langchain-ai/langgraph\n\n"
            "#aiagents #langgraph #python #opensource #aiengineering #dababonpro"
        ),
    },
]

WELCOME_POST = (
    "Welcome to DababonPro!\n\n"
    "We share practical AI tools, open-source GitHub spotlights, and real-world systems engineering "
    "workflows—without the hype.\n\n"
    "What you'll see here every week:\n"
    "• High-signal open-source AI repos worth bookmarking\n"
    "• Practical agent & automation workflows\n"
    "• Engineering breakdowns from DababonPro IT Solutions\n\n"
    "Follow the page and save the Reels you want to try next."
)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    load_env(root / ".env")
    page_id = os.environ["META_PAGE_ID"].strip()
    token = os.environ["META_PAGE_ACCESS_TOKEN"].strip()
    version = os.environ.get("META_GRAPH_VERSION", "v21.0").strip()
    audio_mp3 = root / "assets" / "audio" / "synth_tech_loop.mp3"

    results = []
    for item in LAUNCH_REELS:
        out_path = root / item["out"]
        render_reel(
            repo_url=item["repo"],
            tag=item["tag"],
            hook=item["hook"],
            out_path=out_path,
            duration=18,
            fps=30,
            audio_path=audio_mp3,
        )
        res = publish_facebook_reel(
            video_path=out_path,
            description=item["caption"],
            page_id=page_id,
            token=token,
            graph_version=version,
        )
        results.append({"id": item["id"], "response": res})
        print(f"Published {item['id']}: {res}")

    page_token = resolve_page_token(page_id, token, version)
    welcome_res = post_form(
        f"https://graph.facebook.com/{version}/{page_id}/feed",
        {"message": WELCOME_POST, "access_token": page_token},
    )
    results.append({"id": "welcome_post", "response": welcome_res})
    print(f"Published welcome_post: {welcome_res}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
