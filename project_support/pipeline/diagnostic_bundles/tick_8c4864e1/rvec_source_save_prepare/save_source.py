"""Reviewed, single-use retained source save. Default invocation performs no writes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
CODE = ROOT / "Cluster"
HERE = Path(__file__).resolve().parent
GIT = "C:/Program Files (x86)/Git/cmd/git.exe"
BASELINE_SHA = "26f189e3901efc28d1cbb215be0694a7822422a81003bbc1ccca1794b1a25555"
OWNER_KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def new_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def confined(root, relative):
    p = PurePosixPath(relative)
    require(not p.is_absolute() and ".." not in p.parts and "\\" not in relative, "Unsafe relative path")
    result = root.joinpath(*p.parts)
    require(result.resolve().is_relative_to(root.resolve()), "Path escapes intended root")
    for parent in [result, *result.parents]:
        if parent == root.parent:
            break
        require(not parent.is_symlink(), "Symlink path refused")
    return result


def git(*args, index=None, data=None):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    if index is not None:
        env["GIT_INDEX_FILE"] = str(index)
    process = subprocess.run([
        GIT, "--no-optional-locks", "-c", "core.fsmonitor=false",
        "-c", "core.hooksPath=" + str(HERE / "hooks_disabled"),
        "-c", "commit.gpgsign=false", "-C", str(CODE), *args,
    ], env=env, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
    require(process.returncode == 0, "Git failed: " + " ".join(args[:2]) + ": " + process.stderr.decode("utf-8", errors="replace")[:1500])
    return process.stdout


def owner_check(baseline):
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    binding = {k: owner[k] for k in OWNER_KEYS}
    require(binding == baseline["owner"], "Owner binding changed")
    require(os.environ.get("CODEX_THREAD_ID") == binding["thread_id"], "Wrong executor thread")
    require(datetime.now(timezone.utc) < datetime.fromisoformat(binding["deadline_at"]), "Owner expired")
    require(sha(ROOT / "pipeline/headless/.tick_context.json") == binding["context_sha256"], "Context changed")
    require(sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == binding["pending_sha256"], "Pending state changed")


def unchanged(baseline, source_present):
    owner_check(baseline)
    require(git("rev-parse", "HEAD").decode().strip() == baseline["main_HEAD"], "Main HEAD changed")
    index_path = Path(baseline["real_index_path"])
    require(index_path.resolve() == (CODE / ".git/index").resolve(), "Unexpected actual index path")
    require(sha(index_path) == baseline["real_index_sha256"], "Actual index bytes changed")
    require(hashlib.sha256(git("ls-files", "--stage", "-z")).hexdigest() == baseline["real_index_entries_sha256"], "Actual index entries changed")
    require(not git("diff", "--cached", "--name-only", "-z"), "Actual staged changes appeared")
    for path, expected in baseline["dirty_files_exact28"].items():
        require(sha(confined(CODE, path)) == expected, "Existing user file changed: " + path)
    expected = bytes.fromhex(baseline["status_hex"]).split(b"\0")
    if source_present:
        expected += [b"?? " + p.encode("utf-8") for p in baseline["source_files_exact9"]]
    actual = git("status", "--porcelain=v1", "-z", "--untracked-files=all").split(b"\0")
    require(sorted(x for x in actual if x) == sorted(x for x in expected if x), "Unexpected working-tree status")
    for path, expected_sha in baseline["source_files_exact9"].items():
        destination = confined(CODE, path)
        require(sha(destination) == expected_sha if source_present else not destination.exists(), "Destination state differs: " + path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--review", type=Path)
    args = parser.parse_args()
    if not args.execute:
        print("NOOP: --execute and an independent --review are required.")
        return
    require(sys.dont_write_bytecode, "Run Python with -B")
    require(args.review is not None, "Independent review is required")
    require(sha(HERE / "baseline.json") == BASELINE_SHA, "Baseline changed")
    baseline = read(HERE / "baseline.json")
    frozen = read(HERE / "FROZEN.json")
    require(frozen["owner"] == baseline["owner"], "Packet owner differs")
    for relative, expected_sha in frozen["files"].items():
        require(sha(confined(HERE, relative)) == expected_sha, "Frozen helper packet changed")
    review_path = args.review.resolve()
    require(review_path.is_relative_to((ROOT / "pipeline/diagnostic_bundles/tick_8c4864e1").resolve()), "Review outside current bundle")
    review = read(review_path)
    require(review.get("passed") is True and review.get("material_concerns") == [], "Peer review did not pass")
    require(review.get("owner") == baseline["owner"], "Review owner differs")
    require(review.get("reviewer_thread_id") not in [None, "", baseline["owner"]["thread_id"]], "Review is not independent")
    for key, actual in [
        ("helper_sha256", sha(Path(__file__))),
        ("baseline_sha256", BASELINE_SHA),
        ("FROZEN_sha256", sha(HERE / "FROZEN.json")),
    ]:
        require(review.get(key) == actual, "Review hash differs: " + key)
    source_frozen_path = ROOT / baseline["source_FROZEN"]["path"]
    for reference in [baseline["source_FROZEN"], baseline["source_version"], *baseline["genuine_prior_proofs"].values()]:
        require(sha(confined(ROOT, reference["path"])) == reference["sha256"], "Prior proof changed")
    source_frozen = read(source_frozen_path)
    require(source_frozen["source_files_exact9"] == baseline["source_files_exact9"], "Frozen source map differs")
    require(len(baseline["source_files_exact9"]) == 9 and len(baseline["dirty_files_exact28"]) == 28, "Scope differs")
    source_root = source_frozen_path.parent / "source"
    for path, expected in baseline["source_files_exact9"].items():
        require(sha(confined(source_root, path)) == expected, "Frozen source differs")
    unchanged(baseline, False)
    ref = baseline["retained_ref"]
    require(ref == "refs/pipeline/candidates/M234-RVE-r0", "Unexpected retained ref")
    require(not git("for-each-ref", "--format=%(refname)", ref), "Candidate ref already exists")
    intent = HERE / "source_save_intent.json"
    index = HERE / "temporary.index"
    proof_path = HERE / "source_version.json"
    require(all(not p.exists() for p in [intent, index, Path(str(index) + ".lock"), proof_path]), "Single-use state already exists; no automatic replay")
    new_json(intent, {
        "recorded_at": datetime.now(timezone.utc).isoformat(), "owner": baseline["owner"],
        "review_path": str(review_path), "review_sha256": sha(review_path),
        "helper_sha256": sha(Path(__file__)), "baseline_sha256": BASELINE_SHA,
        "retained_ref": ref, "main_HEAD": baseline["main_HEAD"],
        "no_replay": True, "only_nine_new_paths": list(baseline["source_files_exact9"]),
    })
    owner_check(baseline)
    for path, expected in baseline["source_files_exact9"].items():
        data = confined(source_root, path).read_bytes()
        require(hashlib.sha256(data).hexdigest() == expected, "Source changed before copy")
        destination = confined(CODE, path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    unchanged(baseline, True)
    git("read-tree", baseline["main_HEAD"], index=index)
    blobs = {}
    for path, expected in baseline["source_files_exact9"].items():
        data = confined(CODE, path).read_bytes()
        require(hashlib.sha256(data).hexdigest() == expected, "New source changed before staging")
        blob = git("hash-object", "-w", "--no-filters", "--stdin", data=data).decode().strip()
        git("update-index", "--add", "--cacheinfo", "100644", blob, path, index=index)
        blobs[path] = {"git_blob": blob, "sha256": expected}
    tree = git("write-tree", index=index).decode().strip()
    expected_diff = sorted(b"A\0" + p.encode() + b"\0" for p in baseline["source_files_exact9"])
    raw_diff = git("diff-tree", "--no-commit-id", "--no-renames", "--name-status", "-r", "-z", baseline["main_HEAD"], tree)
    tokens = raw_diff.split(b"\0")
    require(tokens[-1] == b"" and len(tokens) == 19, "Candidate diff has unexpected size")
    actual_diff = sorted(tokens[i] + b"\0" + tokens[i + 1] + b"\0" for i in range(0, len(tokens) - 1, 2))
    require(actual_diff == expected_diff, "Candidate tree is not exactly nine additions")
    for path, detail in blobs.items():
        require(hashlib.sha256(git("cat-file", "blob", tree + ":" + path)).hexdigest() == detail["sha256"], "Tree blob differs")
    unchanged(baseline, True)
    commit = git("commit-tree", tree, "-p", baseline["main_HEAD"], "-F", str(HERE / "commit_message.txt")).decode().strip()
    require(git("rev-list", "--parents", "-n", "1", commit).decode().strip() == commit + " " + baseline["main_HEAD"], "Commit parent differs")
    unchanged(baseline, True)
    owner_check(baseline)
    git("update-ref", ref, commit, "0" * 40)
    unchanged(baseline, True)
    require(git("rev-parse", ref).decode().strip() == commit, "Retained ref differs")
    proof = {
        "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "owner": baseline["owner"], "candidate_id": "fine-leaf-receiver-conditioned-vector-exchange",
        "experiment_id": "M234-RVE", "status": "RETAINED_SOURCE_COMMIT_ONLY_NATIVE_RESOURCES_ADMISSION_PENDING",
        "source_parent_commit": baseline["main_HEAD"], "source_commit": commit,
        "source_tree": tree, "retained_ref": ref, "source_files_exact9": baseline["source_files_exact9"],
        "source_blobs_exact9": blobs, "source_FROZEN": baseline["source_FROZEN"],
        "genuine_prior_proofs": baseline["genuine_prior_proofs"],
        "independent_review": {"path": str(review_path), "sha256": sha(review_path)},
        "helper_sha256": sha(Path(__file__)), "baseline_sha256": BASELINE_SHA,
        "main_HEAD_unchanged": True, "actual_index_bytes_unchanged": True,
        "actual_index_entries_unchanged": True, "all28_user_files_byte_exact": True,
        "main_HEAD": baseline["main_HEAD"], "actual_index_sha256": baseline["real_index_sha256"],
        "actual_index_entries_sha256": baseline["real_index_entries_sha256"],
        "main_HEAD_advanced": False, "pushed": False, "remote_mutation": False,
        "queue_or_shared_state_mutation": False, "native_validation": "PENDING",
        "resource_validation": "PENDING", "scientific_admission": "NOT_GRANTED",
    }
    new_json(proof_path, proof)
    print(json.dumps({"source_commit": commit, "retained_ref": ref, "source_version_path": str(proof_path), "sha256": sha(proof_path)}))


if __name__ == "__main__":
    main()
