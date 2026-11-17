"""Close the tested NDE revision and validate its canonical technical admission."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
TICK = Path(__file__).resolve().parent
TOKEN = "2218a50249ea45588e5138890a7f4160"
CID = "hierarchy-native-distribution-embedding-composition"
SOURCE = "0747f6acec1c61018ec99acf2efa5329c9b3523c"
BASE = "f6257de79148581334ee495e6e2d60ccb525457c"
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
sys.path.insert(0, str(SKILL))
import closure
import pipeline_monitor as monitor


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT.resolve())
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def create(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def git(*args):
    return subprocess.check_output(
        ["git", "--no-optional-locks", "-C", str(ROOT / "Cluster"), *args],
        env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
    )


def main():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sys.dont_write_bytecode and os.environ["GIT_OPTIONAL_LOCKS"] == "0"
    actual_owner = {k: owner[k] for k in (
        "token", "thread_id", "generated_at", "deadline_at",
        "context_sha256", "pending_sha256")}
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == actual_owner["context_sha256"]
    assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == actual_owner["pending_sha256"]
    now = datetime.now(timezone.utc).isoformat()

    # Fresh observation; only the protected name sets are reused.
    old = read(ROOT / "pipeline/diagnostic_bundles/tick_801d029a/protected_assets_before.json")
    before = copy.deepcopy(old)
    before.update(owner=actual_owner, owner_token=TOKEN, recorded_at=now)
    before["head"] = git("rev-parse", "HEAD").decode().strip()
    assert before["head"] == BASE
    index = Path(git("rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = ROOT / "Cluster" / index
    before["index_sha256"] = sha(index)
    before["status_hex"] = git("status", "--porcelain=v1", "--untracked-files=all", "-z").hex()
    before["cached_paths_count"] = len(git("diff", "--cached", "--name-only", "-z").split(b"\0")) - 1
    assert before["cached_paths_count"] == 0
    assert before["index_sha256"] == old["index_sha256"]
    assert before["status_hex"] == old["status_hex"]
    for group in ("files", "WFC_source_paths", "LFT_source_paths"):
        before[group] = {n: sha(ROOT / "Cluster" / n) for n in old[group]}
        assert before[group] == old[group]
    before["protected_ledgers"] = {n: sha(ROOT / "pipeline" / n) for n in old["protected_ledgers"]}
    before["fixed_configs"] = {n: sha(ROOT / n) for n in old["fixed_configs"]}
    assert before["fixed_configs"] == old["fixed_configs"]
    assert len(before["files"]) == 28
    create(TICK / "protected_assets_before.json", before)

    prior = ROOT / "pipeline/diagnostic_bundles/tick_801d029a"
    normalized = prior / "nde_result_active/results_20261108T151307_234650Z"
    eq_review = prior / "nde_equivalence_actual_independent_review.json"
    norm_review = prior / "nde_normalization_actual_independent_review.json"
    prereview = TICK / "nde_admission_review/pre_admission_independent_review.json"
    assert sha(eq_review) == "70eae1bebda61e240f0643623ecc9d6dc3c2ca4ff0bae4f3caa99980a4770b35"
    assert sha(norm_review) == "9958db5ede4f3ff48e056e6f4cebc88dc970b844f2ed6a531c2f6f1e1a47d9ac"
    assert read(eq_review)["passed"] is True and read(norm_review)["passed"] is True
    outputs = [normalized / n for n in (
        "native_smoke.json", "resources.json", "constraints_independence.json",
        "draft_receipt.json", "normalization_audit.json")]
    outputs += [eq_review, norm_review, prior / "nde_equivalence_actual_root_independent_review.json",
                prior / "nde_equivalence_execution/equivalence_execution.json", prereview]
    outputs += [p for p in (prior / "equivalence_evidence").iterdir() if p.is_file()]
    evidence = [ref(p) for p in outputs]
    resolution = {
        "recorded_at": now, "root_owner": actual_owner, "candidate_id": CID,
        "code_commit": SOURCE, "implementation_revision": 1,
        "result": "passed", "scope": "TECHNICAL_IMPLEMENTATION_ONLY",
        "native_train2_and_whole_core_update": "PASSED_ORIGINAL_MEASUREMENTS",
        "original_paired_resource_gates": "PASSED",
        "standalone_constructed_core_equivalence": "PASSED_52_POSITIVE_2_NEGATIVE",
        "normalization_checks": 430, "evidence": evidence,
        "preserve_all_prior_negative_and_partial_results": True,
        "efficacy": "UNKNOWN", "novelty": "UNKNOWN", "long_run_stability": "UNKNOWN",
        "full_model_task_loss_equivalence": "NOT_ESTABLISHED_BY_CONSTRUCTED_CORE_TEST",
        "production_deployment": "PENDING_FRESH_BINDING_SOURCE_SYNC_AND_REVIEW",
        "training_started": False,
    }
    create(TICK / "revision1_actual_resolution.json", resolution)
    evidence.append(ref(TICK / "revision1_actual_resolution.json"))
    work_path = ROOT / "pipeline/research_work.json"
    work = read(work_path)
    candidate = next(c for c in work["candidates"] if c["id"] == CID)
    previous = copy.deepcopy(candidate)
    assert candidate["stage"] == "validation"
    assert candidate["code_commit"] == SOURCE
    assert len(candidate["revision_history"]) == 1
    revision = candidate["revision_history"][0]
    assert revision["result"] == "pending"
    create(TICK / "nde_candidate_before_admission.json", previous)
    for field in ("evidence", "result_evidence"):
        entries = revision.setdefault(field, [])
        for item in evidence:
            if item not in entries:
                entries.append(item)
    revision["result"] = "passed"
    closure.validate_revisions(ROOT, candidate, previous)
    revision_sha = closure.revision_digest(revision)
    decision_path = Path(monitor.log_decision(
        str(ROOT), "next_batch",
        "M233-NDE revision1 real native TRAIN2, original paired resource, repaired EQ and normalization independently passed.",
        "Grant technical experiment-first admission for exact source0747 on authorized server4 GPU0; deployment and launch remain gated.",
        "No efficacy or novelty claim. Keep all failed/partial history, fixed YAML/data/seed/loss/protocol, 20GB startup budget, three locks and manual pauses.",
        str(norm_review) + "; " + str(eq_review),
    ))
    receipt = read(normalized / "draft_receipt.json")
    receipt.update({
        "draft": False, "canonical_receipt": True, "admission_granted": True,
        "requires_root_and_independent_actual_review": False,
        "canonical_recorded_at": now, "canonical_root_owner": actual_owner,
        "implementation_revision_sha256": revision_sha,
        "decision": ref(decision_path),
        "independent_reviews": [ref(eq_review), ref(norm_review), ref(prereview)],
        "source_normalized_draft": ref(normalized / "draft_receipt.json"),
        "revision_resolution": ref(TICK / "revision1_actual_resolution.json"),
        "training_started": False,
        "production_deployment_required_before_launch": True,
    })
    receipt_path = ROOT / "pipeline/admissions/M233-NDE.json"
    assert not receipt_path.exists()
    create(receipt_path, receipt)
    for item in evidence + [ref(decision_path), ref(receipt_path)]:
        if item not in candidate["evidence"]:
            candidate["evidence"].append(item)
    candidate.update({
        "stage": "admission", "admission_receipt": ref(receipt_path)["path"],
        "scientific_admission": "EXPERIMENT_FIRST_TECHNICAL_PASSED_EFFICACY_UNKNOWN",
        "updated_at": now, "queued": False, "deployed": False, "training_started": False,
        "next_action": "Deploy exact admitted0747 by reviewed safe FF and canonical same-root safe_sync; install/review fresh NDE production capability and shim and switch its conda pointer. Then queue only M233 and invoke the original gated dispatcher, verifying increasing native steps. Never use the consumed NSD shim or historical leases.",
    })
    work["updated_at"] = now
    work["next_action"] = candidate["next_action"]
    monitor._save_json(str(work_path), work)
    task = {k: receipt[k] for k in ("id", "candidate_id", "config", "code_commit", "profile")}
    task.update(admission_receipt=ref(receipt_path)["path"], requires_exclusive_ownership=False)
    closure.admission(ROOT, task)
    create(TICK / "canonical_admission_validation.json", {
        "passed": True, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "owner": actual_owner, "receipt": ref(receipt_path),
        "candidate_id": CID, "implementation_revision_sha256": revision_sha,
        "task": task, "queue_added": False, "training_started": False,
    })
    print(json.dumps({"passed": True, "receipt": ref(receipt_path),
                      "revision_sha256": revision_sha, "queue_added": False}))


if __name__ == "__main__":
    main()
