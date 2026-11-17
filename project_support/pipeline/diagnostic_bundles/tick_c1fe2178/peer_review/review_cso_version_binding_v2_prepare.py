"""Independent v2 schema/delta validation; no generator import or execution."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TICK = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
HERE = TICK / "cso_version_binding"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
v1, v2 = HERE / "generate_version_binding.py", HERE / "generate_version_binding_v2.py"
assert sha(v1) == "4ca3209184c9efbba14b4ced40f2bfb80eb1a6894607a1f6ef9034e821f3ea63"
assert sha(v2) == "8852d05d4ae227029e1caeae7cf5380fa20ef225a80cbc349bda6ebcc2581e9c"
old = v1.read_text(encoding="utf-8"); new = v2.read_text(encoding="utf-8")
expected = old.replace("    for key in ('batches', 'losses', 'steps', 'core_calls', 'raw_bank_observations', 'inst_to_mask_path_observations'):\n", "    comparator_path = ROOT / 'pipeline/diagnostic_bundles/tick_71e15360/nde_execution/smoke_champion_execution.json'\n    require(ref(comparator_path)['sha256'] == 'adb5f2659a34b6c7622f20155fc4ff41fda08383df8c2b0c653ccb509b474a7b', 'Retained M95 natural TRAIN observation changed')\n    require(len(r['batches']) == 2 and r['batches'] == read(comparator_path)['result']['batches'], 'Natural batch hashes/metadata differ from original M95')\n    for key in ('losses', 'steps', 'core_calls', 'raw_bank_observations', 'inst_to_mask_path_observations'):\n")
expected = expected.replace("EXECUTION / 'source_binding.json', EXECUTION / 'native_manifest.json', proof_path, review_path]", "EXECUTION / 'source_binding.json', EXECUTION / 'native_manifest.json', proof_path, review_path,\n                   ROOT / 'pipeline/diagnostic_bundles/tick_71e15360/nde_execution/smoke_champion_execution.json']")
expected = expected.replace("default=TICK / 'peer_review/cso_version_binding_prepare_independent_review.json'", "default=TICK / 'peer_review/cso_version_binding_v2_prepare_independent_review.json'")
assert new == expected
ast.parse(new); compile(new, str(v2), "exec")
actual_path = TICK / "cso_native_execution/run_smoke_candidate_actual.json"
r = read(actual_path)["observation"]["result"]
comparator = ROOT / "pipeline/diagnostic_bundles/tick_71e15360/nde_execution/smoke_champion_execution.json"
assert sha(comparator) == "adb5f2659a34b6c7622f20155fc4ff41fda08383df8c2b0c653ccb509b474a7b"
assert len(r["batches"]) == 2 and r["batches"] == read(comparator)["result"]["batches"]
assert all("forward" not in value for value in r["batches"])
for key in ("losses", "steps", "core_calls", "raw_bank_observations", "inst_to_mask_path_observations"):
    assert len(r[key]) == 2 and [value["forward"] for value in r[key]] == [1, 2]
for name in ("version_bound_evidence.json", "native_smoke.version_bound.json", "resources.version_bound.summary.json"):
    assert not (HERE / name).exists()
owner = read(TICK / "current_owner_binding.json")
prior_review = OUT / "cso_version_binding_prepare_independent_review.json"
readonly_validation = HERE / "v2_readonly_input_validation.actual.json"
assert read(readonly_validation)["generation_executed"] is False
assert all(read(readonly_validation)["checks"].values())
review = {
    "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(), "passed": True, "material_concerns": [],
    "reviewer_thread_id": "/root/cso_peer", "reviewer_agent": "/root/cso_peer",
    "kind": "VERSION_ASSOCIATION_GENERATOR_V2_SCHEMA_CORRECTION_STATIC_REVIEW",
    "generator_sha256": sha(v2), "generator_ready_passed": True,
    "preserved_v1_generator_sha256": sha(v1), "preserved_v1_preparation_review_sha256": sha(prior_review),
    "v1_limitation": "The v1 static review missed its batches.forward schema error. Root's v1 execution failed closed before any derived output/admission. This v2 review supersedes v1 readiness for execution; v1 and its negative evidence remain immutable.",
    "verified": {"v2_exact_minimal_text_delta_only": True, "actual_batches_schema_no_forward": True,
        "exact_two_natural_M95_batches_hashes_and_metadata_pinned": True,
        "other_five_record_arrays_actual_forward_one_two_preserved": True,
        "M95_comparator_added_to_READSET_and_published_input_hashes": True,
        "all_existing_owner_actual_review_producer_failclosed_exact9_git_and_exclusive_output_guards_unchanged": True,
        "actual_native_and_resource_model_results_not_rerun_or_changed": True,
        "v1_and_old_review_preserved_no_derived_outputs_yet": True},
    "author_readonly_input_validation": {"path": readonly_validation.relative_to(ROOT).as_posix(), "sha256": sha(readonly_validation), "independent_execution_by_this_reviewer": False},
    "review_scope": "Independent static exact-delta and recorded actual-schema review, with the current smoke/resources independently reviewed separately. No generator import/execution/model rerun was performed by this reviewer. Real generation and separate derived-output review remain required.",
    "generator_executed_by_reviewer": False, "version_binding_generated_by_review": False,
    "scientific_admission": False, "SSH_performed_by_reviewer": False, "Torch_imported_by_reviewer": False, "GPU_use_by_reviewer": False}
target = OUT / "cso_version_binding_v2_prepare_independent_review.json"
with target.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(review, stream, indent=2); stream.write("\n")
print(json.dumps({"path": str(target), "sha256": sha(target), "generator_ready_passed": True}))
