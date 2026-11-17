"""Save the unchanged MIC nine-file bundle on the current parent, without checkout."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

ROOT = Path("D:/project/cluster_project")
REPO = ROOT / "Cluster"
OUT = Path(__file__).resolve().parent / "mic_version_prepare"
GIT = "C:/Program Files (x86)/Git/cmd/git.exe"
TOKEN = "265517f1c8984940a6925367924f062f"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
BASE = "6bc36adfe42764aac2209e6600fb3a783e2fa374"
ORIGINAL = "041b63579888f2143cb9f3a5216ec4cff4ee8046"
CID = "hierarchy-ancestry-mobius-interaction-composition"
REF = "refs/codex/cluster_project/M229-MIC/265517f1"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args: str, env=None, data=None) -> bytes:
    return subprocess.run(
        [GIT, "-C", str(REPO), *args],
        input=data, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=True,
    ).stdout


def guard():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD
    assert os.environ.get("CODEX_THREAD_ID") == THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha((ROOT / "pipeline/headless/.tick_context.json").read_bytes()) == owner["context_sha256"]
    return {k: owner[k] for k in (
        "token", "thread_id", "generated_at", "deadline_at",
        "context_sha256", "pending_sha256",
    )}


def protected():
    index = Path(git("rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = REPO / index
    status = git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    records = status.split(b"\0")
    dirty = {}
    i = 0
    while i < len(records) and records[i]:
        item = records[i]
        name = item[3:].decode("utf-8")
        path = REPO / name
        assert path.resolve().is_relative_to(REPO.resolve())
        if path.is_file():
            dirty[name] = sha(path.read_bytes())
        if b"R" in item[:2] or b"C" in item[:2]:
            i += 1
        i += 1
    lifecycle = {}
    for relative in (
        "SERVERS.yaml", "pipeline/goal.json", "pipeline/closure_policy.json",
        "pipeline/queue.json", "pipeline/research_work.json",
        "pipeline/admissions/M228-NEC.json",
        "pipeline/admissions/M227-LFT.json",
    ):
        p = ROOT / relative
        if p.is_file():
            lifecycle[relative] = sha(p.read_bytes())
    return {
        "head": git("rev-parse", "HEAD").decode().strip(),
        "index_sha256": sha(index.read_bytes()),
        "porcelain_sha256": sha(status),
        "dirty_file_sha256": dirty,
        "lifecycle_sha256": lifecycle,
    }


def main():
    owner = guard()
    assert not OUT.exists(), "Retain any prior intent; reconcile instead of replaying."
    before = protected()
    assert before["head"] == BASE
    work = read(ROOT / "pipeline/research_work.json")
    candidates = work["candidates"]
    candidate = (
        next(c for c in candidates if c["id"] == CID)
        if isinstance(candidates, list) else candidates[CID]
    )
    assert candidate["source_commit"] == ORIGINAL
    expected = candidate["source_files_exact9"]
    assert len(expected) == 9
    assert len([p for p in expected if p.endswith(".py")]) == 8
    versions = {}
    for path, digest in expected.items():
        content = git("show", f"{ORIGINAL}:{path}")
        assert sha(content) == digest
        if path.endswith(".py"):
            compile(content, path, "exec")
        absent = subprocess.run(
            [GIT, "-C", str(REPO), "cat-file", "-e", f"{BASE}:{path}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        assert absent.returncode != 0
        blob = git("rev-parse", f"{ORIGINAL}:{path}").decode().strip()
        versions[path] = blob
    OUT.mkdir(parents=True)
    intent = {
        "owner": owner, "base": BASE, "original_source": ORIGINAL,
        "same_exact9_sha256": expected, "native": "NOT_RUN",
        "no_main_checkout_index_or_remote_mutation": True,
    }
    (OUT / "version_intent.json").write_text(
        json.dumps(intent, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    isolated_env = dict(os.environ)
    isolated_env["GIT_INDEX_FILE"] = str(OUT / "isolated.index")
    git("read-tree", BASE, env=isolated_env)
    for path, blob in versions.items():
        git("update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", env=isolated_env)
    tree = git("write-tree", env=isolated_env).decode().strip()
    guard()
    commit = git(
        "commit-tree", tree, "-p", BASE, "-m",
        "Save unchanged M229 MIC source on NEC-compatible parent",
        env=isolated_env,
    ).decode().strip()
    diff = git("diff-tree", "--no-commit-id", "--name-status", "-r", BASE, commit).decode().splitlines()
    assert sorted(diff) == sorted("A\t" + p for p in expected)
    for path, digest in expected.items():
        assert sha(git("show", f"{commit}:{path}")) == digest
    prior_tree = git("ls-tree", "-r", "-z", BASE).split(b"\0")
    new_tree = set(git("ls-tree", "-r", "-z", commit).split(b"\0"))
    assert all(entry in new_tree for entry in prior_tree if entry)
    git("update-ref", REF, commit, "0" * 40)
    after = protected()
    assert before == after, "Unexpected shared change; preserve proof and reconcile."
    proof = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "owner": owner, "candidate_id": CID, "experiment_id": "M229-MIC",
        "source_commit": commit, "code_commit": commit,
        "parent_commit": BASE, "source_parent_commit": BASE,
        "prior_source_commit": ORIGINAL,
        "prior_parent_commit": candidate["source_parent_commit"],
        "frozen_source_files": expected, "pinned_ref": REF,
        "diff_exact9A": True, "all_prior_tree_entries_unchanged": True,
        "new_model_revision": False, "same9_bytes_as_reviewed_original": True,
        "protected_before": before, "protected_after": after,
        "main_HEAD_index_dirty_files_and_lifecycle_unchanged": True,
        "native_or_resource_checks": "NOT_RUN", "scientific_admission": False,
        "scope": "Local compatible source save only; not promoted, deployed, admitted or executed.",
    }
    output = OUT / "isolated_source_version.json"
    output.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_commit": commit, "parent": BASE, "same_exact9": True,
        "main_unchanged": True, "proof": str(output), "sha256": sha(output.read_bytes()),
    }))


if __name__ == "__main__":
    main()
