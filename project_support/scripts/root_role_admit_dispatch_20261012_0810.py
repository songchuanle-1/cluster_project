"""One reviewed admission using the canonical gated queue dispatcher."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
TOKEN = "612af628c2f046f4acf6414e49f6f18a"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_tmr"
CONFIG = f"configs/Quard/ctf_hcg_csort_tmr/{NAME}.yaml"
ID = "M200-TMR"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def evidence(path):
    file = ROOT / path
    return {"path": path, "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8")


def main():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    os.environ["PROJECT_ROOT"] = "D:/project"
    sys.path.insert(0, str(SKILL))
    import closure
    import pipeline_monitor as monitor
    code = ROOT / "Cluster"
    commit = closure.git(code, "rev-parse", "HEAD")
    manifest = read(ROOT / "pipeline/reports/root_role_static_v2_20261012_0810.json")
    for file in manifest["files"]:
        path = f"framework/model/Quard_model/{NAME}/{file['filename']}"
        payload = subprocess.check_output(["git", "-C", str(code), "show", f"{commit}:{path}"])
        assert hashlib.sha256(payload).hexdigest() == file["sha256"]
    config_payload = subprocess.check_output(["git", "-C", str(code), "show", f"{commit}:{CONFIG}"])
    assert hashlib.sha256(config_payload).hexdigest() == manifest["config_sha256"]
    comparison = read(ROOT / "pipeline/reports/root_role_resource_compare_20261012_0810.json")
    assert comparison["uniform_resource_gate_passed"] is True
    assert comparison["native_repeat_gate_passed"] is True
    assert comparison["prediction_catalog_control_passed"] is True
    servers = monitor.load_servers(str(ROOT))
    server = servers["server-6"]
    assert server["host"] == "100.64.3.28" and server["allowed_gpus"] == [7]
    assert server["dispatch_enabled"] and server["max_tasks_per_gpu"] == 2
    assert not servers["server-4"]["allowed_gpus"] and not servers["server-4"]["dispatch_enabled"]
    live = monitor.ssh(server["host"], server["user"],
        "test \"$(hostname)\" = das && "
        "test \"$(nvidia-smi -i 7 --query-gpu=uuid --format=csv,noheader)\" = "
        "GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a && "
        "flock -n /tmp/cluster_project_gpu7_slot2_diagnostic.lock true && "
        "nvidia-smi -i 7 --query-gpu=utilization.gpu,memory.used,memory.total "
        "--format=csv,noheader,nounits")
    values = [int(value.strip()) for value in live.strip().split(",")]
    assert len(values) == 3 and values[0] < 10 and values[1] < 1000
    queue = monitor.load_queue(str(ROOT))
    tasks = [task for rows in queue["gpu_queues"].values() for task in rows]
    assert not any(task["id"] == ID for task in tasks)
    assert not any(task["status"] in ("waiting", "running", "claiming") for task in tasks)
    assert not (ROOT / f"pipeline/experiments/{ID}.json").exists()
    decision = evidence("pipeline/decisions/20261012-085804_route_change.md")
    review = "pipeline/reviews/motivation_review_v2_20261012_0810.md"
    design = "pipeline/designs/exp_design_v2_20261012_0810.md"
    sources = {
        "diagnosis": ["pipeline/reports/root_role_audit_v2_20261012_0810.json", review],
        "controls": ["pipeline/reports/root_role_incremental_20261012_0810.json",
                     "pipeline/reports/root_role_predict_controls_20261012_0810.json", review],
        "native_backward": ["pipeline/reports/root_role_full_native_v2_20261012_0810.json", review],
        "resources": ["pipeline/reports/root_role_resource_compare_20261012_0810.json", review],
        "independence": ["pipeline/reports/root_role_static_v2_20261012_0810.json",
                         "pipeline/reports/root_role_primary_source_20261012_0810.json", review],
        "constraints": [design, review, "pipeline/goal.json"],
    }
    receipt = {
        "id": ID, "config": CONFIG, "code_commit": commit,
        "goal_sha256": evidence("pipeline/goal.json")["sha256"],
        "gates": {name: {"passed": True, "evidence": [evidence(path) for path in paths]}
                  for name, paths in sources.items()},
        "decision": decision,
        "limitations": "One structural screen, not trained efficacy or independent novelty. Prior numeric/adapter failures preserved.",
    }
    receipt_path = ROOT / f"pipeline/admissions/{ID}.json"
    assert not receipt_path.exists()
    receipt_path.parent.mkdir(exist_ok=True)
    save(receipt_path, receipt)
    task = {
        "id": ID, "label": "M200-TMR target mention role supervision",
        "config": CONFIG, "status": "waiting", "gpu": 7,
        "code_commit": commit, "admission_receipt": f"pipeline/admissions/{ID}.json",
    }
    closure.admission(ROOT, task)
    ledger_path = ROOT / "pipeline/research_work.json"
    work = read(ledger_path)
    candidate = next(row for row in work["candidates"] if row["id"] == "m95-native-target-mention-role")
    refs = list(dict.fromkeys(path for paths in sources.values() for path in paths))
    refs += ["pipeline/reports/root_role_full_native_20261012_0810.json",
             "pipeline/reports/root_role_resource_failure_20261012_0810.json",
             "pipeline/reports/butd_joint_det_dataset_20261012_0810.py",
             "scripts/root_role_full_native_v2_20261012_0810.py",
             "scripts/root_role_predict_only_20261012_0810.py",
             "scripts/root_role_resources_v2_20261012_0810.py",
             "scripts/root_role_resource_compare_20261012_0810.py",
             f"pipeline/admissions/{ID}.json"]
    for path in refs:
        bound = evidence(path)
        if bound not in candidate["evidence"]:
            candidate["evidence"].append(bound)
    candidate.update(stage="admission", experiment_id=ID, code_commit=commit,
                     next_action="Canonical safe ff-only sync and native increasing-training-step verification.",
                     limitations="Initial full-forward FAIL retained; v2 native repeats repaired without tolerance change. Trained gain, population identity quality and independent novelty unknown.")
    work.pop("design_cycle", None)
    save(ledger_path, work)
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None, "Canonical project dispatch lock unavailable"
    try:
        queue["gpu_queues"]["server-6"].append(task)
        monitor.save_queue(str(ROOT), queue)
        monitor._process_queue(
            queue, "server-6", server["host"], server["user"], str(ROOT),
            set(), {"7"}, [], max_tasks_per_gpu=2, allow_external_overlay=False,
            task_memory_mb=server["task_memory_mb"],
            remote_code_root=server["remote_code_root"], current_tasks=0,
            max_tasks_total=server.get("max_tasks"))
    finally:
        lock.close()
    actual = next(row for row in monitor.load_queue(str(ROOT))["gpu_queues"]["server-6"]
                  if row["id"] == ID)
    result = {
        "id": ID, "code_commit": commit, "admission": evidence(str(receipt_path.relative_to(ROOT)).replace("\\", "/")),
        "fresh_prelaunch_gpu7": values, "task": actual,
        "no_repeated_preflight": True, "dispatcher": "canonical pipeline_monitor._process_queue",
    }
    result_path = ROOT / "pipeline/reports/root_role_dispatch_20261012_0810.json"
    save(result_path, result)
    candidate["evidence"].append(evidence(str(result_path.relative_to(ROOT)).replace("\\", "/")))
    candidate.update(stage="training" if actual.get("launch_verified") else "deployment",
                     next_action="Monitor actual native validation and predefined subgroups; do not restart/tune." if actual.get("launch_verified")
                     else "Reconcile exact PID/log/sync error; never blindly relaunch.")
    save(ledger_path, work)
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
