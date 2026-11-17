"""Preserve the reviewed HVD nine blobs on MIC's parent tree; no checkout."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path("D:/project/cluster_project")
PIPE = ROOT / "pipeline"
REPO = ROOT / "Cluster"
HERE = Path(__file__).resolve().parent
TOKEN = "1138a3fc76ce46108e2bb511e1093826"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
BASE = "07ef534a6e44f22bd7b2d083550ebd7823d1d3d3"
OLD = "e38d92db60f43dde00ae0e537493dc3f3dfc82db"
CID = "hierarchy-native-variance-decomposition-composition"
REF = "refs/codex/cluster_project/hvd-compatible-07ef-1138a3fc"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def guard():
    owner = read(PIPE / "headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN
    assert owner["thread_id"] == os.environ.get("CODEX_THREAD_ID") == THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    for filename, key in [
        (".tick_context.json", "context_sha256"),
        (".tick_context_state.next.json", "pending_sha256"),
    ]:
        assert sha((PIPE / "headless" / filename).read_bytes()) == owner[key]
    return {k: owner[k] for k in [
        "token", "thread_id", "generated_at", "deadline_at",
        "context_sha256", "pending_sha256",
    ]}


def git(*args, env=None):
    result = subprocess.run(
        ["git", *args], cwd=REPO, env=env,
        capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")[-1000:]
    return result.stdout


def protected():
    index_name = git("rev-parse", "--git-path", "index").decode().strip()
    index = (REPO / index_name).resolve()
    changed = git("diff", "--name-only", "-z", "HEAD")
    untracked = git("ls-files", "--others", "--exclude-standard", "-z")
    names = sorted(set(x.decode("utf-8") for x in (changed + untracked).split(b"\0") if x))
    files = {}
    for name in names:
        path = (REPO / name).resolve()
        assert path.is_relative_to(REPO.resolve())
        files[name] = sha(path.read_bytes()) if path.is_file() else "ABSENT"
    return {
        "main_head": git("rev-parse", "HEAD").decode().strip(),
        "main_ref": git("symbolic-ref", "HEAD").decode().strip(),
        "index_sha256": sha(index.read_bytes()),
        "index_entries_sha256": sha(git("ls-files", "--stage", "-z")),
        "status_sha256": sha(git("status", "--porcelain=v1", "-z", "--untracked-files=all")),
        "user_files": files,
        "project_files": {
            name: sha((ROOT / name).read_bytes())
            for name in [
                "SERVERS.yaml", "pipeline/goal.json", "pipeline/queue.json",
                "pipeline/running.json", "pipeline/research_work.json",
                "pipeline/admissions/M229-MIC.json",
            ]
        },
    }


owner = guard()
out = HERE / "hvd_compatible_source_version.json"
assert not out.exists()
assert not (HERE / "hvd_compatible.index").exists()
before = protected()
assert before["main_head"] == BASE
candidate = next(c for c in read(PIPE / "research_work.json")["candidates"] if c["id"] == CID)
assert candidate["source_commit"] == OLD
expected = candidate["source_files_exact9"]
assert len(expected) == 9
old_parent = git("rev-parse", OLD + "^").decode().strip()
delta = git("diff-tree", "--no-commit-id", "--name-status", "-r", OLD).decode().splitlines()
assert sorted(delta) == sorted("A\t" + path for path in expected)
base_paths = set(git("ls-tree", "-r", "--name-only", BASE).decode().splitlines())
assert not (base_paths & set(expected))
assert not any((REPO / path).exists() for path in expected)

source = {}
compiled = []
for path, expected_sha in sorted(expected.items()):
    raw = git("show", OLD + ":" + path)
    assert sha(raw) == expected_sha
    mode, kind, oid = git("ls-tree", OLD, "--", path).decode().split("\t", 1)[0].split()
    assert kind == "blob" and mode == "100644"
    source[path] = {"mode": mode, "blob": oid, "sha256": expected_sha}
    if path.endswith(".py"):
        compile(raw, path, "exec")
        compiled.append(path)
assert len(compiled) == 8

environment = dict(os.environ, GIT_INDEX_FILE=str(HERE / "hvd_compatible.index"))
guard()
git("read-tree", BASE, env=environment)
for path, item in source.items():
    git("update-index", "--add", "--cacheinfo", f'{item["mode"]},{item["blob"]},{path}', env=environment)
tree = git("write-tree", env=environment).decode().strip()
guard()
commit = git(
    "commit-tree", tree, "-p", BASE, "-m",
    "Preserve reviewed HVD source on current MIC parent without changing its nine blobs",
    env=environment,
).decode().strip()
git("update-ref", REF, commit, "0" * 40)
assert git("rev-parse", commit + "^").decode().strip() == BASE
assert sorted(git("diff-tree", "--no-commit-id", "--name-status", "-r", commit).decode().splitlines()) == sorted(delta)
for path, item in source.items():
    assert sha(git("show", commit + ":" + path)) == item["sha256"]
    assert git("rev-parse", commit + ":" + path).decode().strip() == item["blob"]
after = protected()
assert before == after
guard()
result = {
    "recorded_at": datetime.now(timezone.utc).isoformat(),
    "owner": owner, "candidate_id": CID, "experiment_id": "M230-HVD",
    "source_commit": commit, "code_commit": commit,
    "source_parent_commit": BASE, "parent_commit": BASE, "pinned_ref": REF,
    "prior_source_commit": OLD, "prior_source_parent_commit": old_parent,
    "source_files_exact9": expected, "git_blobs_exact9": source,
    "diff_exact9A": delta, "all_prior_tree_entries_unchanged": True,
    "same_source_bytes_as_independently_reviewed": True,
    "python_syntax_files_compiled_without_import": compiled,
    "protected_before": before, "protected_after": after,
    "main_HEAD_index_dirty_files_and_lifecycle_unchanged": True,
    "original_NULL_packet_preserved": True,
    "native": "NOT_RUN", "resources": "NOT_RUN",
    "scientific_admission": False, "promoted_or_deployed": False,
    "scope": "Same nine reviewed HVD source blobs preserved on current07ef; Git ancestry compatibility only, no model revision, forward/autograd/GPU/efficacy or novelty claim. Frozen old binding and packets remain unchanged; future execution needs separate reviewed current-source/runtime binding.",
}
with out.open("x", encoding="utf-8") as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({
    "source_commit": commit, "parent_commit": BASE,
    "same_nine_blobs": True, "main_and_user_files_unchanged": True,
    "evidence": {"path": out.relative_to(ROOT).as_posix(), "sha256": sha(out.read_bytes())},
}))
