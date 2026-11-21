"""Publish or schedule a 9:16 Reel to a Facebook Page via the Meta Graph API."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def load_env(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def post_form(url: str, data: dict[str, str]) -> dict:
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=encoded, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Meta API error {exc.code}: {body}") from exc


def upload_video_binary(upload_url: str, token: str, video_path: Path) -> dict:
    video_bytes = video_path.read_bytes()
    headers = {
        "Authorization": f"OAuth {token}",
        "offset": "0",
        "file_size": str(len(video_bytes)),
        "Content-Type": "application/octet-stream",
    }
    req = urllib.request.Request(upload_url, data=video_bytes, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Meta upload error {exc.code}: {body}") from exc


def resolve_page_token(page_id: str, token: str, graph_version: str = "v21.0") -> str:
    """Exchange a User/System-User token for the Page-scoped access token if available."""
    url = (
        f"https://graph.facebook.com/{graph_version}/{page_id}"
        f"?fields=access_token&access_token={urllib.parse.quote(token)}"
    )
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("access_token") or token
    except urllib.error.HTTPError:
        return token


def publish_facebook_reel(
    video_path: Path,
    description: str,
    page_id: str,
    token: str,
    graph_version: str = "v21.0",
    scheduled_unix: int | None = None,
) -> dict:
    page_token = resolve_page_token(page_id, token, graph_version)
    base = f"https://graph.facebook.com/{graph_version}/{page_id}/video_reels"

    # Step 1: Initialize upload session
    start_res = post_form(base, {"upload_phase": "start", "access_token": page_token})
    video_id = start_res["video_id"]
    upload_url = start_res["upload_url"]

    # Step 2: Upload MP4 bytes
    upload_video_binary(upload_url, page_token, video_path)

    # Step 3: Finish & publish (or schedule)
    finish_data: dict[str, str] = {
        "upload_phase": "finish",
        "video_id": video_id,
        "description": description,
        "access_token": page_token,
    }
    if scheduled_unix is not None:
        finish_data["video_state"] = "SCHEDULED"
        finish_data["scheduled_publish_time"] = str(scheduled_unix)
    else:
        finish_data["video_state"] = "PUBLISHED"

    return post_form(base, finish_data)


def check_connection(page_id: str, token: str, graph_version: str = "v21.0") -> dict:
    url = f"https://graph.facebook.com/{graph_version}/{page_id}?fields=id,name&access_token={urllib.parse.quote(token)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Meta API error {exc.code}: {body}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a Reel to your Facebook Page.")
    parser.add_argument("--video", help="Path to 9:16 MP4 file")
    parser.add_argument("--caption", help="Reel caption/description")
    parser.add_argument("--schedule", type=int, help="Optional Unix timestamp to schedule")
    parser.add_argument("--check", action="store_true", help="Verify Page ID and token without publishing")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    load_env(root / ".env")

    page_id = os.environ.get("META_PAGE_ID", "").strip()
    token = os.environ.get("META_PAGE_ACCESS_TOKEN", "").strip()
    version = os.environ.get("META_GRAPH_VERSION", "v21.0").strip()

    if not page_id or not token:
        raise SystemExit("Missing META_PAGE_ID or META_PAGE_ACCESS_TOKEN in .env")

    if args.check:
        print(json.dumps(check_connection(page_id, token, version), indent=2))
        return

    if not args.video or not args.caption:
        parser.error("Provide --video and --caption (or use --check).")

    result = publish_facebook_reel(
        video_path=Path(args.video),
        description=args.caption,
        page_id=page_id,
        token=token,
        graph_version=version,
        scheduled_unix=args.schedule,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
