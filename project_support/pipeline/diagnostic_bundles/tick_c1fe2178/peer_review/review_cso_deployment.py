"""Independent local-only CSO sync review; final review needs a real receipt."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
TICK = ROOT / "pipeline/diagnostic_bundles/tick_c1fe2178"
HERE = Path(__file__).resolve().parent
PACKET = TICK / "cso_deployment_prepare"
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
REVIEWER = "/root/cso_sync_peer"
EXPECTED = {
    "FROZEN.json": "decba0269bf95dfdd654a0973141e08f2173e5faccceb7239aa7474b1b0355ce",
    "deploy_cso_once.py": "05025ae0af8e2ea6a8a3e36d5e775ccda9d8ce9138b84ec84fbef9509d2defa6",
    "baseline.json": "a1eaa3b44245cfcc8aabc8ac67ae55165ea4b136c06bee392d1a064382998064",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def source_checks():
    assert sys.dont_write_bytecode and not sys.flags.optimize
    assert os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"
    os.environ["GIT_OPTIONAL_LOCKS"] = "0"
    owner = read(TICK / "current_owner_binding.json")
    assert len(owner) == 6
    for name, expected in EXPECTED.items():
        assert sha(PACKET / name) == expected, name
    frozen = read(PACKET / "FROZEN.json")
    baseline = read(PACKET / "baseline.json")
    before = read(TICK / "integrity_before.json")
    assert frozen["author_thread_id"] == "/root/cso_readiness"
    assert frozen["owner"] == baseline["owner"] == before["owner"] == owner
    for name, expected in frozen["files"].items():
        assert sha(PACKET / name) == expected, name
    for name, item in frozen["anchors"].items():
        assert sha(item["path"]) == item["sha256"], name
    assert baseline["real_index_sha256"] == before["index_sha256"]
    assert baseline["SERVERS_sha256"] == before["servers_sha256"]
    assert len(baseline["dirty_files_exact28"]) == 28
    assert len(baseline["working_tree_r0_files_exact9"]) == 9
    assert {**baseline["dirty_files_exact28"], **baseline["working_tree_r0_files_exact9"]} == before["dirty_sha256"]
    source = (PACKET / "deploy_cso_once.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    old_path = ROOT / "pipeline/diagnostic_bundles/tick_6b23467a/m235_deployment_prepare/deploy_m235_once.py"
    old_source = old_path.read_text(encoding="utf-8")
    old_tree = ast.parse(old_source)
    functions = {n.name: ast.get_source_segment(source, n) for n in tree.body if isinstance(n, ast.FunctionDef)}
    old_functions = {n.name: ast.dump(n, include_attributes=False) for n in old_tree.body if isinstance(n, ast.FunctionDef)}
    new_functions = {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.FunctionDef)}
    for name in ("sha", "read", "save", "lifecycle", "protected"):
        assert new_functions[name] == old_functions[name], name
    assert "closure.admission(ROOT, task)" in functions["guard"]
    assert "current_native_gate_binding(receipt)" in functions["guard"]
    assert "not sys.flags.optimize" in functions["guard"]
    assert "scoped_safe_sync(closure, server, strict_ssh)" in functions["main"]
    assert "return closure.safe_sync(ROOT, DETACHED, server, strict_ssh)" in functions["scoped_safe_sync"]
    canonical = (SKILL / "closure.py").read_text(encoding="utf-8")
    canonical_tree = ast.parse(canonical)
    safe_sync = next(ast.get_source_segment(canonical, n) for n in canonical_tree.body if isinstance(n, ast.FunctionDef) and n.name == "safe_sync")
    assert "merge --ff-only" in safe_sync
    assert safe_sync.count("source_integrity.verify_git(") == 2
    assert "merge.autoStash=false" in safe_sync
    spec = importlib.util.spec_from_file_location("independently_reviewed_cso_sync", PACKET / "deploy_cso_once.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.OWNER == owner
    assert module.SOURCE == "5413102c57b526035f3920b5e7a81f3b58ad764d"
    assert module.PARENT == "b1e639b3ceb14bb5c65d9f81a084d41c834b951c"
    old_remote = next(n.value.value for n in old_tree.body if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id == "REMOTE_OBSERVE" for x in n.targets))
    assert old_remote == module.REMOTE_OBSERVE
    module.protected()
    module.verify_checkout()
    proof = read(PACKET / "existing_checkout_proof.json")
    assert proof["owner"] == owner and proof["existing_checkout_reused"] is True
    assert proof["new_checkout_performed"] is False
    assert proof["files_exact9"] == baseline["source_files_exact9"]
    exact9 = baseline["source_files_exact9"]
    for commit, parent in ((module.SOURCE, module.PARENT), ("af45707d7b6089f764843337c5f88af285383f88", "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e")):
        assert module.git(module.MAIN, "rev-list", "--parents", "-n", "1", commit).decode().strip() == commit + " " + parent
        changed = module.git(module.MAIN, "diff-tree", "--no-commit-id", "--name-status", "-r", commit).decode().splitlines()
        assert len(changed) == 9 and {line[2:] for line in changed if line.startswith("A\t")} == set(exact9)
        for relative, expected in exact9.items():
            assert hashlib.sha256(module.git(module.MAIN, "cat-file", "blob", commit + ":" + relative)).hexdigest() == expected
    # Exercise only the process-local environment adapter with a local stub.
    selected = ("GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0")
    previous = {name: os.environ.get(name) for name in selected}
    class LocalStub:
        @staticmethod
        def safe_sync(project, code, server, ssh):
            assert project == ROOT and code == module.DETACHED
            count = int(os.environ["GIT_CONFIG_COUNT"])
            assert os.environ["GIT_CONFIG_KEY_" + str(count - 1)] == "safe.directory"
            assert os.environ["GIT_CONFIG_VALUE_" + str(count - 1)] == module.DETACHED.resolve().as_posix()
            return True
    assert module.scoped_safe_sync(LocalStub, {}, None) is True
    assert {name: os.environ.get(name) for name in selected} == previous
    nop = subprocess.run([sys.executable, "-X", "utf8", "-B", str(PACKET / "deploy_cso_once.py")], capture_output=True, text=True, check=True)
    assert json.loads(nop.stdout)["status"] == "DEFAULT_NOP_NO_GIT_MUTATION_SSH_TORCH_GPU_OR_STATE_WRITE"
    return owner, module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admission")
    parser.add_argument("--admission-sha256")
    args = parser.parse_args()
    assert bool(args.admission) == bool(args.admission_sha256)
    owner, module = source_checks()
    final = bool(args.admission)
    bindings = {}
    if final:
        path = Path(args.admission).resolve()
        assert path == (ROOT / "pipeline/admissions/M236-CSO.json").resolve()
        assert sha(path) == args.admission_sha256
        receipt = read(path)
        assert receipt["id"] == "M236-CSO" and receipt["code_commit"] == module.SOURCE
        assert receipt["candidate_id"] == "fine-leaf-full-covariance-shape-composition"
        assert receipt["config"] == module.CONFIG and receipt["profile"] == "experiment_first"
        module.current_native_gate_binding(receipt)
        sys.path.insert(0, str(SKILL))
        import closure
        canonical_receipt = closure.admission(ROOT, {"id": receipt["id"], "candidate_id": receipt["candidate_id"], "config": module.CONFIG,
            "code_commit": module.SOURCE, "profile": "experiment_first", "admission_receipt": path.relative_to(ROOT).as_posix(), "requires_exclusive_ownership": False})
        assert canonical_receipt == receipt
        for field in ("version_association", "native_smoke", "version_association_review"):
            item = receipt[field]
            assert sha(ROOT / item["path"]) == item["sha256"]
            bindings[field] = item
        bindings["admission"] = {"path": str(path), "sha256": sha(path)}
    review = {
        "owner": owner, "reviewer_thread_id": REVIEWER,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "kind": "INDEPENDENT_CANONICAL_CSO_SYNC_REVIEW" if final else "CSO_SYNC_SOURCE_ONLY_REVIEW_NOT_AUTHORIZED_TO_EXECUTE",
        "status": "REVIEWED_WITH_REAL_ADMISSION_NOT_EXECUTED" if final else "SOURCE_ONLY_NOT_AUTHORIZED_TO_EXECUTE",
        "passed": final, "material_concerns": [],
        "FROZEN_sha256": EXPECTED["FROZEN.json"], "helper_sha256": EXPECTED["deploy_cso_once.py"],
        "baseline_sha256": EXPECTED["baseline.json"], "source_commit": module.SOURCE,
        "admission_sha256": args.admission_sha256,
        "source_review_passed": True, "canonical_sync_review_passed": True,
        "canonical_admission_accepted": final, "real_current_gate_and_version_binding_reviewed": final,
        "bindings": bindings,
        "verified": {
            "freeze_and_all_files_anchors_match": True, "protected_main_HEAD_index_entries_porcelain_exact37": True,
            "existing_clean_detached_checkout_and_two_commits_exact_nine_added_blobs_equal": True,
            "canonical_admission_and_unchanged_safe_sync_ff_only_source_integrity_before_after": True,
            "original_three_locks_device66308_inodes92537152_92537153_92537154": True,
            "strict_known_key_no_password_host_dl04_uid1001": True,
            "base_conda_4ca73fba_pinned_consumed_SERVERS_rvec_entry_unused": True,
            "lifecycle_protected_no_training_no_signal_no_replay": True,
            "process_local_exact_worktree_trust_and_environment_restoration": True,
            "default_NOP_observed": True,
        },
        "review_scope": "Local source, hashes and read-only Git evidence; real receipt and native/version gates also validated." if final else "Local source, hashes and read-only Git evidence only; genuine admission and derived version evidence still required before a final executable review.",
        "SSH_performed_by_reviewer": False, "Torch_imported_by_reviewer": False, "GPU_use_by_reviewer": False,
        "sync_executed_by_reviewer": False, "shared_ledger_queue_SERVERS_source_modified_by_reviewer": False,
    }
    module.protected()
    module.verify_checkout()
    for name, expected in EXPECTED.items():
        assert sha(PACKET / name) == expected
    target = HERE / ("cso_deployment_independent_review.json" if final else "cso_deployment_source_only_independent_review.json")
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(review, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"path": str(target), "sha256": sha(target), "passed": final, "admission_sha256": args.admission_sha256}))


if __name__ == "__main__":
    main()
