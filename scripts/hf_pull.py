"""Download the source files and recent logs of every Space in apps.json.

Used by the hf-pull workflow. Only small text files are fetched (code, configs,
requirements); model weights and data files are skipped.
"""
import json
import os
import sys

import requests
from huggingface_hub import HfApi, snapshot_download

OUT = sys.argv[1] if len(sys.argv) > 1 else "spaces"
TOKEN = os.environ["HF_TOKEN"]
APPS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps.json"), encoding="utf-8"))
PATTERNS = ["*.py", "*.txt", "*.md", "*.json", "*.yaml", "*.yml", "*.toml", "*.cfg", "Dockerfile", "*.sh",
            "requirements*", "packages.txt", "runtime.txt", ".huggingface.yaml", "*.csv", "*.db", "*.faiss"]


def logs(space, kind):
    url = f"https://huggingface.co/api/spaces/{space}/logs/{kind}"
    text = []
    try:
        with requests.get(url, headers={"Authorization": f"Bearer {TOKEN}"}, stream=True, timeout=(10, 8)) as r:
            for line in r.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    try:
                        text.append(json.loads(line[5:]).get("data", ""))
                    except ValueError:
                        text.append(line[5:])
    except Exception as exc:  # the stream stays open; a read timeout ends it
        text.append(f"\n[log stream ended: {type(exc).__name__}]")
    return "".join(text)[-20000:]


api = HfApi(token=TOKEN)
for space in APPS["huggingface"]:
    repo = f"DatariusAI/{space['id']}"
    dest = os.path.join(OUT, space["id"])
    try:
        snapshot_download(repo, repo_type="space", local_dir=dest, allow_patterns=PATTERNS, token=TOKEN)
        info = api.space_info(repo)
        files = [s.rfilename for s in info.siblings]
        runtime = api.get_space_runtime(repo)
        meta = {"stage": runtime.stage, "sdk": info.sdk, "files": files,
                "secrets_or_vars_needed": "see app code"}
        json.dump(meta, open(os.path.join(dest, "_meta.json"), "w"), indent=1)
        for kind in ("build", "run"):
            open(os.path.join(dest, f"_log_{kind}.txt"), "w").write(logs(repo, kind))
        print("ok", repo, runtime.stage)
    except Exception as exc:
        print("fail", repo, exc)
