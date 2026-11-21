"""Re-render 03_aider_audio.mp4 from Aider-AI/aider and replace scheduled FB + YT posts."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from generate_repo_reel import render_reel
from publish_reel import load_env, publish_facebook_reel, resolve_page_token
from publish_youtube import get_access_token, upload_short

SGT = timezone(timedelta(hours=8))

CAPTION_FB = (
    "No bloated IDE needed. Aider edits multiple files across your local Git repo and writes "
    "clean commits automatically—right from your terminal.\n\n"
    "Repo: github.com/Aider-AI/aider\n\n"
    "#git #developertools #ai #coding #cli #dababonpro"
)

CAPTION_YT = (
    "No bloated IDE needed. Aider edits multiple files across your local Git repo and writes "
    "clean commits automatically—right from your terminal.\n\n"
    "Repo: https://github.com/Aider-AI/aider\n\n"
    "#git #developertools #ai #coding #shorts #dababonpro"
)


def delete_youtube_video(access_token: str, video_id: str) -> str:
    url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"}, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return f"deleted ({resp.status})"
    except urllib.error.HTTPError as exc:
        return f"delete_err {exc.code}: {exc.read().decode('utf-8', errors='replace')}"


def delete_fb_post(page_token: str, full_post_id: str, version: str = "v21.0") -> str:
    url = f"https://graph.facebook.com/{version}/{full_post_id}?access_token={urllib.parse.quote(page_token)}"
    req = urllib.request.Request(url, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return f"delete_err {exc.code}: {exc.read().decode('utf-8', errors='replace')}"


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    out_mp4 = root / "out" / "03_aider_audio.mp4"
    audio_mp3 = root / "assets" / "audio" / "synth_tech_loop.mp3"

    # 1. Re-render fixed video
    render_reel(
        repo_url="https://github.com/Aider-AI/aider",
        tag="Terminal Dev Tool • Open Source",
        hook="AI pair programming right inside your Git terminal",
        out_path=out_mp4,
        duration=18,
        fps=30,
        audio_path=audio_mp3,
    )
    print(f"Rendered fixed video: {out_mp4}")

    # 2. Replace on YouTube
    yt_token = get_access_token(root / "yt_client_secrets.json", root / "youtube_token.json")
    yt_del = delete_youtube_video(yt_token, "3ZmtnoTXOLA")
    yt_new = upload_short(
        access_token=yt_token,
        video_path=out_mp4,
        title="AI pair programming right inside your Git terminal (Aider) #Shorts",
        description=CAPTION_YT,
        privacy="private",
        publish_at="2026-11-25T01:00:00Z",
    )
    print("YouTube:", yt_del, "->", {"id": yt_new.get("id"), "status": yt_new.get("status")})

    # 3. Replace on Facebook
    load_env(root / ".env")
    page_id = os.environ["META_PAGE_ID"].strip()
    token = os.environ["META_PAGE_ACCESS_TOKEN"].strip()
    version = os.environ.get("META_GRAPH_VERSION", "v21.0").strip()
    page_token = resolve_page_token(page_id, token, version)

    fb_del = delete_fb_post(page_token, f"{page_id}_122137813106811547", version)
    sched_ts = int(datetime(2026, 11, 25, 9, 0, tzinfo=SGT).timestamp())
    fb_new = publish_facebook_reel(
        video_path=out_mp4,
        description=CAPTION_FB,
        page_id=page_id,
        token=token,
        graph_version=version,
        scheduled_unix=sched_ts,
    )
    print("Facebook:", fb_del, "->", json.dumps(fb_new))


if __name__ == "__main__":
    main()
