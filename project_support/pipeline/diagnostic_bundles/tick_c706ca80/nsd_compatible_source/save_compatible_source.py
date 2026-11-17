"""Save exact reviewed NSD blobs on current PSC parent through a private index."""
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from unittest.mock import patch
import ast
import copy
import hashlib
import json
import os
import subprocess
import sys
import yaml

ROOT = Path("D:/project/cluster_project")
REPO = ROOT / "Cluster"
HERE = Path(__file__).resolve().parent
TOKEN = "c706ca805df642f3b7d41f51206ed921"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
CHILD = "01a1b166-dcbf-7d01-b0cb-c85fff644605"
PARENT = "0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"
OLD_SOURCE = "1fa7d779567b3e10119c63190d2eee16d7fda18f"
OLD_PARENT = "d20eb221eff6584b67d4e9b5673559d0e1cb735b"
OLD_TICK = ROOT / "pipeline/diagnostic_bundles/tick_2e51495f"
OLD_PACKET = OLD_TICK / "reserve_candidate"
OLD_PROOF = OLD_TICK / "nsd_isolated_source_version.json"
OLD_REVIEW = OLD_TICK / "reserve_candidate_independent_review.json"
USER_BASELINE = ROOT / "pipeline/diagnostic_bundles/tick_d20ca92f/protected_assets_before.json"
REF = "refs/codex/cluster_project/nsd-compatible-psc-c706ca80"
OWNER_KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
GIT = ["C:/Program Files (x86)/Git/cmd/git.exe", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(REPO)]
ENV = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1")
for variable in ("GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE"):
    ENV.pop(variable, None)
PRIVATE_INDEX = HERE / "nsd_compatible.index"
PRIVATE_ENV = dict(ENV, GIT_INDEX_FILE=str(PRIVATE_INDEX))
CHECKS = []


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    return digest(Path(path).read_bytes())


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return {"path": Path(path).relative_to(ROOT).as_posix(), "sha256": sha(path)}


def check(name, condition):
    assert condition, name
    CHECKS.append({"name": name, "passed": True})


def guard():
    assert HERE == ROOT / "pipeline/diagnostic_bundles/tick_c706ca80/nsd_compatible_source"
    assert os.environ.get("CODEX_THREAD_ID") == CHILD != THREAD and sys.dont_write_bytecode
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    mode = read(ROOT / "pipeline/execution_mode.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == mode["target_thread_id"] == THREAD
    assert mode["mode"] == "foreground"
    assert datetime.fromisoformat(owner["generated_at"]) <= datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
    assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
    return {key: owner[key] for key in OWNER_KEYS}


def git(*args, mutation=False, private=False, allow_missing=False):
    if mutation:
        guard()
        assert args[0] in ("read-tree", "update-index", "write-tree", "commit-tree", "update-ref")
        if args[0] == "update-ref":
            assert args[1] == REF and args[3] == "0" * 40 and not private
        else:
            assert private
    process = subprocess.run(GIT + list(args), env=PRIVATE_ENV if private else ENV,
                             capture_output=True, timeout=30)
    if allow_missing and process.returncode == 1:
        return None
    assert process.returncode == 0, process.stderr.decode("utf8", "replace")[-1000:]
    return process.stdout


def save(name, value):
    guard()
    path = HERE / name
    assert path.parent == HERE
    with path.open("x", encoding="utf8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def tree(commit):
    entries = {}
    for entry in git("ls-tree", "-r", "-z", commit).split(b"\0"):
        if entry:
            header, path = entry.split(b"\t", 1)
            mode, kind, oid = header.decode().split()
            entries[path.decode()] = {"mode": mode, "type": kind, "oid": oid}
    return entries


def protected_snapshot(user_paths, index):
    return {
        "HEAD": git("rev-parse", "HEAD").decode().strip(),
        "branch": git("symbolic-ref", "HEAD").decode().strip(),
        "index": sha(index),
        "status_hex": git("status", "--porcelain=v1", "--untracked-files=all", "-z").hex(),
        "user28": {path: sha(REPO / path) for path in user_paths},
        "cached_paths": git("diff", "--cached", "--name-only", "-z").hex(),
    }


def combined_import_check(source_blobs, parent_tree):
    """Import real graph definitions with explicit dependency stubs, no tensors."""
    class ModuleOnly:
        pass
    torch = ModuleType("torch")
    nn = ModuleType("torch.nn")
    nn.Module = ModuleOnly
    functional = ModuleType("torch.nn.functional")
    nn.functional = functional
    torch.nn = nn
    pointnet = ModuleType("pointnet2")
    pointnet.__path__ = []
    pointnet_utils = ModuleType("pointnet2.pointnet2_utils")
    def forbidden(*args, **kwargs):
        raise AssertionError("Tensor/model operation is forbidden in a definition import check")
    pointnet_utils.FurthestPointSampling = forbidden
    scatter = ModuleType("torch_scatter")
    scatter.scatter_mean = scatter.scatter_max = forbidden
    modules = {"torch": torch, "torch.nn": nn, "torch.nn.functional": functional,
               "pointnet2": pointnet, "pointnet2.pointnet2_utils": pointnet_utils, "torch_scatter": scatter}
    for name in ("framework", "framework.model", "framework.model.Quard_model"):
        module = ModuleType(name)
        module.__path__ = []
        modules[name] = module
    base = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
    loaded = {}
    with patch.dict(sys.modules, modules):
        for suffix, core_name in (("psc", "position_scatter"), ("nsd", "spatial_dirichlet")):
            package = "framework.model.Quard_model." + base + "_" + suffix
            package_module = ModuleType(package)
            package_module.__path__ = []
            sys.modules[package] = package_module
            for filename in (core_name + ".py", "hier_postprocess.py"):
                path = "framework/model/Quard_model/" + base + "_" + suffix + "/" + filename
                raw = source_blobs[path] if suffix == "nsd" else git("show", PARENT + ":" + path)
                check("combined_tree_real_source_file_exists:" + suffix + ":" + filename,
                      path in parent_tree if suffix == "psc" else path in source_blobs)
                name = package + "." + filename[:-3]
                module = ModuleType(name)
                module.__package__ = package
                module.__file__ = PARENT + ":" + path
                sys.modules[name] = module
                exec(compile(raw, module.__file__, "exec"), module.__dict__)
                loaded[suffix, filename] = module
            graph = loaded[suffix, "hier_postprocess.py"]
            raw = source_blobs[path] if suffix == "nsd" else git("show", PARENT + ":" + path)
            imported = next(node for node in ast.parse(raw).body if isinstance(node, ast.ImportFrom) and node.module == core_name)
            for item in imported.names:
                check("actual_relative_core_import_resolves_without_collision:" + suffix + ":" + item.name,
                      getattr(graph, item.asname or item.name) is getattr(loaded[suffix, core_name + ".py"], item.name))
        check("PSC_and_NSD_graph_classes_independent_namespaces",
              loaded["psc", "hier_postprocess.py"].C2F_ClusterAttn_CTF_HCG_CSORT is not
              loaded["nsd", "hier_postprocess.py"].C2F_ClusterAttn_CTF_HCG_CSORT)
    return {
        "actual_imported_definition_modules": [module.__name__ for module in loaded.values()],
        "dependency_stubs": sorted(modules), "real_Torch_imported": False, "tensor_or_model_execution": False,
        "scope": "Actual complete core/graph module definitions imported together with explicit dependency stubs; not full native network import, forward, autograd or CUDA.",
    }


def main():
    owner = guard()
    assert not (HERE / "compatible_source_version.json").exists() and not PRIVATE_INDEX.exists()
    old_proof, old_review = read(OLD_PROOF), read(OLD_REVIEW)
    check("exact_original_review_SHA", sha(OLD_REVIEW) == "74ae877c702fef9891acdfd4e1268a2aa31926326e1e305881ad1c19e80a2f97")
    check("original_independent_source_algebra_review_passed", old_review["passed"] is True)
    check("original_CPU41_evidence_hash_and_pass",
          sha(OLD_PACKET / "static_validation.json") == "19af1de18c72effb8bd9b7c6ae7e5d37502cb6d098b29bd8bbaa02d6719f4cb1"
          and read(OLD_PACKET / "static_validation.json")["checks_passed"] == 41
          and read(OLD_PACKET / "static_validation.json")["passed"] is True)
    check("original_independent200_cases_reused_not_rerun", any(item.get("cases") == 200 for item in old_review["checks"]))
    check("exact_old_source_parent", old_proof["source_commit"] == OLD_SOURCE and old_proof["parent_commit"] == OLD_PARENT
          and git("rev-parse", OLD_SOURCE + "^").decode().strip() == OLD_PARENT)
    paths = old_proof["source_files_exact9"]
    check("exact9_reviewed_source_map", len(paths) == 9 and paths == old_review["source_files_exact9"])
    source_blobs, blob_ids = {}, {}
    for path, expected in paths.items():
        raw = git("show", OLD_SOURCE + ":" + path)
        blob_ids[path] = git("rev-parse", OLD_SOURCE + ":" + path).decode().strip()
        source_blobs[path] = raw
        check("old_blob_exact_original_frozen_bytes:" + path,
              digest(raw) == expected == sha(OLD_PACKET / "source" / path))
        if path.endswith(".py"):
            compile(raw, OLD_SOURCE + ":" + path, "exec")
    user_baseline = read(USER_BASELINE)
    user_paths = list(user_baseline["files"])
    check("exact28_protected_user_paths", len(user_paths) == 28)
    index = Path(git("rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = REPO / index
    before = protected_snapshot(user_paths, index)
    check("current_primary_exact_PSC_parent_and_empty_cached_paths", before["HEAD"] == PARENT and not before["cached_paths"])
    check("user28_bytes_still_equal_root_preserved_baseline", before["user28"] == user_baseline["files"])
    parent_tree = tree(PARENT)
    check("all_nine_NSD_paths_absent_from_PSC_parent", not set(paths) & set(parent_tree))
    imports = combined_import_check(source_blobs, parent_tree)
    nsd_config_path = next(path for path in paths if path.endswith(".yaml"))
    psc_config_path = nsd_config_path.replace("_nsd", "_psc")
    psc_yaml = git("show", PARENT + ":" + psc_config_path)
    nsd_yaml = source_blobs[nsd_config_path]
    check("independent_NSD_and_PSC_native_YAML_exact_same_bytes", nsd_yaml == psc_yaml)
    config = yaml.safe_load(nsd_yaml)
    check("fixed_original_seed_data_schedule_optimizer_unchanged",
          config == yaml.safe_load(psc_yaml) and config["train"]["seed"] == 1999
          and config["train"]["epochs"] == 50 and config["lr_scheduler"]["max_iters"] == 70
          and config["dataloader"]["train"]["batch_size"] == 2
          and config["dataloader"]["train"]["num_workers"] == 4
          and config["dataloader"]["train"]["persistent_workers"] is True
          and config["optimizer"]["type"] == "AdamW")
    check("fresh_private_ref_absent", git("show-ref", "--verify", "--quiet", REF, allow_missing=True) is None)
    git("read-tree", PARENT, mutation=True, private=True)
    for path in sorted(paths):
        git("update-index", "--add", "--cacheinfo", "100644," + blob_ids[path] + "," + path, mutation=True, private=True)
    new_tree_oid = git("write-tree", mutation=True, private=True).decode().strip()
    new_commit = git("commit-tree", new_tree_oid, "-p", PARENT, "-m",
                     "Preserve reviewed NSD exact9 source on current PSC parent; no model or protocol revision",
                     mutation=True, private=True).decode().strip()
    check("new_commit_parent_exact_current_PSC", git("rev-parse", new_commit + "^").decode().strip() == PARENT)
    combined_tree = tree(new_commit)
    check("all_prior_PSC_tree_entries_byte_exact_unchanged",
          all(combined_tree.get(path) == entry for path, entry in parent_tree.items()))
    check("new_tree_has_exactly_nine_additions", set(combined_tree) - set(parent_tree) == set(paths)
          and len(combined_tree) == len(parent_tree) + 9)
    changes = [item.decode() for item in git("diff-tree", "--no-commit-id", "--name-status", "-r", "-z", new_commit).split(b"\0") if item]
    check("git_diff_exact9_added_paths", changes[::2] == ["A"] * 9 and sorted(changes[1::2]) == sorted(paths))
    for path, expected in paths.items():
        check("saved_commit_exact_source_blob:" + path,
              combined_tree[path]["oid"] == blob_ids[path]
              and digest(git("show", new_commit + ":" + path)) == expected)
    git("update-ref", REF, new_commit, "0" * 40, mutation=True)
    check("new_commit_durably_accessible_via_fresh_ref", git("rev-parse", REF).decode().strip() == new_commit)
    after = protected_snapshot(user_paths, index)
    check("primary_HEAD_branch_index_status_cached_and_user28_all_unchanged", before == after)
    check("original_source_proof_and_review_unmodified",
          sha(OLD_REVIEW) == "74ae877c702fef9891acdfd4e1268a2aa31926326e1e305881ad1c19e80a2f97"
          and read(OLD_PROOF) == old_proof)
    guard()
    result = {
        "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(), "passed": True,
        "owner": owner, "actual_author_child_thread_id": CHILD,
        "candidate_id": old_proof["candidate_id"], "experiment_id": "M232-NSD",
        "source_commit": new_commit, "code_commit": new_commit, "parent_commit": PARENT,
        "source_parent_commit": PARENT, "prior_source_commit": OLD_SOURCE, "prior_source_parent_commit": OLD_PARENT,
        "pinned_ref": REF, "tree_oid": new_tree_oid, "source_files_exact9": paths,
        "git_blobs_exact9": blob_ids, "diff_exact9A": sorted(paths),
        "prior_current_PSC_tree_entry_count": len(parent_tree), "new_tree_entry_count": len(combined_tree),
        "all_prior_current_PSC_tree_entries_unchanged": True, "same_source_bytes_as_reviewed_NSD": True,
        "model_or_YAML_or_protocol_revision": False,
        "original_source_proof": ref(OLD_PROOF), "original_independent_review": ref(OLD_REVIEW),
        "original_CPU41_validation": ref(OLD_PACKET / "static_validation.json"),
        "original_source_FROZEN": ref(OLD_PACKET / "FROZEN.json"),
        "prior_CPU41_and_independent200_reused_not_rerun": True,
        "actual_new_combined_definition_import_check": imports,
        "actual_new_configuration_compatibility": "Independent native NSD YAML byte-identical to current PSC YAML; original seed/data/optimizer/schedule retained.",
        "protected_before": before, "protected_after": after, "private_index": ref(PRIVATE_INDEX),
        "checks": CHECKS, "check_count": len(CHECKS), "independent_review": "PENDING_EXTERNAL",
        "native": "NOT_RUN", "resources": "NOT_RUN", "Torch_autograd": "NOT_RUN",
        "scientific_admission": False, "promoted_or_deployed": False,
        "main_worktree_index_or_existing_refs_changed": False,
        "only_new_ref_written": REF, "SSH_GPU_model_execution": False,
        "scope": "New compatible source Git object and fresh pin only; original code and protocol unchanged. Not a model variant, native execution, resource PASS or efficacy evidence.",
    }
    save("compatible_source_version.json", result)
    save("source_manifest.json", {"source_commit": new_commit, "parent_commit": PARENT,
         "source_files_exact9": paths, "git_blobs_exact9": blob_ids, "pinned_ref": REF,
         "source_model_YAML_protocol_unchanged": True})
    print(json.dumps({"source_commit": new_commit, "parent_commit": PARENT, "pinned_ref": REF,
                      "check_count": len(CHECKS), "proof": ref(HERE / "compatible_source_version.json"),
                      "primary_HEAD_index_user28_status_unchanged": True,
                      "native": "NOT_RUN", "resources": "NOT_RUN"}))


if __name__ == "__main__":
    main()
