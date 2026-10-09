"""Upload fixed Space files (from a decrypted bundle), wait for builds, report final state.

Each sub-folder of the bundle is named after a Space id and holds the files to upload.
A file named _delete.txt lists paths to remove from that Space.
"""
import json
import os
import sys
import time

from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi

SRC = sys.argv[1]
api = HfApi(token=os.environ["HF_TOKEN"])
targets = sorted(d for d in os.listdir(SRC) if os.path.isdir(os.path.join(SRC, d)))
for space in targets:
    repo, root = f"DatariusAI/{space}", os.path.join(SRC, space)
    ops = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, root)
            if rel == "_delete.txt":
                existing = set(api.list_repo_files(repo, repo_type="space"))
                ops += [CommitOperationDelete(p.strip()) for p in open(full) if p.strip() in existing]
            else:
                ops.append(CommitOperationAdd(path_in_repo=rel, path_or_fileobj=full))
    api.create_commit(repo, operations=ops, repo_type="space",
                      commit_message="Fix build/runtime errors and refresh the app")
    print("pushed", repo, len(ops), "changes", flush=True)

deadline, final = time.time() + 25 * 60, {}
while time.time() < deadline and len(final) < len(targets):
    time.sleep(30)
    for space in targets:
        if space in final:
            continue
        stage = api.get_space_runtime(f"DatariusAI/{space}").stage
        if stage in ("RUNNING", "BUILD_ERROR", "RUNTIME_ERROR", "CONFIG_ERROR", "NO_APP_FILE"):
            final[space] = stage
            print(space, stage, flush=True)
for space in targets:
    final.setdefault(space, api.get_space_runtime(f"DatariusAI/{space}").stage)
print(json.dumps(final, indent=1))
