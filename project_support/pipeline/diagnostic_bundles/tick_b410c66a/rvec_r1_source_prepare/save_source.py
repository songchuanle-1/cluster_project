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
BASELINE_SHA = "94cc5151fcb180c4f1e4c017a28ce9710ca431f8f707737ae2d716e6c00cc702"
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


def unchanged(baseline):
    owner_check(baseline)
    require(git("rev-parse", "HEAD").decode().strip() == baseline["main_HEAD"], "Main HEAD changed")
    require(git("rev-parse", baseline["prior_r0_ref"]).decode().strip() == baseline["source_parent_commit"], "r0 ref changed")
    index_path = Path(baseline["real_index_path"])
    require(index_path.resolve() == (CODE / ".git/index").resolve(), "Unexpected actual index path")
    require(sha(index_path) == baseline["real_index_sha256"], "Actual index bytes changed")
    require(hashlib.sha256(git("ls-files", "--stage", "-z")).hexdigest() == baseline["real_index_entries_sha256"], "Actual index entries changed")
    require(not git("diff", "--cached", "--name-only", "-z"), "Actual staged changes appeared")
    require(git("status", "--porcelain=v1", "-z", "--untracked-files=all").hex() == baseline["status_hex"], "Working-tree status changed")
    for path, expected in {**baseline["dirty_files_exact28"], **baseline["working_tree_r0_files_exact9"]}.items():
        require(sha(confined(CODE, path)) == expected, "Existing working-tree file changed: " + path)


def exact_diff(parent, tree, expected):
    raw = git("diff-tree", "--no-commit-id", "--no-renames", "--name-status", "-r", "-z", parent, tree)
    tokens = raw.split(b"\0")
    require(tokens[-1] == b"" and len(tokens) == 2 * len(expected) + 1, "Diff size differs")
    observed = sorted((tokens[i].decode("utf-8"), tokens[i + 1].decode("utf-8")) for i in range(0, len(tokens) - 1, 2))
    require(observed == sorted(expected), "Diff scope differs")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--review", type=Path)
    args = parser.parse_args()
    if not args.execute:
        print("NOOP: --execute and an independent --review are required.")
        return
    require(sys.dont_write_bytecode, "Run Python with -B")
    require(args.review is not None, "Independent review required")
    require(sha(HERE / "baseline.json") == BASELINE_SHA, "Baseline changed")
    baseline = read(HERE / "baseline.json")
    frozen = read(HERE / "FROZEN.json")
    require(frozen["owner"] == baseline["owner"], "Packet owner differs")
    for relative, expected in frozen["files"].items():
        require(sha(confined(HERE, relative)) == expected, "Frozen packet changed: " + relative)
    review_path = args.review.resolve()
    require(review_path.is_relative_to(HERE.parent.resolve()), "Review outside current bundle")
    review = read(review_path)
    require(review.get("passed") is True and review.get("material_concerns") == [], "Independent review did not pass")
    require(review.get("owner") == baseline["owner"], "Review owner differs")
    require(review.get("reviewer_thread_id") not in [None, "", baseline["owner"]["thread_id"]], "Review not independent")
    for key, actual in [("helper_sha256", sha(Path(__file__))), ("baseline_sha256", BASELINE_SHA), ("FROZEN_sha256", sha(HERE / "FROZEN.json"))]:
        require(review.get(key) == actual, "Review hash differs: " + key)
    for reference in [baseline["preregistration"], baseline["historical_source_version"], baseline["source_FROZEN"], *baseline["genuine_prior_proofs"].values()]:
        require(sha(confined(ROOT, reference["path"])) == reference["sha256"], "Bound prior evidence changed")
    prereg = read(ROOT / baseline["preregistration"]["path"])
    require(prereg["owner"] == baseline["owner"] and prereg["source_parent"] == baseline["source_parent_commit"], "Preregistration binding differs")
    require(prereg["revision"]["revision"] == 1 and prereg["revision"]["result"] == "pending", "Revision not pending1")
    work = read(ROOT / "pipeline/research_work.json")
    candidate = next(item for item in work["candidates"] if item.get("id") == "fine-leaf-receiver-conditioned-vector-exchange")
    require(candidate.get("revision_history") == [prereg["revision"]], "Registered revision changed")
    for reference in prereg["revision"]["failure_evidence"]:
        require(sha(confined(ROOT, reference["path"])) == reference["sha256"], "Actual failure evidence changed")
    files = baseline["source_files_exact9"]
    old_files = baseline["working_tree_r0_files_exact9"]
    changed = baseline["changed_path_exact1"]
    parent = baseline["source_parent_commit"]
    require(len(files) == len(old_files) == 9 and set(files) == set(old_files), "Source scope differs")
    require([p for p in files if files[p] != old_files[p]] == [changed] and changed.endswith("/hier_postprocess.py"), "Not the one registered hierarchy change")
    require(len(baseline["dirty_files_exact28"]) == 28, "User file scope differs")
    for path, expected in files.items():
        require(sha(confined(HERE / "source", path)) == expected, "Isolated r1 source changed")
        require(hashlib.sha256(git("cat-file", "blob", parent + ":" + path)).hexdigest() == old_files[path], "Committed r0 source differs")
    unchanged(baseline)
    ref = baseline["retained_ref"]
    require(ref == "refs/pipeline/candidates/M234-RVE-r1", "Unexpected new ref")
    require(not git("for-each-ref", "--format=%(refname)", ref), "r1 ref already exists")
    intent = HERE / "source_save_intent.json"
    index = HERE / "temporary.index"
    proof_path = HERE / "source_version.json"
    require(all(not p.exists() for p in [intent, index, Path(str(index) + ".lock"), proof_path]), "Single-use state exists; no automatic replay")
    new_json(intent, {"recorded_at": datetime.now(timezone.utc).isoformat(), "owner": baseline["owner"],
        "review_path": str(review_path), "review_sha256": sha(review_path), "helper_sha256": sha(Path(__file__)),
        "baseline_sha256": BASELINE_SHA, "retained_ref": ref, "source_parent_commit": parent,
        "changed_path_exact1": changed, "working_tree_writes": False, "no_replay": True})
    owner_check(baseline)
    git("read-tree", parent, index=index)
    data = confined(HERE / "source", changed).read_bytes()
    require(hashlib.sha256(data).hexdigest() == files[changed], "Changed bytes differ before object write")
    blob = git("hash-object", "-w", "--no-filters", "--stdin", data=data).decode().strip()
    git("update-index", "--add", "--cacheinfo", "100644", blob, changed, index=index)
    tree = git("write-tree", index=index).decode().strip()
    exact_diff(parent, tree, [("M", changed)])
    exact_diff(baseline["main_HEAD"], tree, [("A", p) for p in files])
    blobs = {}
    for path, expected in files.items():
        require(hashlib.sha256(git("cat-file", "blob", tree + ":" + path)).hexdigest() == expected, "Candidate tree blob differs")
        oid = git("rev-parse", tree + ":" + path).decode().strip()
        require(git("ls-tree", "-z", tree, "--", path).split(b"\t", 1)[0].decode() == "100644 blob " + oid, "Blob mode differs")
        blobs[path] = {"git_blob": oid, "sha256": expected}
    unchanged(baseline)
    commit = git("commit-tree", tree, "-p", parent, "-F", str(HERE / "commit_message.txt")).decode().strip()
    require(git("rev-list", "--parents", "-n", "1", commit).decode().strip() == commit + " " + parent, "r1 commit parent differs")
    unchanged(baseline)
    owner_check(baseline)
    git("update-ref", ref, commit, "0" * 40)
    unchanged(baseline)
    require(git("rev-parse", ref).decode().strip() == commit, "Retained r1 ref differs")
    proof = {"schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(), "owner": baseline["owner"],
        "candidate_id": "fine-leaf-receiver-conditioned-vector-exchange", "experiment_id": "M234-RVE", "implementation_revision": 1,
        "status": "RETAINED_R1_SOURCE_ONLY_FRESH_CONSTRUCTOR_NATIVE_RESOURCES_PROOFS_PENDING", "source_parent_commit": parent,
        "source_commit": commit, "source_tree": tree, "retained_ref": ref, "runtime_original_parent_commit": baseline["main_HEAD"],
        "source_files_exact9": files, "source_blobs_exact9": blobs, "changed_path_exact1": changed,
        "source_directory": str(HERE / "source"), "preregistration": baseline["preregistration"],
        "historical_r0_source_version": baseline["historical_source_version"], "historical_source_FROZEN": baseline["source_FROZEN"],
        "historical_CPU_operator_proofs": baseline["genuine_prior_proofs"], "historical_proofs_relabelled_as_r1": False,
        "independent_review": {"path": str(review_path), "sha256": sha(review_path)}, "helper_sha256": sha(Path(__file__)),
        "FROZEN_sha256": sha(HERE / "FROZEN.json"), "baseline_sha256": BASELINE_SHA,
        "main_HEAD": baseline["main_HEAD"], "actual_index_sha256": baseline["real_index_sha256"],
        "actual_index_entries_sha256": baseline["real_index_entries_sha256"], "main_HEAD_unchanged": True,
        "actual_index_bytes_unchanged": True, "actual_index_entries_unchanged": True, "all28_user_files_byte_exact": True,
        "all9_r0_working_tree_files_byte_exact": True, "Cluster_working_tree_remains_r0": True, "working_tree_writes": False,
        "r0_ref_unchanged": True, "r0_to_r1_diff_exactly_one_hierarchy_modification": True,
        "runtime_base_to_r1_diff_exactly_nine_additions": True, "main_HEAD_advanced": False,
        "pushed": False, "remote_mutation": False, "queue_or_shared_state_mutation": False,
        "new_constructor_discriminating_test": "PENDING", "native_common_init_TRAIN2": "PENDING", "resource_validation": "PENDING",
        "scientific_admission": "NOT_GRANTED", "efficacy": "UNKNOWN", "novelty": "UNKNOWN"}
    new_json(proof_path, proof)
    print(json.dumps({"source_commit": commit, "retained_ref": ref, "source_version_path": str(proof_path), "sha256": sha(proof_path)}))


if __name__ == "__main__":
    main()
