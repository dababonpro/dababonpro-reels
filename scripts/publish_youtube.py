"""Upload a 9:16 video as a YouTube Short via YouTube Data API v3 (zero external deps)."""

from __future__ import annotations

import argparse
import http.server
import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def load_client_secrets(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("installed") or data.get("web") or data


def exchange_code(client: dict, code: str, redirect_uri: str) -> dict:
    payload = urllib.parse.urlencode({
        "code": code,
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode("utf-8")
    req = urllib.request.Request(client["token_uri"], data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        tok = json.loads(resp.read().decode("utf-8"))
    tok["expires_at"] = time.time() + int(tok.get("expires_in", 3600)) - 60
    return tok


def refresh_token(client: dict, refresh_tok: str) -> dict:
    payload = urllib.parse.urlencode({
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "refresh_token": refresh_tok,
        "grant_type": "refresh_token",
    }).encode("utf-8")
    req = urllib.request.Request(client["token_uri"], data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        tok = json.loads(resp.read().decode("utf-8"))
    tok["refresh_token"] = tok.get("refresh_token") or refresh_tok
    tok["expires_at"] = time.time() + int(tok.get("expires_in", 3600)) - 60
    return tok


def run_browser_oauth(client: dict) -> dict:
    code_holder: dict[str, str] = {}
    done_event = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "code" in qs:
                code_holder["code"] = qs["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h2>YouTube OAuth complete. You can close this tab.</h2>")
                done_event.set()
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing code")
                done_event.set()

        def log_message(self, format: str, *args: object) -> None:
            return

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    redirect_uri = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    auth_params = urllib.parse.urlencode({
        "client_id": client["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    })
    auth_url = f"{client['auth_uri']}?{auth_params}"
    print(f"Opening browser for YouTube OAuth:\n{auth_url}")
    webbrowser.open(auth_url)
    done_event.wait(timeout=180)
    server.shutdown()
    server.server_close()

    if "code" not in code_holder:
        raise RuntimeError("OAuth authorization timed out or failed.")
    return exchange_code(client, code_holder["code"], redirect_uri)


def get_access_token(secrets_path: Path, token_path: Path) -> str:
    client = load_client_secrets(secrets_path)
    if token_path.exists():
        tok = json.loads(token_path.read_text(encoding="utf-8"))
        if tok.get("expires_at", 0) > time.time():
            return tok["access_token"]
        if tok.get("refresh_token"):
            tok = refresh_token(client, tok["refresh_token"])
            token_path.write_text(json.dumps(tok, indent=2), encoding="utf-8")
            return tok["access_token"]

    tok = run_browser_oauth(client)
    token_path.write_text(json.dumps(tok, indent=2), encoding="utf-8")
    return tok["access_token"]


def check_channel(access_token: str) -> dict:
    url = "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def upload_short(
    access_token: str,
    video_path: Path,
    title: str,
    description: str,
    privacy: str = "private",
    publish_at: str | None = None,
) -> dict:
    video_bytes = video_path.read_bytes()
    metadata: dict = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "categoryId": "28",  # Science & Technology
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }
    if publish_at:
        metadata["status"]["privacyStatus"] = "private"
        metadata["status"]["publishAt"] = publish_at

    init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
    init_req = urllib.request.Request(
        init_url,
        data=json.dumps(metadata).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Length": str(len(video_bytes)),
            "X-Upload-Content-Type": "video/mp4",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(init_req, timeout=60) as resp:
            upload_url = resp.headers["Location"]
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"YouTube init error {exc.code}: {exc.read().decode('utf-8', errors='replace')}") from exc

    put_req = urllib.request.Request(
        upload_url,
        data=video_bytes,
        headers={
            "Content-Length": str(len(video_bytes)),
            "Content-Type": "video/mp4",
        },
        method="PUT",
    )
    try:
        with urllib.request.urlopen(put_req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"YouTube upload error {exc.code}: {exc.read().decode('utf-8', errors='replace')}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload a Short to YouTube.")
    parser.add_argument("--video", help="Path to 9:16 MP4")
    parser.add_argument("--title", help="Video title (include #Shorts)")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    parser.add_argument("--publish-at", help="Optional ISO-8601 UTC timestamp (e.g. 2026-11-23T01:00:00Z)")
    parser.add_argument("--auth-only", action="store_true", help="Authenticate and print channel info")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    secrets_path = root / "yt_client_secrets.json"
    token_path = root / "youtube_token.json"
    if not secrets_path.exists():
        raise SystemExit(f"Missing {secrets_path}")

    token = get_access_token(secrets_path, token_path)
    if args.auth_only:
        print(json.dumps(check_channel(token), indent=2))
        return

    if not args.video or not args.title:
        parser.error("Provide --video and --title (or use --auth-only).")

    res = upload_short(
        access_token=token,
        video_path=Path(args.video),
        title=args.title,
        description=args.description,
        privacy=args.privacy,
        publish_at=args.publish_at,
    )
    print(json.dumps({"id": res.get("id"), "status": res.get("status")}, indent=2))


if __name__ == "__main__":
    main()
