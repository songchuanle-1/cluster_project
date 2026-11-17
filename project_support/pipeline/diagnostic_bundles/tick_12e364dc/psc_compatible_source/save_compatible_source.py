"""Save original PSC blobs on current d20 using a separate index; no checkout."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path("D:/project/cluster_project")
REPO = ROOT / "Cluster"
HERE = Path(__file__).resolve().parent
EXPECTED_HERE = ROOT / "pipeline/diagnostic_bundles/tick_12e364dc/psc_compatible_source"
TOKEN = "12e364dc14cd4e1195532c7fd295b834"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
CHILD = "01a1a684-e37c-7023-a69a-924d4014a2d5"
BASE = "d20eb221eff6584b67d4e9b5673559d0e1cb735b"
OLD = "a709fe0cf93690d0695fd9d9a6f6e0e865340a7a"
OLD_PARENT = "07ef534a6e44f22bd7b2d083550ebd7823d1d3d3"
CID = "hierarchy-native-position-feature-cross-scatter-composition"
REF = "refs/codex/cluster_project/psc-compatible-d20-12e364dc"
OLD_TICK = ROOT / "pipeline/diagnostic_bundles/tick_0f3c54ec"
PRIVATE = OLD_TICK / "reserve_candidate_prepare"
OLD_PROOF = OLD_TICK / "psc_version_prepare/isolated_source_version.json"
OLD_REVIEW = OLD_TICK / "psc_source_independent_review.json"
OLD_BASELINE = OLD_TICK / "protected_assets_before.json"
FF_RESULT = ROOT / "pipeline/diagnostic_bundles/tick_154767c2/hvd_deployment_execute/ff_result.json"
OWNER_KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
GIT = ["C:/Program Files (x86)/Git/cmd/git.exe", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(REPO)]
DEFAULT_ENV = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1")
DEFAULT_ENV.pop("GIT_INDEX_FILE", None)
ALT_INDEX = HERE / "psc_compatible.index"
ALT_ENV = dict(DEFAULT_ENV, GIT_INDEX_FILE=str(ALT_INDEX))
CHECKS = []


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fsha(path):
    return sha(Path(path).read_bytes())


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return {"path": Path(path).relative_to(ROOT).as_posix(), "sha256": fsha(path)}


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    CHECKS.append({"name": name, "passed": True})


def guard():
    assert HERE.resolve() == EXPECTED_HERE.resolve()
    assert os.environ.get("CODEX_THREAD_ID") == CHILD != THREAD
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    mode = read(ROOT / "pipeline/execution_mode.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == mode["target_thread_id"] == THREAD
    assert mode["mode"] == "foreground"
    now = datetime.now(timezone.utc)
    assert datetime.fromisoformat(owner["generated_at"]) <= now < datetime.fromisoformat(owner["deadline_at"])
    assert fsha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
    assert fsha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
    return {key: owner[key] for key in OWNER_KEYS}


def git(*args, mutation=False, alternate=False):
    if mutation:
        guard()
        assert args[0] in {"read-tree", "update-index", "write-tree", "commit-tree", "update-ref"}
        if args[0] == "update-ref":
            assert not alternate and args[1] == REF and len(args) == 4 and args[3] == "0" * 40
        else:
            assert alternate
    result = subprocess.run(GIT + list(args), env=ALT_ENV if alternate else DEFAULT_ENV,
                            capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")[-1200:]
    return result.stdout


def tree(commit):
    output = {}
    for part in git("ls-tree", "-r", "-z", commit).split(b"\0"):
        if part:
            header, name = part.split(b"\t", 1)
            output[name.decode("utf-8")] = tuple(header.decode().split())
    return output


def protected(baseline):
    status = git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    names = [part.decode("utf-8")[3:] for part in status.split(b"\0") if part]
    assert len(names) == len(set(names))
    index = Path(git("rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = REPO / index
    return {
        "main_head": git("rev-parse", "HEAD").decode().strip(),
        "main_ref": git("symbolic-ref", "HEAD").decode().strip(),
        "index_sha256": fsha(index),
        "index_entries_sha256": sha(git("ls-files", "--stage", "-z")),
        "status_sha256": sha(status),
        "original_user20": {name: fsha(REPO / name) for name in baseline["dirty_files"]},
        "all_porcelain_user_files": {name: fsha(REPO / name) for name in names},
    }


def shared_hashes():
    return {name: fsha(ROOT / name) for name in (
        "SERVERS.yaml", "pipeline/goal.json", "pipeline/queue.json", "pipeline/running.json",
        "pipeline/research_work.json", "pipeline/codex_memory.md")}


def frozen_snapshot():
    path = PRIVATE / "FROZEN.json"
    digest = fsha(path)
    assert digest == "263f6acb4ec442e175c91a9c87280c44420d46d518982071a29261cfefcc8a0a"
    declared = read(path)["files"]
    assert all(fsha(PRIVATE / name) == value for name, value in declared.items())
    return {"manifest": ref(path), "declared_file_count": len(declared),
            "all_declared_files_verified": True, "declared_files": declared}


owner = guard()
assert not ALT_INDEX.exists() and not (HERE / "compatible_source_version.json").exists()
check("prior_source_proof_hash", fsha(OLD_PROOF) == "ad7cf1fea60aa7546e7d1aed928737742f84f76970e2afda44060e2cc72c37f8")
check("prior_independent_source_review_hash", fsha(OLD_REVIEW) == "a167ed2fac7bfd15a617c05e4f318634e7a3f8b7370376b271fcbb4d30cbce19")
check("original_user20_baseline_hash", fsha(OLD_BASELINE) == "c99dc7fb7b26bbab4425ee767632a734ea9692b3b808d77fb0a91fa63912e6dd")
check("legitimate_HVD_ff_baseline_hash", fsha(FF_RESULT) == "76749eeeb74aa4faef4d2c9dce5a4f5016c13e2feacee2194dd3d2a22bfd4617")
old_proof, old_review, baseline, ff = map(read, (OLD_PROOF, OLD_REVIEW, OLD_BASELINE, FF_RESULT))
check("prior_a709_parent07ef_reviewed", old_proof["source_commit"] == old_review["source_commit"] == OLD
      and old_proof["parent_commit"] == old_review["source_parent_commit"] == OLD_PARENT and old_review["passed"] is True)
check("actual_prior_single_parent", git("rev-list", "--parents", "-n", "1", OLD).decode().split() == [OLD, OLD_PARENT])
expected = old_proof["source_files_exact9"]
check("same_original_exact9_manifest", len(expected) == 9
      and expected == old_review["source_files_exact9"] == read(PRIVATE / "source_manifest.json")["source_files_exact9"])
candidate = next(c for c in read(ROOT / "pipeline/research_work.json")["candidates"] if c["id"] == CID)
check("current_existing_candidate_keeps_original_source", candidate["source_commit"] == candidate["code_commit"] == OLD
      and candidate["source_files_exact9"] == expected)
frozen_before = frozen_snapshot()
check("original19_frozen_files_match", frozen_before["declared_file_count"] == 19)
proposal_hash = fsha(PRIVATE / "proposal.json")
proposal = read(PRIVATE / "proposal.json")
check("original_proposal_source_NULL_and_parent_preserved", proposal["source_commit"] is None and proposal["source_parent_commit"] == OLD_PARENT)
before = protected(baseline)
shared_before = shared_hashes()
check("actual_main_is_d20_and_main_ref", before["main_head"] == ff["local_head"] == BASE and before["main_ref"] == "refs/heads/main")
check("actual_index_matches_legitimate_ff_baseline", before["index_sha256"] == ff["index_sha256_after"]
      and before["index_entries_sha256"] == ff["index_entries_sha256_after"])
check("original20_user_bytes_unchanged", len(before["original_user20"]) == 20 and before["original_user20"] == baseline["dirty_files"])
check("original_porcelain_status_unchanged", before["status_sha256"] == baseline["status_sha256"])
check("all28_porcelain_files_observed", len(before["all_porcelain_user_files"]) == 28)
check("no_staged_changes", not git("diff", "--cached", "--name-only", "-z"))
base_tree, old_tree = tree(BASE), tree(OLD)
check("new9_paths_absent_from_current_tree_and_checkout", not set(expected).intersection(base_tree)
      and not any((REPO / name).exists() for name in expected))
old_delta = git("diff-tree", "--no-commit-id", "--name-status", "-r", OLD).decode().splitlines()
check("prior_source_exact9_additions", sorted(old_delta) == sorted("A\t" + name for name in expected))
blobs, compiled = {}, []
for name, digest in sorted(expected.items()):
    mode, kind, oid = old_tree[name]
    raw = git("cat-file", "blob", oid)
    prior_blob = old_proof["git_blobs_exact9"][name]
    prior_oid = prior_blob if isinstance(prior_blob, str) else prior_blob["blob"]
    check("same_blob_bytes_private_and_reviewed:" + name,
          mode == "100644" and kind == "blob" and sha(raw) == digest
          and raw == (PRIVATE / "source" / name).read_bytes()
          and prior_oid == oid)
    if name.endswith(".py"):
        compile(raw, name, "exec")
        compiled.append(name)
    blobs[name] = {"mode": mode, "kind": kind, "blob": oid, "sha256": digest}
check("eight_original_python_sources_compile_without_import", len(compiled) == 8)
guard()
git("read-tree", BASE, mutation=True, alternate=True)
for name, item in blobs.items():
    git("update-index", "--add", "--cacheinfo", item["mode"] + "," + item["blob"] + "," + name,
        mutation=True, alternate=True)
new_tree_oid = git("write-tree", mutation=True, alternate=True).decode().strip()
commit = git("commit-tree", new_tree_oid, "-p", BASE, "-m",
             "Preserve original PSC source blobs on current HVD parent without a model revision",
             mutation=True, alternate=True).decode().strip()
guard()
git("update-ref", REF, commit, "0" * 40, mutation=True)
check("new_exact_single_d20_parent", git("rev-list", "--parents", "-n", "1", commit).decode().split() == [commit, BASE])
check("new_isolated_ref_matches", git("rev-parse", REF).decode().strip() == commit)
new_tree = tree(commit)
delta = git("diff-tree", "--no-commit-id", "--name-status", "-r", commit).decode().splitlines()
check("new_actual_diff_exact9A", sorted(delta) == sorted(old_delta) == sorted("A\t" + name for name in expected))
check("every_prior_current_d20_tree_entry_unchanged", all(new_tree.get(name) == value for name, value in base_tree.items()))
check("tree_grows_only_by_original9", set(new_tree) - set(base_tree) == set(expected) and len(new_tree) == len(base_tree) + 9)
for name, item in blobs.items():
    check("new_saved_same_blob:" + name, new_tree[name] == old_tree[name] == (item["mode"], "blob", item["blob"])
          and sha(git("show", commit + ":" + name)) == item["sha256"])
after = protected(baseline)
shared_after = shared_hashes()
frozen_after = frozen_snapshot()
check("main_shared_index_status_and_all_user_bytes_unchanged", before == after)
check("old_FROZEN_all19_files_unchanged", frozen_before == frozen_after)
check("old_a709_and_source_review_proof_preserved",
      fsha(OLD_PROOF) == "ad7cf1fea60aa7546e7d1aed928737742f84f76970e2afda44060e2cc72c37f8"
      and fsha(OLD_REVIEW) == "a167ed2fac7bfd15a617c05e4f318634e7a3f8b7370376b271fcbb4d30cbce19"
      and git("rev-list", "--parents", "-n", "1", OLD).decode().split() == [OLD, OLD_PARENT])
check("original_NULL_proposal_not_filled", fsha(PRIVATE / "proposal.json") == proposal_hash
      and read(PRIVATE / "proposal.json")["source_commit"] is None)
check("owner_context_and_deadline_unchanged", guard() == owner)
changed_shared = [name for name in shared_before if shared_before[name] != shared_after[name]]
result = {
    "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(), "passed": True,
    "owner": owner, "actual_author_child_thread_id": CHILD, "candidate_id": CID, "experiment_id": "M231-PSC",
    "source_commit": commit, "code_commit": commit, "source_parent_commit": BASE, "parent_commit": BASE,
    "pinned_ref": REF, "tree_oid": new_tree_oid, "prior_source_commit": OLD, "prior_source_parent_commit": OLD_PARENT,
    "source_files_exact9": expected, "git_blobs_exact9": blobs, "diff_exact9A": delta,
    "same_source_bytes_as_original_reviewed_PSC": True, "model_or_protocol_revision": False,
    "python_sources_syntax_compiled_without_import": compiled,
    "prior_current_tree_entry_count": len(base_tree), "new_tree_entry_count": len(new_tree),
    "all_prior_current_d20_tree_entries_unchanged": True,
    "original_source_proof": ref(OLD_PROOF), "original_independent_source_review": ref(OLD_REVIEW),
    "original_source_manifest": ref(PRIVATE / "source_manifest.json"), "original_FROZEN": frozen_after,
    "original_NULL_proposal": ref(PRIVATE / "proposal.json"), "original_NULL_proposal_not_filled": True,
    "legitimate_HVD_ff_result_baseline": ref(FF_RESULT), "original_user20_baseline": ref(OLD_BASELINE),
    "protected_before": before, "protected_after": after,
    "alternate_index": {"path": ALT_INDEX.relative_to(ROOT).as_posix(), "sha256": fsha(ALT_INDEX)},
    "shared_project_hashes_before": shared_before, "shared_project_hashes_after": shared_after,
    "shared_project_paths_changed_during_observation": changed_shared,
    "shared_project_change_note": "No shared project file was written by this helper; concurrent root changes, if observed, are reported without attribution.",
    "checks": CHECKS, "check_count": len(CHECKS),
    "candidate_research_memory_queue_SERVERS_or_worktree_written": False,
    "native": "NOT_RUN", "resources": "NOT_RUN", "scientific_admission": False,
    "promoted_or_deployed": False, "remote_GPU_lease_stage_model_execution": False,
    "independent_review": "PENDING_EXTERNAL_PARENT_COMPATIBILITY_REVIEW",
    "scope": "Isolated parent compatibility for the existing PSC candidate only. Original nine blobs preserved on d20; no new candidate, model revision, main promotion or shared-index edit.",
}
out = HERE / "compatible_source_version.json"
with out.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
guard()
files = {p.name: fsha(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name != "FROZEN.json"}
frozen = {"schema_version": 1, "frozen_at": datetime.now(timezone.utc).isoformat(), "writer_stopped": True,
          "candidate_id": CID, "source_commit": commit, "parent_commit": BASE, "files": files,
          "native": "NOT_RUN", "resources": "NOT_RUN", "scientific_admission": False,
          "independent_review": "PENDING_EXTERNAL_PARENT_COMPATIBILITY_REVIEW"}
with (HERE / "FROZEN.json").open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(frozen, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"source_commit": commit, "parent_commit": BASE, "pinned_ref": REF,
                  "proof": ref(out), "frozen": ref(HERE / "FROZEN.json"), "check_count": len(CHECKS),
                  "main_and_shared_index_and_user_files_unchanged": before == after,
                  "shared_project_paths_changed_during_observation": changed_shared,
                  "native": "NOT_RUN", "resources": "NOT_RUN"}))
