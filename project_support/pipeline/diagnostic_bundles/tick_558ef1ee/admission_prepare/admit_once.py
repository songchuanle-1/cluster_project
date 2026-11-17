"""Default NOOP. Root-only, peer-bound, single-use admission recording; no launch."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path("D:/project/cluster_project").resolve()
HERE = Path(__file__).resolve().parent
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
OWNER_KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def within(relative):
    path = (ROOT / relative).resolve()
    require(path.is_relative_to(ROOT), "Path outside project")
    return path


def new_bytes(path, data):
    require(path.resolve().is_relative_to(ROOT), "Output outside project")
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def new_json(path, value):
    new_bytes(path, encoded(value))


def replace_if_exact(path, expected, value):
    require(digest(path) == expected, "Shared target changed before replace: " + str(path))
    temp = path.with_name(path.name + ".558ef1ee.M234-RVE.new")
    new_bytes(temp, encoded(value))
    require(digest(path) == expected, "Shared target changed after preparation")
    os.replace(temp, path)


def owner_check(base):
    current = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    require({k: current[k] for k in OWNER_KEYS} == base["owner"], "Current owner differs")
    require(os.environ.get("CODEX_THREAD_ID") == base["owner"]["thread_id"], "Only owning root thread may execute")
    require(datetime.now(timezone.utc) < datetime.fromisoformat(base["owner"]["deadline_at"]), "Owner deadline expired")
    require(digest(ROOT / "pipeline/headless/.tick_context.json") == base["owner"]["context_sha256"], "Context changed")
    require(digest(ROOT / "pipeline/headless/.tick_context_state.next.json") == base["owner"]["pending_sha256"], "Pending state changed")
    for relative, expected in base["control_hashes"].items():
        require(digest(within(relative)) == expected, "Control file changed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--review", type=Path)
    parser.add_argument("--review-sha256")
    args = parser.parse_args()
    if not args.execute_root:
        print("NOOP: --execute-root and genuine bound independent review are required.")
        return
    require(sys.dont_write_bytecode, "Run with python -B")
    require(args.review is not None and args.review_sha256, "Independent review missing")
    base = read(HERE / "baseline.json")
    frozen = read(HERE / "FROZEN.json")
    require(frozen["owner"] == base["owner"], "Freeze owner differs")
    for relative, expected in frozen["files"].items():
        path = (HERE / relative).resolve()
        require(path.is_relative_to(HERE) and digest(path) == expected, "Frozen packet changed")
    review_path = args.review.resolve()
    require(review_path.is_relative_to(HERE.parent) and digest(review_path) == args.review_sha256, "Review path/hash differs")
    review = read(review_path)
    require(review.get("passed") is True and review.get("material_concerns") == [], "Genuine peer did not pass")
    require(review.get("owner") == base["owner"], "Review owner differs")
    require(review.get("reviewer_thread_id") not in [None, "", base["owner"]["thread_id"]], "Review not independent")
    for key, actual in [
        ("helper_sha256", digest(Path(__file__))), ("baseline_sha256", digest(HERE / "baseline.json")),
        ("FROZEN_sha256", digest(HERE / "FROZEN.json")),
    ]:
        require(review.get(key) == actual, "Review binding differs: " + key)
    owner_check(base)
    require(digest(SKILL / "closure.py") == base["canonical_closure_sha256"], "Canonical closure changed")
    require(digest(SKILL / "experiment_first.py") == base["canonical_experiment_first_sha256"], "Canonical smoke schema changed")
    for reference in base["references"].values():
        require(digest(within(reference["path"])) == reference["sha256"], "Historical evidence changed")
    sys.path.insert(0, str(SKILL))
    import closure
    lock = (ROOT / ".pipeline.lock").open("r+b")  # Existing canonical monitor inode; never create/delete.
    locked = False
    try:
        if os.name == "nt":
            import msvcrt
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locked = True
        owner_check(base)
        work_path, queue_path = ROOT / "pipeline/research_work.json", ROOT / "pipeline/queue.json"
        require(digest(work_path) == base["research_work_sha256"], "Research state changed")
        require(digest(queue_path) == base["queue_sha256"], "Queue changed")
        work, queue = read(work_path), read(queue_path)
        before_work, before_queue = read(work_path), read(queue_path)
        matches = [c for c in work["candidates"] if c.get("id") == base["candidate_id"]]
        require(len(matches) == 1 and matches[0] == base["candidate_before"], "Candidate baseline differs")
        candidate = matches[0]
        require(candidate["revision_history"] == base["revision_history"], "Completed revision changed")
        require(closure.revision_digest(candidate["revision_history"][-1]) == base["implementation_revision_sha256"], "Revision digest changed")
        require(candidate["revision_history"][-1]["result"] == "passed", "Revision not passed")
        closure.validate_revisions(ROOT, candidate)
        require(not any(t.get("id") == "M234-RVE" for tasks in queue["gpu_queues"].values() for t in tasks), "M234 already queued")
        task = read(HERE / "queue_task.draft.json")
        receipt = read(HERE / "receipt.draft.json")
        receipt_path = within(base["receipt_path"])
        decision_path = within(base["decision"]["path"])
        require(not receipt_path.exists(), "Receipt exists; no automatic replay")
        intent, result_path = HERE / "admission_intent.json", HERE / "admission_actual.json"
        require(not intent.exists() and not result_path.exists(), "Single-use state exists; reconcile, never replay")
        require(receipt_path.parent.is_dir() and decision_path.parent.is_dir(), "Canonical output directories missing")
        decision_bytes = (HERE / "decision.draft.md").read_bytes()
        require(hashlib.sha256(decision_bytes).hexdigest() == base["decision"]["sha256"], "Decision draft changed")
        if decision_path.exists():
            require(digest(decision_path) == base["decision"]["sha256"], "Existing root decision differs")
        peer_ref = {"path": review_path.relative_to(ROOT).as_posix(), "sha256": args.review_sha256}
        receipt["gates"]["independence"]["evidence"].append(peer_ref)
        receipt["normalization_independent_review"] = peer_ref
        receipt["admitted_at"] = datetime.now(timezone.utc).isoformat()
        closure.experiment_first.validate_smoke(ROOT, receipt)
        for gate in closure.experiment_first.GATES:
            require(receipt["gates"][gate]["passed"] is True, "Required gate not passed")
            for reference in receipt["gates"][gate]["evidence"]:
                closure.artifact(ROOT, reference)
        new_json(intent, {"recorded_at": datetime.now(timezone.utc).isoformat(), "owner": base["owner"],
            "FROZEN_sha256": digest(HERE / "FROZEN.json"), "peer_review": peer_ref,
            "research_work_before_sha256": base["research_work_sha256"], "queue_before_sha256": base["queue_sha256"],
            "receipt_path": str(receipt_path), "decision_path": str(decision_path), "no_replay": True, "no_launch": True})
        owner_check(base)
        if not decision_path.exists():
            new_bytes(decision_path, decision_bytes)
        new_json(receipt_path, receipt)
        receipt_ref = {"path": base["receipt_path"], "sha256": digest(receipt_path)}
        patch = read(HERE / "candidate_patch.draft.json")
        candidate.update(patch)
        candidate["gates"] = receipt["gates"]
        candidate["updated_at"] = receipt["admitted_at"]
        candidate["normalization_independent_review"] = peer_ref
        for reference in [receipt["native_smoke"], base["decision"], peer_ref, receipt_ref, *[
                evidence for gate in receipt["gates"].values() for evidence in gate["evidence"]]]:
            if reference not in candidate["evidence"]:
                candidate["evidence"].append(reference)
        require(candidate["revision_history"] == base["revision_history"], "Completed revision mutation refused")
        for old, new in zip(before_work["candidates"], work["candidates"]):
            require(old.get("id") == base["candidate_id"] or old == new, "Unrelated candidate changed")
        queue["gpu_queues"]["server-4"].append(task)
        require(queue["gpu_queues"]["server-4"][:-1] == before_queue["gpu_queues"]["server-4"], "Existing server4 queue changed")
        for server, tasks in before_queue["gpu_queues"].items():
            require(server == "server-4" or queue["gpu_queues"][server] == tasks, "Unrelated queue changed")
        for ident, protected in base["protected_queue_tasks"].items():
            require(next(t for tasks in queue["gpu_queues"].values() for t in tasks if t.get("id") == ident) == protected, "User pause changed")
        owner_check(base)
        replace_if_exact(work_path, base["research_work_sha256"], work)
        replace_if_exact(queue_path, base["queue_sha256"], queue)
        try:
            actual_task = next(t for t in read(queue_path)["gpu_queues"]["server-4"] if t.get("id") == "M234-RVE")
            checked = closure.admission(ROOT, actual_task)  # Actual canonical files after root mutation.
            require(checked == receipt, "Canonical actual receipt differs")
            require(closure.revision_digest(read(work_path)["candidates"][next(
                i for i,c in enumerate(work["candidates"]) if c["id"] == base["candidate_id"]
            )]["revision_history"][-1]) == base["implementation_revision_sha256"], "Completed revision changed after recording")
            new_json(result_path, {"recorded_at": datetime.now(timezone.utc).isoformat(), "owner": base["owner"],
                "canonical_closure_admission_validated": True, "receipt": receipt_ref,
                "decision": base["decision"], "peer_review": peer_ref,
                "research_work_after_sha256": digest(work_path), "queue_after_sha256": digest(queue_path),
                "completed_revision_digest_unchanged": base["implementation_revision_sha256"],
                "M206_M227_pauses_unchanged": True, "M234_status": "waiting",
                "dispatch_hold": task["dispatch_hold"], "training_started": False, "new_measurements": False})
        except BaseException as error:
            new_json(HERE / "admission_uncertain.json", {"recorded_at": datetime.now(timezone.utc).isoformat(),
                "owner": base["owner"], "error": str(error), "no_replay": True,
                "instruction": "Shared recording may be partial; root must reconcile exact files. No rollback or automatic replay."})
            raise
        print(json.dumps({"canonical_admission": True, "receipt_sha256": digest(receipt_path),
            "actual_proof_path": str(result_path), "actual_proof_sha256": digest(result_path), "queued": "M234-RVE waiting with production-setup hold"}))
    finally:
        if locked:
            if os.name == "nt":
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


if __name__ == "__main__":
    main()
