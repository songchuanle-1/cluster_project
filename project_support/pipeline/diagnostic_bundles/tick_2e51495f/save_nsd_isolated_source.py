"""Save only the reviewed nine NSD files using an isolated Git index."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
SOURCE = HERE / "reserve_candidate/source"
TOKEN = "2e51495f07244023946fc53eec6e6d98"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
PARENT = "d20eb221eff6584b67d4e9b5673559d0e1cb735b"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def guard():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"] == THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    for name, key in ((".tick_context.json", "context_sha256"),
                      (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[key]
    return {k: owner[k] for k in (
        "token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256",
    )}


def git(*args, env=None, raw=None):
    return subprocess.check_output(
        ["git", "--no-optional-locks", "-C", str(ROOT / "Cluster"), *args],
        input=raw, env=env or dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
    )


owner = guard()
assert not (HERE / "nsd_isolated_source_version.json").exists()
review = read(HERE / "reserve_candidate_independent_review.json")
assert review.get("passed") is True, "Exact independent review must pass before saving this source"
proposal = read(HERE / "reserve_candidate/candidate_proposal_final.json")
paths = proposal["source_files_exact9"]
assert len(paths) == 9
assert all(sha(SOURCE / path) == digest for path, digest in paths.items())
assert git("rev-parse", "HEAD").decode().strip() == PARENT
index = Path(git("rev-parse", "--git-path", "index").decode().strip())
if not index.is_absolute():
    index = ROOT / "Cluster" / index
before = {
    "HEAD": git("rev-parse", "HEAD").decode().strip(), "index": sha(index),
    "status_hex": git("status", "--porcelain=v1", "--untracked-files=all", "-z").hex(),
}
temporary_index = HERE / "nsd_isolated_source.index"
assert not temporary_index.exists()
environment = dict(os.environ, GIT_INDEX_FILE=str(temporary_index), GIT_OPTIONAL_LOCKS="0")
git("read-tree", PARENT, env=environment)
blobs = {}
for path in sorted(paths):
    guard()
    blob = git("hash-object", "-w", "--stdin", env=environment,
               raw=(SOURCE / path).read_bytes()).decode().strip()
    blobs[path] = blob
    git("update-index", "--add", "--cacheinfo", "100644," + blob + "," + path, env=environment)
tree = git("write-tree", env=environment).decode().strip()
guard()
commit = git("commit-tree", tree, "-p", PARENT, "-m",
             "Prepare native spatial Dirichlet hierarchy source; no deployment or admission",
             env=environment).decode().strip()
assert git("rev-parse", commit + "^").decode().strip() == PARENT
changed = sorted(path.decode() for path in git(
    "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", commit).split(b"\0") if path)
assert changed == sorted(paths)
for path, digest in paths.items():
    assert hashlib.sha256(git("show", commit + ":" + path)).hexdigest() == digest
after = {
    "HEAD": git("rev-parse", "HEAD").decode().strip(), "index": sha(index),
    "status_hex": git("status", "--porcelain=v1", "--untracked-files=all", "-z").hex(),
}
assert before == after
record = {
    "recorded_at": datetime.now(timezone.utc).isoformat(), "owner_provenance_only": owner,
    "candidate_id": proposal["id"], "experiment_id": proposal["experiment_id"],
    "source_commit": commit, "parent_commit": PARENT, "tree": tree,
    "source_files_exact9": paths, "blobs": blobs, "changed_paths": changed,
    "main_head_index_and_user_status_preserved": True,
    "protected_before": before, "protected_after": after,
    "independent_review": {"path": (HERE / "reserve_candidate_independent_review.json").relative_to(ROOT).as_posix(),
                           "sha256": sha(HERE / "reserve_candidate_independent_review.json")},
    "native": "NOT_RUN", "resources": "NOT_RUN", "Torch_autograd": "NOT_RUN",
    "source_promoted": False, "runtime_deployed": False,
}
with (HERE / "nsd_isolated_source_version.json").open("x", encoding="utf8") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"source_commit": commit, "parent": PARENT, "exact_files": 9,
                  "main_index_user_state_preserved": True, "native": "NOT_RUN"}))
