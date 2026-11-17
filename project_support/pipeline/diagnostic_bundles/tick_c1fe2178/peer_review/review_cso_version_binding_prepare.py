"""Static review only of the version association generator; never imports it."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TICK = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
GEN = TICK / "cso_version_binding/generate_version_binding.py"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
assert sha(GEN) == "4ca3209184c9efbba14b4ced40f2bfb80eb1a6894607a1f6ef9034e821f3ea63"
owner = read(TICK / "current_owner_binding.json")
source = GEN.read_text(encoding="utf-8")
tree = ast.parse(source)
compile(source, str(GEN), "exec")
functions = {node.name: ast.get_source_segment(source, node) for node in tree.body if isinstance(node, ast.FunctionDef)}
assert "if not args.execute:" in functions["main"] and functions["main"].index("return") < functions["main"].index("generate(args)")
assert "raise ValueError(message)" in functions["require"]
assert "review['owner'] == owner" in functions["current_review"] and "review['actual_sha256']" in functions["current_review"]
assert "len(owner) == 6" in functions["owner_guard"] and "not sys.flags.optimize" in functions["owner_guard"]
assert "safe.directory=" in functions["git"] and "--no-optional-locks" in functions["git"]
assert "only_nine_additions" in functions["verify_git"] and "'cat-file', 'blob'" in functions["verify_git"]
assert "observed[0]['files_exact9'] == observed[1]['files_exact9']" in functions["verify_git"]
generate = functions["generate"]
for required in ("generator_ready_passed", "source_and_native_protocol_review_passed", "native_smoke_passed", "resource_gate_passed", "verify_git(proof, exact9)", "for path, digest in READSET.items()", "all(not (HERE / name).exists() for name in outputs)"):
    assert required in generate and generate.index(required) < generate.index("save(outputs[0], evidence)")
assert "open('x'" in generate
assert "actual_execution_code_commit': SOURCE" in generate and "associated_code_commit': INTEGRATED" in generate
assert "new_execution_claimed': False" in generate and "scientific_admission': False" in generate
assert "raw_actual_source_owner_or_metadata_modified': False" in generate
assert "full_optimizer_training_peak" in generate and "original_no_cluster_resource_delta" in generate
prep = read(TICK / "cso_version_binding/preparation.NOT_RUN.json")
assert prep["owner"] == owner and prep["generator"]["sha256"] == sha(GEN)
assert prep["version_binding_generated"] is False and prep["scientific_admission"] is False
for name in prep["outputs_do_not_exist"]: assert not (GEN.parent / name).exists()
native_review = read(OUT / "cso_native_bound_independent_review.json")
assert native_review["passed"] and native_review["verified"]["source9_bytes_equal_both_distinct_native_and_integrated_commits"]
proof_path = ROOT / "pipeline/diagnostic_bundles/tick_7caf419d/cso_integration_commit/commit_proof.json"
review_path = ROOT / "pipeline/diagnostic_bundles/tick_7caf419d/peer_review/cso_integration_independent_review.json"
assert sha(proof_path) == "41dd72acfb62ff4fc7ff690f751c820fca80536dc3b5b552a62c704ea5a99c7a"
assert sha(review_path) == "04608ef80c5f5590e785038d471fe9127d501d0734c85e4adb6058cc401ace44"
assert read(review_path)["commit_proof_sha256"] == sha(proof_path)
review = {
    "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
    "passed": True, "material_concerns": [], "reviewer_thread_id": "/root/cso_peer", "reviewer_agent": "/root/cso_peer",
    "kind": "VERSION_ASSOCIATION_GENERATOR_STATIC_PREPARATION_REVIEW",
    "generator_sha256": sha(GEN), "generator_ready_passed": True,
    "source_commit": "af45707d7b6089f764843337c5f88af285383f88",
    "source_parent_commit": "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e",
    "associated_commit": "5413102c57b526035f3920b5e7a81f3b58ad764d",
    "associated_parent_and_actual_runtime": "b1e639b3ceb14bb5c65d9f81a084d41c834b951c",
    "verified": {"default_NOP_and_explicit_execute": True, "owner6_lease_context_pending_root_only_and_expiry_guards": True,
        "current_distinct_review_exact_producer_actual_and_hash_bindings": True,
        "both_clean_retained_worktree_commit_parents_exact_nine_additions_blobIDs_and_SHA_equality_required": True,
        "actual_smoke_common841_core9_full_backward_and_resources_gate_required": True,
        "raw_execution_source_and_historical_owner_metadata_preserved": True,
        "last_readset_hash_recheck_and_exclusive_no_overwrite_outputs": True,
        "sourceaf457_runtimeb1_distinct_from_derived541_association_explicit": True,
        "no_new_execution_admission_sync_GPU_or_efficacy_claim": True},
    "review_scope": "Static generator readiness only. Both source commits and exact9 bytes were independently verified in the current native-source review. The generator requires real current raw smoke/resources and exact independent PASS reviews before deriving a byte association; resource outputs have not been observed by this preparation review. Root execution and a separate review of actual derived outputs remain required.",
    "generator_executed_by_reviewer": False, "version_binding_generated_by_review": False,
    "actual_resource_gate_passed_by_this_review": False, "scientific_admission": False,
    "SSH_performed_by_reviewer": False, "Torch_imported_by_reviewer": False, "GPU_use_by_reviewer": False,
    "prepared_module_import_or_execution_performed": False, "shared_work_queue_memory_ledger_SERVERS_goal_or_source_edits": False}
target = OUT / "cso_version_binding_prepare_independent_review.json"
with target.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(review, stream, indent=2); stream.write("\n")
print(json.dumps({"path": str(target), "sha256": sha(target), "generator_ready_passed": True}))
