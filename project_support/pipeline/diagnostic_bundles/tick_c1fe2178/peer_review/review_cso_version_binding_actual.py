"""Independent verification of derived association outputs; no generator/model execution."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
TICK = Path(__file__).resolve().parents[1]
HERE = TICK / "cso_version_binding"
OUT = Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
expected = {"version_bound_evidence.json": "4c44c69c847fb597cf275e5eeb115d2efe3320c3e0498d0214878127a95907a9",
            "native_smoke.version_bound.json": "bdd7151715a6c94e78dfb8e32a0e2073909241659aad51d223b8ba5774bd5799",
            "resources.version_bound.summary.json": "5d1121152fec6fef92825ee047e1f9f6735c2b4889127f50ebc81be8891dc15b"}
for name, value in expected.items(): assert sha(HERE / name) == value
owner = read(TICK / "current_owner_binding.json")
evidence, smoke, resources = (read(HERE / name) for name in expected)
raw_smoke = read(TICK / "cso_native_execution/run_smoke_candidate_actual.json")["observation"]["result"]
raw_resources = read(TICK / "cso_native_execution/run_resources_candidate_actual.json")["observation"]["result"]
assert evidence["owner"] == smoke["normalization_owner"] == resources["owner"] == owner
assert evidence["passed"] and evidence["material_concerns"] == []
assert evidence["associated_code_commit"] == smoke["code_commit"] == resources["associated_code_commit"] == "5413102c57b526035f3920b5e7a81f3b58ad764d"
assert evidence["actual_execution_code_commit"] == smoke["original_execution_code_commit"] == resources["actual_execution_code_commit"] == raw_smoke["code_commit"] == raw_resources["code_commit"] == "af45707d7b6089f764843337c5f88af285383f88"
assert evidence["actual_source_parent_commit"] == smoke["original_source_parent_commit"] == "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
assert evidence["actual_runtime_HEAD"] == smoke["runtime_original_parent_commit"] == resources["actual_runtime_HEAD"] == "b1e639b3ceb14bb5c65d9f81a084d41c834b951c"
assert evidence["raw_execution_owners_preserved"] == {"smoke": raw_smoke["owner"], "resources": raw_resources["owner"]}
assert smoke["original_execution_owner"] == raw_smoke["owner"] == owner
assert smoke["original_execution_observed_at"] == raw_smoke["observed_at"]
assert all(value["scientific_admission"] is False and value["efficacy"] == value["novelty"] == "UNKNOWN" for value in (evidence, smoke, resources))
assert evidence["new_execution_claimed"] is smoke["new_execution_claimed"] is False
assert evidence["raw_actual_source_owner_or_metadata_modified"] is False
assert evidence["producer"]["sha256"] == sha(ROOT / evidence["producer"]["path"]) == "8852d05d4ae227029e1caeae7cf5380fa20ef225a80cbc349bda6ebcc2581e9c"
assert read(OUT / "cso_version_binding_v2_prepare_independent_review.json")["generator_sha256"] == evidence["producer"]["sha256"]
for reference in evidence["inputs"] + smoke["evidence"] + [resources["actual"], resources["actual_independent_review"], resources["version_association"]]:
    assert sha(ROOT / reference["path"]) == reference["sha256"]
assert len(evidence["inputs"]) == 16
assert smoke["steps"] == raw_smoke["optimizer_steps"] == 2 and smoke["split"] == "train"
assert smoke["losses"] == [value["loss"] for value in raw_smoke["losses"]]
for key in ("native_data_loaded", "backward_finite", "intended_path_observed", "goal_sha256", "config"):
    assert smoke[key] == raw_smoke[key]
assert smoke["command"] == raw_smoke["actual_train_command"] and smoke["data_source"] == raw_smoke["data_source"]["train"]
assert resources["resource_gate_passed"] is True and read(OUT / "cso_resources_actual_independent_review.json")["resource_gate_passed"] is True
for key in ("batch_size", "lang_num_max", "warmup", "repeat", "parameters", "median_ms", "p90_ms", "peak_allocated_bytes", "peak_reserved_bytes", "measurement_scope", "exclusive_measurement_claimed", "full_optimizer_training_peak", "original_no_cluster_resource_delta", "validation_accuracy_evaluated_for_selection"):
    assert resources[key] == raw_resources[key]
assert resources["flops_g"] == raw_resources["profile"]["flops_g"]
proof = read(ROOT / "pipeline/diagnostic_bundles/tick_7caf419d/cso_integration_commit/commit_proof.json")
assert evidence["files_exact9_sha256"] == proof["files_exact9_sha256"]
assert evidence["historical_commit_proof_owner_preserved"] == proof["owner"]
git = "C:/Program Files (x86)/Git/cmd/git.exe"
for record in evidence["current_read_only_git_observations"]:
    worktree = Path(record["worktree"])
    def gitout(*args):
        return subprocess.check_output([git, "--no-optional-locks", "-c", "core.fsmonitor=false", "-c", "safe.directory=" + worktree.as_posix(), "-C", str(worktree), *args], env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"), timeout=30)
    assert record["clean"] and record["only_nine_additions"]
    assert gitout("rev-parse", "HEAD").decode().strip() == record["HEAD"]
    assert gitout("show", "-s", "--format=%P", record["HEAD"]).decode().strip() == record["parent"]
    assert gitout("status", "--porcelain=v1", "--untracked-files=all") == b""
    assert set(gitout("diff-tree", "--no-commit-id", "--name-status", "-r", record["HEAD"]).decode().splitlines()) == {"A\t" + name for name in evidence["files_exact9_sha256"]}
    for name, value in record["files_exact9"].items():
        assert value["sha256"] == evidence["files_exact9_sha256"][name] == sha(worktree / name)
        assert gitout("rev-parse", record["HEAD"] + ":" + name).decode().strip() == value["git_blob"] == proof["blob_ids"][name]
        assert hashlib.sha256(gitout("show", record["HEAD"] + ":" + name)).hexdigest() == value["sha256"]
assert evidence["current_read_only_git_observations"][0]["files_exact9"] == evidence["current_read_only_git_observations"][1]["files_exact9"]
review = {
    "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(), "passed": True, "material_concerns": [],
    "reviewer_thread_id": "/root/cso_peer", "reviewer_agent": "/root/cso_peer", "kind": "ACTUAL_DERIVED_EXACT_BYTE_VERSION_ASSOCIATION_REVIEW",
    "version_association_passed": True,
    "version_bound_evidence_sha256": expected["version_bound_evidence.json"],
    "native_smoke_sha256": expected["native_smoke.version_bound.json"],
    "normalized_smoke_sha256": expected["native_smoke.version_bound.json"],
    "resources_summary_sha256": expected["resources.version_bound.summary.json"],
    "associated_commit": "5413102c57b526035f3920b5e7a81f3b58ad764d", "commit_parent": "b1e639b3ceb14bb5c65d9f81a084d41c834b951c",
    "actual_execution_commit": "af45707d7b6089f764843337c5f88af285383f88", "actual_source_parent": "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e",
    "exact_nine_added_blobs_verified": True, "commit_worktree_clean": True,
    "raw_actual_source_owner_metadata_and_negative_v1_evidence_unchanged": True,
    "source_model_yaml_seed_data_loss_schedule_and_resource_protocol_unchanged": True,
    "all16_input_and_derived_evidence_hashes_verified": True,
    "native_smoke_passed": True, "resource_gate_passed": True,
    "scientific_admission": False, "training_launched": False, "new_execution_claimed": False,
    "timing_interpretation": "Resource timing is a non-simultaneous historical comparison, not architectural speedup; full optimizer peak and efficacy remain unknown.",
    "review_scope": "Actual v2-derived outputs faithfully retain current native smoke/resource observations and bind a distinct exact-byte association to clean integration541(parentb1). Actual execution loaded af457(parentd214) on runtimeb1; it did not check out541. Both clean source worktrees, parents, nine additions, raw git blobs and working bytes were independently rechecked read-only. No source/replay/admission/launch was performed by this review.",
    "SSH_performed_by_reviewer": False, "Torch_imported_by_reviewer": False, "GPU_use_by_reviewer": False,
    "prepared_generator_or_model_execution_performed": False, "shared_work_queue_memory_ledger_SERVERS_goal_or_source_edits": False}
target = OUT / "cso_version_binding_actual_independent_review.json"
with target.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(review, stream, indent=2); stream.write("\n")
print(json.dumps({"path": str(target), "sha256": sha(target), "version_association_passed": True}))
