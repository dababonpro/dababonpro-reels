"""Pre-publish verifier for 9:16 Reels/Shorts MP4 files."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True)


def verify_mp4(mp4_path: Path, min_dur: float = 8.0, max_dur: float = 90.0) -> dict:
    if not mp4_path.exists():
        raise FileNotFoundError(f"Missing video: {mp4_path}")

    probe = run_cmd([
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(mp4_path),
    ])
    if probe.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {probe.stderr}")

    info = json.loads(probe.stdout)
    streams = info.get("streams", [])
    v_streams = [s for s in streams if s.get("codec_type") == "video"]
    a_streams = [s for s in streams if s.get("codec_type") == "audio"]

    errors: list[str] = []
    if not v_streams:
        errors.append("No video stream found")
    else:
        vs = v_streams[0]
        w, h = int(vs.get("width", 0)), int(vs.get("height", 0))
        if (w, h) != (1080, 1920):
            errors.append(f"Expected 1080x1920, got {w}x{h}")
        if vs.get("codec_name") != "h264":
            errors.append(f"Expected h264 codec, got {vs.get('codec_name')}")
        if vs.get("pix_fmt") != "yuv420p":
            errors.append(f"Expected yuv420p pixel format, got {vs.get('pix_fmt')}")

    dur = float(info.get("format", {}).get("duration", 0))
    if not (min_dur <= dur <= max_dur):
        errors.append(f"Duration {dur:.1f}s outside [{min_dur}, {max_dur}]s")

    mean_vol = None
    if not a_streams:
        errors.append("No audio stream found (silent video)")
    else:
        vol = run_cmd([
            "ffmpeg", "-i", str(mp4_path), "-af", "volumedetect", "-f", "null", "-",
        ])
        m = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", vol.stderr)
        if m:
            mean_vol = float(m.group(1))
            if mean_vol < -60.0:
                errors.append(f"Audio stream is effectively silent ({mean_vol} dB)")

    return {
        "file": str(mp4_path),
        "ok": len(errors) == 0,
        "duration": round(dur, 2),
        "mean_volume_db": mean_vol,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify 9:16 Reel MP4s before publishing.")
    parser.add_argument("videos", nargs="+", help="MP4 file paths or globs")
    args = parser.parse_args()

    paths: list[Path] = []
    for pat in args.videos:
        p = Path(pat)
        if p.exists():
            paths.append(p)
        else:
            paths.extend(sorted(Path(".").glob(pat)))

    if not paths:
        raise SystemExit("No MP4 files matched.")

    all_ok = True
    results = []
    for path in paths:
        res = verify_mp4(path)
        results.append(res)
        if not res["ok"]:
            all_ok = False

    print(json.dumps(results, indent=2))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
