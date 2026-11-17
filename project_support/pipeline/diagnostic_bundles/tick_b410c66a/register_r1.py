"""Prospectively register one evidenced RVE constructor implementation revision."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "b410c66a6c6243e1bbb8f970d1bd8c29"
CID = "fine-leaf-receiver-conditioned-vector-exchange"
assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
raw_owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
owner = {k: raw_owner[k] for k in (
    "token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256"
)}
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])


def ref(name, expected=None):
    path = ROOT / name
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert expected is None or digest == expected
    return {"path": name, "sha256": digest}


def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


failure = ref(
    "pipeline/diagnostic_bundles/tick_915589b3/rvec_native_execution_v2/run_smoke_candidate_actual.json",
    "fff18fe7ed274780db8829e77b66b4342555f7609b7b7dbcf083d53e63895da8",
)
review = ref(
    "pipeline/diagnostic_bundles/tick_915589b3/operational_review/rvec_native_actual_independent_review_v2.json",
    "87b71289253b21ccd14ce09063976fa966ab3d10582d287cbebf1a728f8cc145",
)
plan = ref(
    "pipeline/diagnostic_bundles/tick_915589b3/revision_plan/conditional_rng_guard_plan.json",
    "800a6b521b7b661f64467b31fe1e2807b92ba5090743ddeb3d97e593acb87958",
)
actual = json.loads((ROOT / failure["path"]).read_text())["observation"]["result"]
common = actual["original_common_initialization_comparison"]
assert common["passed"] is False
assert all(common[k] for k in ("same_names", "same_shapes", "same_dtypes"))
assert len(common["different_parameter_names"]) == 252
assert all(n.startswith(("dec.encoder_layers.", "dec.decoder_layers.")) for n in common["different_parameter_names"])
assert actual["native_loss_forwards"] == actual["optimizer_steps"] == 0
work_path = ROOT / "pipeline/research_work.json"
work_bytes = work_path.read_bytes()
work = json.loads(work_bytes.decode("utf-8-sig"))
candidate = next(item for item in work["candidates"] if item["id"] == CID)
assert candidate["stage"] == "validation" and candidate["failure_scope"] == "implementation"
assert candidate["code_commit"] == "0f8cc0f978b38c24e159d3a2d37344f59cc9a0be"
assert not candidate.get("revision_history")
now = datetime.now(timezone.utc).isoformat()
revision = {
    "revision": 1, "failure_scope": "implementation",
    "reason": "The unguarded new fine-exchange CPU constructor consumes the shared RNG stream. In actual r0 common initialization, all841 names/shapes/dtypes align and589 values match, but60 later encoder and192 decoder parameter values differ. This is an implementation explanation to test, not a trained mechanism rejection.",
    "change": "In C2F_ClusterAttn_RVEC_CSORT.__init__, after unchanged super().__init__, wrap ONLY FineLeafReceiverVectorExchange construction in torch.random.fork_rng(devices=[]). Keep existing fine Identity replacements, all other eight files, initializer values, formula, topology and YAML/training numbers unchanged. No manual_seed, parameter copy, common-layer reinitialization, exclusion expansion or post-comparison repair.",
    "prediction": "From the same new-core entry state, the guarded and unguarded core generate identical five parameter values, while the guarded caller CPU RNG is exactly restored. Fresh native r1 then matches all original common names/shapes/dtypes/values/hashes at the unchanged gate before the first natural TRAIN batch.",
    "discriminating_control": [
        "Fresh actual isolated constructor observation from equal entry RNG: all five core tensors/hash identical; unguarded caller stream advances and guarded caller stream is unchanged. Restore Python/NumPy/Torch caller state; CUDA remains uninitialized.",
        "Fresh native original M95 reference and revised candidate common initialization with the same three prefix exclusions; compare actual complete names/shapes/dtypes/values/hashes, retain middle/coarse FFNs/norms and stop before TRAIN on any mismatch.",
        "If common gate passes, original two natural TRAIN batches/seed1999/batch2/workers4/original criterion backward and actual wr/wd/w2/b1/b2 updates; no batch substitution. Then unchanged original resource protocol and independent actual review before admission.",
    ],
    "preregistered_at": now, "failure_evidence": [failure, review],
    "result": "pending", "evidence": [plan], "result_evidence": [],
}
prereg = {
    "schema_version": 1, "owner": owner, "candidate_id": CID, "experiment_id": "M234-RVE",
    "recorded_at": now, "source_parent": candidate["code_commit"], "revision": revision,
    "source_implementation_or_revised_test_performed": False,
    "stable_hypothesis_preserved": candidate["hypothesis"], "budget_used_before": 0,
    "budget_limit": 2, "efficacy": "UNKNOWN", "novelty": "UNKNOWN",
}
prereg_path = HERE / "rve_r1_preregistration.json"
save(prereg_path, prereg)
candidate["revision_history"] = [revision]
candidate["evidence"].append(ref(prereg_path.relative_to(ROOT).as_posix()))
candidate["updated_at"] = now
candidate["next_action"] = "Implement only the prospectively registered r1 constructor RNG boundary in an isolated new packet, review and retain exact source without touching main HEAD/index/user files; execute its discriminating constructor test and original native common/TRAIN2/resources with new current-owner bindings. No admission before all actual gates."
work["updated_at"] = now
temporary = work_path.with_name("research_work.b410c66a.registration.tmp")
assert not temporary.exists()
save(temporary, work)
os.replace(temporary, work_path)
save(HERE / "registration_audit.json", {
    "owner": owner, "preregistered_at": now,
    "preregistration": ref(prereg_path.relative_to(ROOT).as_posix()),
    "research_work_sha256_before": hashlib.sha256(work_bytes).hexdigest(),
    "research_work_sha256_after": hashlib.sha256(work_path.read_bytes()).hexdigest(),
    "source_changed": False, "revised_results_seen": False,
})
print(json.dumps({"status": "REVISION1_PROSPECTIVELY_REGISTERED_SOURCE_UNCHANGED",
                  "preregistered_at": now, "preregistration": ref(prereg_path.relative_to(ROOT).as_posix())}))
