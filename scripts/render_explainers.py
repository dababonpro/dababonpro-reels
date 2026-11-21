"""Render and verify all 6 AI Engineering explainer Reels."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from verify_reel import verify_mp4

SERIES = [
    ("content/explainers/11_llms.json", "out/11_explainer_llms.mp4"),
    ("content/explainers/12_rag.json", "out/12_explainer_rag.mp4"),
    ("content/explainers/13_mcp.json", "out/13_explainer_mcp.mp4"),
    ("content/explainers/14_context_engineering.json", "out/14_explainer_context_engineering.mp4"),
    ("content/explainers/15_harness_engineering.json", "out/15_explainer_harness_engineering.mp4"),
    ("content/explainers/16_graph_engineering.json", "out/16_explainer_graph_engineering.mp4"),
]


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    results = []
    for sb_rel, out_rel in SERIES:
        sb = root / sb_rel
        out = root / out_rel
        subprocess.run(
            [sys.executable, str(root / "scripts" / "generate_story_reel.py"), "--storyboard", str(sb), "--out", str(out)],
            check=True,
        )
        res = verify_mp4(out)
        results.append(res)
        print(f"Verified {out_rel}: ok={res['ok']} dur={res['duration']}s vol={res['mean_volume_db']}dB")
        if not res["ok"]:
            raise SystemExit(f"Verification failed for {out_rel}: {res['errors']}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
