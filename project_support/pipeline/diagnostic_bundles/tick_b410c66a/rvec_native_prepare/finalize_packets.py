"""Default NOP. Freeze own new preparation packets after genuine r1 source save."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
CPU = TICK / "rvec_constructor_cpu_prepare"
SOURCE = TICK / "rvec_r1_source_prepare"
OLD = ROOT / "pipeline/diagnostic_bundles/tick_915589b3/rvec_native_prepare_v2"
R0 = "0f8cc0f978b38c24e159d3a2d37344f59cc9a0be"
RUNTIME = "0747f6acec1c61018ec99acf2efa5329c9b3523c"
GIT = "C:/Program Files (x86)/Git/cmd/git.exe"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8", newline="\n")


def anchor(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    if not args.finalize:
        print(json.dumps({"status": "DEFAULT_NOP_NO_GIT_TORCH_SSH_GPU_OR_MUTATION"}))
        return
    assert sys.dont_write_bytecode
    assert not (HERE / "FROZEN.json").exists() and not (CPU / "FROZEN.json").exists()
    prereg = TICK / "rve_r1_preregistration.json"
    owner = read(prereg)["owner"]
    actual_owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {key: actual_owner[key] for key in owner} == owner
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    proof_path = SOURCE / "source_version.json"
    proof = read(proof_path)
    source_frozen = read(SOURCE / "FROZEN.json")
    assert sha(SOURCE / "FROZEN.json") == "155e9d7f4689c54a4a25278b93727017a03fe7a4597796729fdb7fe4f4b1ef76"
    assert proof["owner"] == owner and proof["source_parent_commit"] == R0
    assert proof["runtime_original_parent_commit"] == RUNTIME
    assert proof["FROZEN_sha256"] == sha(SOURCE / "FROZEN.json")
    assert proof["source_files_exact9"] == source_frozen["source_files_exact9"]
    assert proof["retained_ref"] == "refs/pipeline/candidates/M234-RVE-r1"
    assert re.fullmatch(r"[0-9a-f]{40}", proof["source_commit"])
    assert proof["source_commit"] not in (R0, RUNTIME)
    assert proof["r0_to_r1_diff_exactly_one_hierarchy_modification"] is True
    assert proof["main_HEAD_unchanged"] is True and proof["actual_index_bytes_unchanged"] is True
    review_path = Path(proof["independent_review"]["path"])
    assert review_path.resolve().is_relative_to(ROOT.resolve())
    assert sha(review_path) == proof["independent_review"]["sha256"]
    review = read(review_path)
    assert review["passed"] is True and review["owner"] == owner and review["material_concerns"] == []
    assert review["reviewer_thread_id"] not in (owner["thread_id"], "/root", "/root/fresh_ops", "/root/actual_chain_fast")
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")

    def git(*args):
        return subprocess.check_output([GIT, "--no-optional-locks", "-c", "core.fsmonitor=false",
                                        "-C", str(ROOT / "Cluster"), *args], env=env, timeout=20)

    assert git("rev-parse", proof["retained_ref"]).decode().strip() == proof["source_commit"]
    assert git("rev-list", "--parents", "-n", "1", proof["source_commit"]).decode().strip() == proof["source_commit"] + " " + R0
    assert git("rev-parse", "HEAD").decode().strip() == RUNTIME
    files = proof["source_files_exact9"]
    for relative, expected in files.items():
        assert sha(SOURCE / "source" / relative) == expected
        assert hashlib.sha256(git("cat-file", "blob", proof["source_commit"] + ":" + relative)).hexdigest() == expected
        staged = HERE / ("candidate.yaml" if relative.endswith(".yaml") else "candidate_model/" + Path(relative).name)
        assert sha(staged) == expected
    commit = proof["source_commit"]
    version_hash = sha(proof_path)
    model_hashes = {Path(path).name: expected for path, expected in files.items() if path.endswith(".py")}
    config_hash = next(expected for path, expected in files.items() if path.endswith(".yaml"))
    native_binding = {
        "schema_version": 1, "owner": owner, "candidate_id": "fine-leaf-receiver-conditioned-vector-exchange",
        "experiment_id": "M234-RVE", "implementation_revision": 1, "source_parent_commit": R0,
        "runtime_original_parent_commit": RUNTIME, "source_commit": commit, "source_files": files,
        "candidate_source_hashes": model_hashes, "candidate_config_sha256": config_hash,
        "source_version_proof": proof, "source_version_sha256": version_hash}
    save(HERE / "source_binding.template.json", native_binding)
    manifest = read(HERE / "manifest_template.json")
    manifest.update(code_commit=commit, owner=owner, candidate_source_hashes=model_hashes,
                    candidate_config_sha256=config_hash,
                    environment_binding_sha256=sha(HERE / "environment_binding.json"))
    for name in manifest["diagnostic_files"]:
        manifest["diagnostic_files"][name] = sha(HERE / name)
    save(HERE / "manifest_template.json", manifest)
    for name in ("independent_review_contract.json", "execution_release_contract.json"):
        contract = read(HERE / name)
        contract.update(source_commit=commit, source_version_sha256=version_hash,
                        source_parent_commit=R0, runtime_original_parent_commit=RUNTIME,
                        environment_binding_sha256=sha(HERE / "environment_binding.json"))
        if name == "independent_review_contract.json":
            contract.update(FROZEN_sha256="ACTUAL_FINAL_R1_FROZEN_SHA256",
                            worker_sha256=sha(HERE / "worker.py"), runtime_sha256=sha(HERE / "native_runtime.py"),
                            transport_sha256=sha(HERE / "run_native_once.py"))
        else:
            contract["minimal_harness_delta"] = "Exact accepted v2 worker; fresh owner/stage/source lineage bindings; candidate r1 single fork_rng constructor guard only"
        save(HERE / name, contract)
    model = "framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rvec"
    r0_root = ROOT / "pipeline/diagnostic_bundles/tick_10a3f8b7/rvec_prepare/source"
    paths = {
        "r0_hierarchy": (r0_root / model / "hier_postprocess.py").relative_to(ROOT).as_posix(),
        "r1_hierarchy": (SOURCE / "source" / model / "hier_postprocess.py").relative_to(ROOT).as_posix(),
        "operator": (SOURCE / "source" / model / "receiver_vector_exchange.py").relative_to(ROOT).as_posix()}
    cpu_binding = {
        "schema_version": 1, "owner": owner, "candidate_id": native_binding["candidate_id"],
        "experiment_id": "M234-RVE", "implementation_revision": 1, "source_parent_commit": R0,
        "runtime_original_parent_commit": RUNTIME, "source_commit": commit, "source_files_exact9": files,
        "r1_source_root": (SOURCE / "source").relative_to(ROOT).as_posix(),
        "source_version_proof": proof, "source_version_sha256": version_hash,
        "probe_source_paths": paths, "probe_source_hashes": {name: sha(ROOT / path) for name, path in paths.items()}}
    assert cpu_binding["probe_source_hashes"]["r0_hierarchy"] == "dcee33e0f3e6b5cd4118ce8a06e008995b07e35d37ed29b28d813be4231318be"
    assert cpu_binding["probe_source_hashes"]["r1_hierarchy"] == "2de9a6bf654b65e10a80dab112da70abeb94d44ee321584fd0902eee1f0280ee"
    assert cpu_binding["probe_source_hashes"]["operator"] == "3b2ed3dc9f99d62a0a9108d3154792752e06a85a8c493b47317be9ec264099d3"
    save(CPU / "source_binding.json", cpu_binding)
    contract = read(CPU / "independent_review_contract.json")
    contract.update(source_binding_sha256=sha(CPU / "source_binding.json"), source_version_sha256=version_hash)
    save(CPU / "independent_review_contract.json", contract)
    common_anchors = {
        "source_version": anchor(proof_path), "source_frozen": anchor(SOURCE / "FROZEN.json"),
        "source_save_independent_review": anchor(review_path), "preregistration": anchor(prereg),
        "native_reconciliation": anchor(TICK / "stage_release_rvec_915589b3b_gpu0.json"),
        "immutable_conda_base": anchor(ROOT / "pipeline/runtime/server4_conda_4ca73fba.sh"),
        "goal": anchor(ROOT / "pipeline/goal.json")}
    previous = read(OLD / "FROZEN.json")
    native_anchors = dict(common_anchors)
    for key in ("environment_actual", "environment_actual_review", "resource_authorization"):
        native_anchors[key] = previous["anchors"][key]
    native_anchors["historical_r0_source_frozen"] = previous["anchors"]["source_frozen"]
    for directory in (HERE, CPU):
        validation = read(directory / "software_validation.json")
        validation.update(source_commit_proof="GENUINE_RETAINED_R1_PROOF_AND_ACTUAL_GIT_BLOBS_VERIFIED",
                          source_version_sha256=version_hash, source_commit=commit)
        save(directory / "software_validation.json", validation)
        save(directory / "PREPARATION_STATUS.json", {
            "owner": owner, "producer_agent": "/root/fresh_ops", "source_commit": commit,
            "source_version_sha256": version_hash, "status": "FROZEN_PENDING_GENUINE_INDEPENDENT_PACKET_REVIEW",
            "author_Torch_SSH_GPU": "NOT_RUN", "scientific_admission": False})
        frozen = {
            "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
            "owner": owner, "producer_agent": "/root/fresh_ops", "candidate_id": native_binding["candidate_id"],
            "experiment_id": "M234-RVE", "implementation_revision": 1,
            "status": "FROZEN_PENDING_GENUINE_INDEPENDENT_PACKET_REVIEW",
            "source_commit": commit, "source_parent_commit": R0, "runtime_HEAD": RUNTIME,
            "runtime_original_parent_commit": RUNTIME, "source_version_sha256": version_hash,
            "source_files_exact9": files, "anchors": native_anchors if directory == HERE else common_anchors,
            "files": {path.relative_to(directory).as_posix(): sha(path)
                      for path in sorted(directory.rglob("*")) if path.is_file() and path.name != "FROZEN.json"},
            "Torch_SSH_GPU": "NOT_RUN_BY_AUTHOR", "independent_review": "PENDING_NOT_SELF_APPROVED",
            "scientific_admission": False, "efficacy": "UNKNOWN", "novelty": "UNKNOWN"}
        if directory == HERE:
            frozen.update(worker_sha256=sha(HERE / "worker.py"), runtime_sha256=sha(HERE / "native_runtime.py"),
                          transport_sha256=sha(HERE / "run_native_once.py"),
                          environment_binding_sha256=sha(HERE / "environment_binding.json"),
                          remote_stage=manifest["stage"], execution_directory="rvec_native_execution",
                          accepted_v2_worker_byte_exact=sha(HERE / "worker.py") == previous["worker_sha256"],
                          original_locks=previous["original_locks"],
                          parent_packet={"path": OLD.relative_to(ROOT).as_posix(), "FROZEN_sha256": sha(OLD / "FROZEN.json"),
                                         "historical_owner_preserved": True})
        else:
            frozen.update(producer_sha256=sha(CPU / "constructor_probe.py"),
                          transport_sha256=sha(CPU / "run_constructor_once.py"),
                          source_binding_sha256=sha(CPU / "source_binding.json"),
                          execution_directory="rvec_constructor_cpu_execution", CPU8_repeated=False,
                          actual_constructor_test="PENDING_ROOT_EXECUTION")
        save(directory / "FROZEN.json", frozen)
    print(json.dumps({
        "native_FROZEN_sha256": sha(HERE / "FROZEN.json"), "native_worker_sha256": sha(HERE / "worker.py"),
        "native_runtime_sha256": sha(HERE / "native_runtime.py"),
        "native_transport_sha256": sha(HERE / "run_native_once.py"),
        "constructor_FROZEN_sha256": sha(CPU / "FROZEN.json"),
        "constructor_producer_sha256": sha(CPU / "constructor_probe.py"),
        "constructor_transport_sha256": sha(CPU / "run_constructor_once.py"),
        "constructor_source_binding_sha256": sha(CPU / "source_binding.json"),
        "source_commit": commit, "source_version_sha256": version_hash,
        "Torch_SSH_GPU": "NOT_RUN_BY_AUTHOR"}))


if __name__ == "__main__":
    main()
