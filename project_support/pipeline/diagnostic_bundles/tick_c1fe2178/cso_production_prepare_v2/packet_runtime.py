"""Current-owner M236 runtime verification -> collect -> render guards; import inert."""
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
SOURCE = "5413102c57b526035f3920b5e7a81f3b58ad764d"
PARENT = "b1e639b3ceb14bb5c65d9f81a084d41c834b951c"
RUNTIME = "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
CONFIG = "configs/Quard/ctf_hcg_csort_cso/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cso.yaml"
PRODUCER = "/data/songcl/Project/Cluster_project/pipeline/runtime/cso_path_prepare_c1fe2178_v2"
PRODUCTION = "/data/songcl/Project/Cluster_project/pipeline/runtime/cso_path_prod_c1fe2178_v2"
VERIFICATION = TICK / "cso_deployment_execution/sync.actual.json"
OWNER = {
    "token": "c1fe217800894083b65baac45f79aa83",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-14T01:52:47.538159+00:00",
    "deadline_at": "2026-11-14T02:52:47.538159+00:00",
    "context_sha256": "e33442420ba4c77b839918c43c944153092f834b2d316bb8979f843d3cdf82a4",
    "pending_sha256": "3d0bc5d2092b154a1acdb483f3d9185e95e9aa411b2089930f01dc1fd96875e6",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def arguments(parser):
    for name in ("admission", "admission-sha256", "review", "review-sha256",
                 "current-verification", "current-verification-sha256"):
        parser.add_argument("--" + name)


def require_arguments(args):
    assert all(getattr(args, key) for key in ("admission", "admission_sha256", "review", "review_sha256",
                                             "current_verification", "current_verification_sha256"))


def guard(args, *, pointer=False, minimum=180):
    assert sys.dont_write_bytecode and not sys.flags.optimize
    assert os.environ.get("GIT_OPTIONAL_LOCKS") == "0" and os.environ.get("CODEX_THREAD_ID") == OWNER["thread_id"]
    live = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {key: live[key] for key in OWNER} == OWNER
    assert (datetime.fromisoformat(OWNER["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > minimum
    mode = read(ROOT / "pipeline/execution_mode.json")
    assert mode["mode"] == "foreground" and mode["target_thread_id"] == OWNER["thread_id"]
    for filename, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / filename) == OWNER[key]
    frozen = read(HERE / "FROZEN.json")
    assert frozen["owner"] == OWNER and frozen["source_commit"] == SOURCE
    assert all(sha(HERE / name) == expected for name, expected in frozen["files"].items())
    assert all(sha(ROOT / item["path"]) == item["sha256"] for item in frozen["anchors"])
    baseline = read(HERE / "baseline.json")
    assert sha(ROOT / "SERVERS.yaml") == baseline["SERVERS_sha256"]
    assert sha(ROOT / "pipeline/goal.json") == baseline["goal_sha256"]
    from source_resolver import verify
    verify()
    # Require the new owner's real canonical safe_sync outcome; no historical sync relabel.
    verification_path = Path(args.current_verification).resolve()
    assert verification_path == VERIFICATION.resolve()
    assert sha(verification_path) == args.current_verification_sha256
    proof = read(verification_path)
    assert proof["owner"] == OWNER and proof["passed"] is True
    assert proof["certainty"] == "terminal" and proof["canonical_safe_sync"] is True
    assert proof["source_commit"] == SOURCE and proof["runtime_root"] == RUNTIME
    assert proof["runtime_code_commit"] == SOURCE
    assert proof["source_verified"] is True and proof["source_integrity_before_after"] is True
    assert proof["source_files_exact9"] == baseline["source_files_exact9"]
    assert proof["runtime_before"] == PARENT
    assert proof["training_started"] is False and proof["GPU_compute"] is False
    assert proof["signals_sent"] is False and proof["automatic_retry"] is False
    actual = proof["actual"]
    assert actual["hostname"] == "dl04-MS-7E06" and actual["uid"] == 1001
    assert actual["runtime_HEAD"] == SOURCE
    assert [(item["kind"], item["device"], item["inode"]) for item in actual["original_locks"]] == [
        ("training", 66308, 92537152), ("diagnostic", 66308, 92537153), ("exclusive", 66308, 92537154),
    ]
    receipt_path = Path(args.admission).resolve()
    assert receipt_path == (ROOT / "pipeline/admissions/M236-CSO.json").resolve()
    assert sha(receipt_path) == args.admission_sha256 == frozen["admission_sha256"]
    receipt = read(receipt_path)
    assert receipt["id"] == "M236-CSO" and receipt["candidate_id"] == "fine-leaf-full-covariance-shape-composition"
    assert receipt["code_commit"] == SOURCE and receipt["config"] == CONFIG
    assert receipt["goal_sha256"] == baseline["goal_sha256"] and receipt["profile"] == "experiment_first"
    assert all(receipt["gates"][name]["passed"] is True for name in
               ("native_backward", "resources", "independence", "constraints"))
    task = {"id": "M236-CSO", "candidate_id": receipt["candidate_id"], "config": CONFIG,
            "code_commit": SOURCE, "profile": "experiment_first", "requires_exclusive_ownership": False,
            "admission_receipt": receipt_path.relative_to(ROOT).as_posix()}
    sys.path.insert(0, str(SKILL))
    import closure
    import pipeline_monitor as monitor
    closure.admission(ROOT, task)
    server = monitor.load_servers(str(ROOT))["server-4"]
    assert server["host"] == "192.168.1.115" and server["user"] == "songcl"
    assert server["expected_hostname"] == "dl04-MS-7E06" and server["remote_code_root"] == RUNTIME
    assert server["allowed_gpus"] == [0] and server["max_tasks_per_gpu"] == 1
    assert server["allow_external_overlay"] is True and server["task_memory_mb"] == 20000
    # The canonical loader omits UUID metadata; verify it from the unchanged inventory.
    import yaml
    inventory = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]["server-4"]
    uuids = inventory["expected_gpu_uuids"]
    assert str(uuids.get("0", uuids.get(0))) == "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
    review_path = Path(args.review).resolve()
    assert review_path.is_relative_to(TICK) and sha(review_path) == args.review_sha256
    peer = read(review_path)
    assert peer["owner"] == OWNER and peer["passed"] is True and peer["material_concerns"] == []
    assert peer["reviewer_thread_id"] not in (OWNER["thread_id"], "/root", "/root/fresh_ops", "/root/sinc_prod", "/root/cso_native_ops", "/root/cso_readiness")
    assert peer["FROZEN_sha256"] == sha(HERE / "FROZEN.json")
    assert peer["source_commit"] == SOURCE and peer["admission_sha256"] == args.admission_sha256
    for key, name in (("controller_sha256", "production_controller.py"), ("transport_sha256", "run_setup_once.py"),
                      ("resolver_sha256", "source_resolver.py"), ("guard_sha256", "packet_runtime.py"),
                      ("receiver_sha256", "remote_receiver.py.txt")):
        assert peer[key] == sha(HERE / name)
    assert peer["source_review_passed"] is True and peer["production_transport_review_passed"] is True
    assert peer["locked_direct_memory_free_and_cap1_integration_review_passed"] is True
    assert peer["lock_core_sha256"] == sha(HERE / "lock_core.py")
    return OWNER, receipt, server


def actual_production(result_path, review_path, review_sha):
    result_path, review_path = Path(result_path).resolve(), Path(review_path).resolve()
    assert result_path.is_relative_to(TICK) and review_path.is_relative_to(TICK)
    assert sha(review_path) == review_sha
    result, peer = read(result_path), read(review_path)
    assert peer["owner"] == OWNER and peer["passed"] is True and peer["material_concerns"] == []
    assert peer["reviewer_thread_id"] not in (OWNER["thread_id"], "/root", "/root/fresh_ops", "/root/sinc_prod", "/root/cso_native_ops", "/root/cso_readiness")
    assert peer["production_result_sha256"] == sha(result_path)
    assert result["owner"] == OWNER and result["kind"] == "PRODUCTION_PATH_INSTALLED_NO_TRAINER_LAUNCHED"
    binding = result["binding"]
    assert binding["owner"] == OWNER and binding["owner_deadline_at"] == OWNER["deadline_at"]
    assert binding["producer"] == PRODUCER and binding["stage"] == PRODUCTION
    assert binding["source_commit"] == SOURCE and binding["runtime_root"] == RUNTIME
    assert binding["entry"] == PRODUCTION + "/bin/python" and result["shim"] == PRODUCTION + "/conda_source.sh"
    assert binding["one_shot_marker"] == PRODUCTION + "/train-consumed.json"
    assert binding["physical_gpu"] == 0 and binding["expected_gpu_uuid"] == "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
    assert binding["max_project_tasks"] == 1 and binding["required_free_memory_mib"] == 20000
    assert result["training_launch_or_GPU_use"] is False and result["one_shot_consumed"] is False
    return result
