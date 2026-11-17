"""Local fresh packet guards; importing definitions performs no external action."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
SOURCE = "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
RUNTIME = "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
CONFIG = "configs/Quard/ctf_hcg_csort_rvec/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rvec.yaml"
PRODUCER = "/data/songcl/Project/Cluster_project/pipeline/runtime/rvec_path_prepare_558ef1ee"
PRODUCTION = "/data/songcl/Project/Cluster_project/pipeline/runtime/rvec_path_prod_558ef1ee"
OWNER = {
    "token": "558ef1ee132543f98d6897c98aff9dc9",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-09T05:05:14.672419+00:00",
    "deadline_at": "2026-11-09T06:05:14.672419+00:00",
    "context_sha256": "86e154fd6ee7f16a513f80dbe7ed7ef92c289a82ca7c0816b5418afffbe85373",
    "pending_sha256": "ce36edc3c5ca9f8b9fc76d34daaedf09a5c8d46a36200bf270e9c1c23df7d129"
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def guard(args, *, pointer=False, minimum=180):
    assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    assert os.environ.get("CODEX_THREAD_ID") == OWNER["thread_id"]
    actual = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {key: actual[key] for key in OWNER} == OWNER
    assert (datetime.fromisoformat(OWNER["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > minimum
    mode = read(ROOT / "pipeline/execution_mode.json")
    assert mode["mode"] == "foreground" and mode["target_thread_id"] == OWNER["thread_id"]
    for name, field in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == OWNER[field]
    frozen = read(HERE / "FROZEN.json")
    assert frozen["owner"] == OWNER and frozen["source_commit"] == SOURCE
    assert all(sha(HERE / name) == expected for name, expected in frozen["files"].items())
    for anchor in frozen["anchors"].values():
        assert sha(anchor["path"]) == anchor["sha256"]
    deployment = TICK / "rvec_deployment_execution/sync_result.json"
    assert sha(deployment) == args.deployment_result_sha256
    proof = read(deployment)
    assert proof["owner"] == OWNER and proof["passed"] is True and proof["source_commit"] == SOURCE
    assert proof["runtime_root"] == RUNTIME and proof["runtime_code_commit"] == SOURCE
    assert proof["source_verified"] is True and proof["source_integrity_before_after"] is True
    assert proof["main_index_user28_r0nine_preserved"] is True and proof["lifecycle_unchanged"] is True
    assert proof["training_started"] is False and proof["GPU_compute"] is False
    from source_resolver import verify
    verify()
    import yaml
    baseline = read(HERE / "baseline.json")
    raw = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))
    expected = baseline["SERVERS_parsed"]
    if pointer:
        import copy
        expected = copy.deepcopy(expected)
        expected["servers"]["server-4"]["conda_source"] = PRODUCTION + "/conda_source.sh"
    assert raw == expected
    if not pointer:
        assert sha(ROOT / "SERVERS.yaml") == baseline["SERVERS_sha256"]
    server = raw["servers"]["server-4"]
    assert server["remote_code_root"] == RUNTIME and server["host"] == "192.168.1.115"
    assert server["user"] == "songcl" and server["expected_hostname"] == "dl04-MS-7E06"
    assert server["allowed_gpus"] == [0] and server["max_tasks_per_gpu"] == 1
    assert server["allow_external_overlay"] is True and server["task_memory_mb"] == 20000
    receipt_path = Path(args.admission).resolve()
    assert receipt_path.is_relative_to(ROOT.resolve()) and sha(receipt_path) == args.admission_sha256
    receipt = read(receipt_path)
    assert receipt["id"] == "M234-RVE" and receipt["code_commit"] == SOURCE and receipt["config"] == CONFIG
    assert receipt["candidate_id"] == "fine-leaf-receiver-conditioned-vector-exchange"
    assert receipt["profile"] == "experiment_first" and receipt["implementation_revision_sha256"]
    task = {"id": "M234-RVE", "candidate_id": receipt["candidate_id"], "config": CONFIG,
            "code_commit": SOURCE, "profile": "experiment_first",
            "admission_receipt": receipt_path.relative_to(ROOT).as_posix(),
            "requires_exclusive_ownership": False}
    sys.path.insert(0, str(SKILL))
    import closure
    closure.admission(ROOT, task)
    peer_path = Path(args.review).resolve()
    assert peer_path.is_relative_to(ROOT.resolve()) and sha(peer_path) == args.review_sha256
    peer = read(peer_path)
    assert peer["passed"] is True and peer["owner"] == OWNER and peer["material_concerns"] == []
    assert peer["reviewer_thread_id"] not in (OWNER["thread_id"], "/root", "/root/fresh_ops")
    assert peer["FROZEN_sha256"] == sha(HERE / "FROZEN.json")
    assert peer["source_commit"] == SOURCE and peer["admission_sha256"] == args.admission_sha256
    for field, filename in (
        ("controller_sha256", "production_controller.py"), ("transport_sha256", "run_setup_once.py"),
        ("resolver_sha256", "source_resolver.py"), ("dispatch_sha256", "dispatch_rvec_once.py"),
        ("switch_sha256", "switch_rvec_pointer.py"), ("guard_sha256", "packet_runtime.py")):
        assert peer[field] == sha(HERE / filename)
    assert peer["source_review_passed"] is True and peer["production_transport_review_passed"] is True
    assert peer["scoped_resolver_canonical_dispatch_review_passed"] is True
    return OWNER, receipt, server


def arguments(parser):
    for option in ("admission", "admission-sha256", "review", "review-sha256", "deployment-result-sha256"):
        parser.add_argument("--" + option, required=False)


def require_arguments(args):
    assert all(getattr(args, key) for key in (
        "admission", "admission_sha256", "review", "review_sha256", "deployment_result_sha256"))


def actual_production(result_path, review_path, review_sha):
    result_path, review_path = (Path(path).resolve() for path in (result_path, review_path))
    assert result_path.is_relative_to(ROOT.resolve()) and review_path.is_relative_to(ROOT.resolve())
    assert sha(review_path) == review_sha
    result, peer = read(result_path), read(review_path)
    assert peer["passed"] is True and peer["owner"] == OWNER and peer["material_concerns"] == []
    assert peer["reviewer_thread_id"] not in (OWNER["thread_id"], "/root", "/root/fresh_ops")
    assert peer["production_result_sha256"] == sha(result_path)
    assert result["owner"] == OWNER and result["kind"] == "PRODUCTION_PATH_INSTALLED_NO_TRAINER_LAUNCHED"
    assert result["binding"]["source_commit"] == SOURCE and result["binding"]["runtime_root"] == RUNTIME
    assert result["shim"] == PRODUCTION + "/conda_source.sh"
    assert result["training_launch_or_GPU_use"] is False and result["one_shot_consumed"] is False
    return result
