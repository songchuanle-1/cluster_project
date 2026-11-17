"""Default NOP; one current-owner canonical MIC GPU0 dispatch, never replay."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import copy
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
HERE = Path(__file__).resolve().parent
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
EXP = "M229-MIC"
CID = "hierarchy-ancestry-mobius-interaction-composition"
COMMIT = "07ef534a6e44f22bd7b2d083550ebd7823d1d3d3"
NEW_ROOT = "/data/songcl/Project/Cluster_project/Cluster_mic_20261105"
UUID = "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
FIXED_SHA = "3ea8ed1bce3be8cc749a4718b01f043228243e98119c5afe13a6c997c36cf044"
RECEIPT_SHA = "b7cb59e0b78ae81f4b3dec9dd5b40a19b1797cb4a0902e704918eb6ff7f3ff40"
CALLS = []
EXPECTED = {
    "token": "3b2b394d2fa242b19bbf4fef5ea11c67",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-05T13:07:08.623175+00:00",
    "deadline_at": "2026-11-05T14:07:08.623175+00:00",
    "context_sha256": "fe48ed24dba1c4e039abbf0c098ace6ec43bad7c5c91b3def914f40e492dc065",
    "pending_sha256": "8a63b7b374f3cd520c81f28baae4a09b5f9266b53b45eafd4f65e40893922d77",
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def ref(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT.resolve())
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def guard(minimum=0):
    owner = read(P / "headless/.foreground.lockdir/owner.json")
    assert all(owner.get(k) == v for k, v in EXPECTED.items()), "Current owner changed"
    assert os.environ.get("CODEX_THREAD_ID") == EXPECTED["thread_id"], "Owning root chat required"
    assert read(P / "execution_mode.json") == {"mode": "foreground", "target_thread_id": EXPECTED["thread_id"]}
    assert (datetime.fromisoformat(EXPECTED["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > minimum
    assert sha(P / "headless/.tick_context.json") == EXPECTED["context_sha256"]
    assert sha(P / "headless/.tick_context_state.next.json") == EXPECTED["pending_sha256"]


def save(path, value, exclusive=False):
    guard()
    path = Path(path)
    target = path if exclusive else path.with_name(path.name + ".3b2b394d.dispatch.tmp")
    with target.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    if not exclusive:
        guard()
        os.replace(target, path)


def checked(reference):
    assert isinstance(reference, dict) and {"path", "sha256"} <= set(reference)
    path = (ROOT / reference["path"]).resolve()
    assert path.is_relative_to(ROOT.resolve()) and path.is_file()
    assert sha(path) == reference["sha256"], str(path)
    return read(path) if path.suffix == ".json" else None


def evidence_graph(value, seen=None, depth=0):
    """Verify actual project-local hash references without running producers."""
    seen = set() if seen is None else seen
    assert depth < 200
    if isinstance(value, dict):
        if {"path", "sha256"} <= set(value) and isinstance(value["path"], str):
            if value["path"].startswith("/"):
                # Observed remote asset/checkpoint hashes are not local references.
                return seen
            key = (value["path"], value["sha256"])
            if key not in seen:
                seen.add(key)
                nested = checked(value)
                if nested is not None:
                    evidence_graph(nested, seen, depth + 1)
        else:
            for child in value.values():
                evidence_graph(child, seen, depth + 1)
    elif isinstance(value, list):
        for child in value:
            evidence_graph(child, seen, depth + 1)
    return seen


def immutable_evidence(receipt_path, peer_path, runtime_path):
    guard()
    fixed_path = HERE / "mic_dispatch_immutable_raw_bindings.json"
    assert sha(fixed_path) == FIXED_SHA
    fixed = read(fixed_path)
    assert fixed["owner"] == EXPECTED and fixed["code_commit"] == COMMIT
    refs = fixed["actual_raw_and_static_refs"]
    for entry in refs.values():
        checked(entry)
    for name in ("smoke_champion", "smoke_candidate", "resources_champion", "resources_candidate"):
        raw = checked(refs[name])
        result = raw["result"]
        mode, target = name.split("_", 1)
        assert raw["certainty"] == "terminal" and raw["returncode"] == 0
        assert raw["identity"]["candidate_id"] == result["candidate_id"] == CID
        assert raw["identity"]["code_commit"] == result["code_commit"] == COMMIT
        assert result["execution_completed"] is True and result["mode"] == mode and result["target"] == target
    prior = checked(refs["prior_reuse_review"])
    assert prior["passed"] is True and prior["candidate_id"] == CID
    actual_binding = checked(refs["actual_binding_review"])
    assert actual_binding["passed"] is True and actual_binding["material_concerns"] == []
    grant = checked(refs["resource_authorization"])
    assert grant["allow_external_overlay"] is True and grant["allowed_gpus"] == [0]
    assert grant["task_memory_mb"] == 20000 and grant["max_project_tasks_per_gpu"] == 1
    assert sha(receipt_path) == RECEIPT_SHA, "Actual reviewed MIC admission changed"
    receipt = read(receipt_path)
    assert receipt["id"] == EXP and receipt["candidate_id"] == CID and receipt["code_commit"] == COMMIT
    assert receipt["goal_sha256"] == sha(P / "goal.json")
    assert receipt["profile"] == "experiment_first"
    peer = read(peer_path)
    assert peer["candidate_id"] == CID and peer["code_commit"] == COMMIT
    assert peer.get("owner") == EXPECTED and peer.get("material_concerns") == []
    assert peer.get("passed") is True or peer.get("review_status") in (
        "RAW_SEMANTICS_VALIDATED_NOT_ADMISSION", "ACTUAL_RESULTS_INDEPENDENTLY_VERIFIED")
    for name in ("native_backward", "resources", "independence", "constraints"):
        gate = receipt["gates"][name]
        assert gate["passed"] is True and gate["evidence"], name
    evidence_graph(receipt)
    evidence_graph(peer)
    proof = read(runtime_path)
    assert proof.get("owner") == EXPECTED and proof.get("returncode", 0) == 0
    runtime = proof.get("observation", proof.get("data", proof))
    assert runtime["runtime_root"] == NEW_ROOT and runtime["runtime_code_commit"] == COMMIT
    assert runtime["source_verified"] is True and runtime["old_roots_preserved"] is True
    assert runtime.get("old_roots_before") is not None
    assert runtime["old_roots_before"] == runtime["old_roots_after"]
    template = checked(refs["static_manifest_template"])
    return {
        "immutable_existing_raws": ref(fixed_path), "receipt": ref(receipt_path),
        "independent_actual_gate_review": ref(peer_path), "runtime_preparation": ref(runtime_path),
        "project_authorization": refs["project_authorization"],
        "resource_authorization": refs["resource_authorization"],
        "candidate_source_hashes": template["candidate_source_hashes"],
        "candidate_name": template["candidate_name"], "config": template["config"],
        "candidate_config_sha256": template["candidate_config_sha256"],
    }


def local_source(catalogue):
    git = ["C:/Program Files (x86)/Git/cmd/git.exe", "--no-optional-locks",
           "-c", "core.fsmonitor=false", "-C", str(ROOT / "Cluster")]
    query = lambda *args: subprocess.check_output(git + list(args))
    assert query("rev-parse", "HEAD").decode().strip() == COMMIT
    assert not query("diff", "--cached", "--name-only", "-z"), "Unexpected staged changes"
    index = Path(query("rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = ROOT / "Cluster" / index
    baseline = read(HERE / "protected_assets_before.json")
    files = {name: sha(ROOT / "Cluster" / name) for name in baseline["files"]}
    assert files == baseline["files"], "Protected user files changed"
    model = ROOT / "Cluster/framework/model/Quard_model" / catalogue["candidate_name"]
    source = {name: sha(model / name) for name in catalogue["candidate_source_hashes"]}
    assert source == catalogue["candidate_source_hashes"]
    assert sha(ROOT / "Cluster" / catalogue["config"]) == catalogue["candidate_config_sha256"]
    return {"head": COMMIT, "status_hex": query("status", "--porcelain=v1", "--untracked-files=all", "-z").hex(),
            "index_sha256": sha(index), "protected_user_files": files, "MIC_source": source}


def unrelated():
    queue = copy.deepcopy(read(P / "queue.json"))
    for tasks in queue["gpu_queues"].values():
        tasks[:] = [t for t in tasks if t.get("id") != EXP]
    running = copy.deepcopy(read(P / "running.json"))
    for server in list(running):
        running[server] = {g: t for g, t in running[server].items() if t != EXP}
        if not running[server]:
            del running[server]
    files = [ROOT / "SERVERS.yaml", P / "goal.json", P / "closure_policy.json", P / "experiments.csv"]
    files += list((P / "admissions").glob("*.json"))
    files += [f for f in (P / "experiments").glob("*.json") if f.name != EXP + ".json"]
    files += list((P / "authorizations").glob("*.json"))
    candidates = read(P / "research_work.json")["candidates"]
    return {"queue_without_MIC": queue, "running_without_MIC": running,
            "other_ledgers_and_settings": {f.relative_to(ROOT).as_posix(): sha(f) for f in files},
            "other_candidate_digests": {c["id"]: digest(c) for c in candidates if c["id"] != CID}}


def strict_ssh(host, user, command, timeout=8):
    guard()
    assert (host, user) == ("192.168.1.115", "songcl")
    inventory = "nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null"
    if command == inventory:
        command = command.replace("nvidia-smi ", "nvidia-smi -i 0 ", 1)
    elif "nvidia-smi" in command:
        raise RuntimeError("Unexpected canonical GPU query: do not query another card")
    launch = "proc=subprocess.Popen(" in command and "tools/train.py" in command
    if "Popen" in command and "tools/train.py" in command:
        assert launch
    remote_guard = "import socket;assert socket.gethostname()=='dl04-MS-7E06'"
    if launch:
        assert command.count("proc=subprocess.Popen(") == 1
        assert not any(c["canonical_native_launch_request"] for c in CALLS), "Never repeat native launch"
        assert NEW_ROOT in command, "Wrong launch root"
        deadline = 'assert __import__("datetime").datetime.now(__import__("datetime").timezone.utc)<__import__("datetime").datetime.fromisoformat("' + EXPECTED["deadline_at"] + '"); '
        command = command.replace("proc=subprocess.Popen(", deadline + "proc=subprocess.Popen(", 1)
        remote_guard = """import socket,subprocess,fcntl,os,sys,json
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06'
handles=[]
try:
 for kind in ('training','diagnostic','exclusive'):
  f=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip().split(',')
 assert row[0].strip()=='0' and row[1].strip()==GPU_UUID and int(row[3])-int(row[2])>=20000
 contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
 observation={'observed_at':datetime.now(timezone.utc).isoformat(),'physical_gpu':0,'gpu_uuid':GPU_UUID,'gpu_inventory':','.join(row),'memory_free_mib':int(row[3])-int(row[2]),'external_contexts_raw':contexts,'allow_external_overlay':True,'minimum_free_mib':20000,'cooperative_locks':['training','diagnostic','exclusive'],'external_tasks_signaled':False,'exclusive_physical_claim':False}
 sys.stderr.write('GPU0_OVERLAY_PRELAUNCH='+json.dumps(observation)+'\\n');sys.stderr.flush()
 env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONFAULTHANDLER']='1'
 result=subprocess.run(['/bin/bash','-lc',COMMAND],env=env,capture_output=True,text=True,timeout=120)
 sys.stdout.write(result.stdout);sys.stderr.write(result.stderr)
 if result.returncode:raise SystemExit(result.returncode)
finally:
 for handle in handles:handle.close()
""".replace("GPU_UUID", repr(UUID)).replace("COMMAND", repr(command))
    checked_command = "export PYTHONDONTWRITEBYTECODE=1 && /usr/bin/python3 -B -c " + shlex.quote(remote_guard)
    if not launch:
        checked_command += " && " + command
    args = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
            "-o", "ConnectTimeout=8", user + "@" + host, checked_command]
    process = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=max(timeout, 150))
    CALLS.append({"recorded_at": datetime.now(timezone.utc).isoformat(), "command": args,
                  "returncode": process.returncode, "stdout": process.stdout, "stderr": process.stderr,
                  "canonical_native_launch_request": launch, "physical_gpu": 0, "gpu_uuid": UUID})
    save(HERE / "mic_dispatch_transport_calls.json", CALLS)
    if process.returncode:
        raise RuntimeError("Pinned SSH failed; reconcile exact original attempt, never blind retry: " + process.stderr[-2000:])
    return process.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--runtime-proof")
    parser.add_argument("--peer-review", default=str(HERE / "mic_actual_independent_review.json"))
    parser.add_argument("--receipt", default=str(P / "admissions/M229-MIC.json"))
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_DISPATCH", "id": EXP}))
        return
    guard(150)
    assert args.runtime_proof, "Actual deployment proof is required"
    receipt_path, peer_path, runtime_path = [Path(x).resolve() for x in (args.receipt, args.peer_review, args.runtime_proof)]
    assert receipt_path == (P / "admissions/M229-MIC.json").resolve()
    assert peer_path.is_relative_to(HERE.resolve()) and runtime_path.is_relative_to(HERE.resolve())
    for filename in ("mic_dispatch_request.json", "mic_dispatch_result.json", "mic_dispatch_transport_calls.json"):
        assert not (HERE / filename).exists(), "Prior attempt exists; reconcile, never replay"
    catalogue = immutable_evidence(receipt_path, peer_path, runtime_path)
    sys.path.insert(0, str(SKILL))
    import pipeline_monitor as mon
    import closure
    lock = mon.acquire_lock(str(ROOT))
    assert lock is not None
    old_ssh = mon.ssh
    old_git_ssh = os.environ.get("GIT_SSH_COMMAND")
    try:
        guard(120)
        local_before, other_before = local_source(catalogue), unrelated()
        server = mon.load_servers(str(ROOT))["server-4"]
        assert server["host"] == "192.168.1.115" and server["user"] == "songcl"
        assert server["expected_hostname"] == "dl04-MS-7E06" and server["remote_code_root"] == NEW_ROOT
        assert server["allowed_gpus"] == [0] and server["max_tasks_per_gpu"] == 1
        assert server["dispatch_enabled"] is True and server["allow_external_overlay"] is True
        assert server["task_memory_mb"] == 20000 and server["expected_gpu_uuid"] == UUID
        queue = mon.load_queue(str(ROOT))
        tasks = queue["gpu_queues"]["server-4"]
        target = [t for t in tasks if t.get("id") == EXP]
        assert len(target) == 1
        task = target[0]
        assert task["status"] == "waiting" and task["code_commit"] == COMMIT and str(task["gpu"]) == "0"
        assert task["config"] == catalogue["config"] and task["admission_receipt"] == "pipeline/admissions/M229-MIC.json"
        assert task.get("requires_exclusive_ownership") is False
        assert not task.get("pid") and not task.get("dispatch_hold") and not task.get("resume_from")
        assert not task.get("launch_verified") and task.get("launch_verification") != "pending_progress"
        assert task.get("dispatch_phase") not in ("launch_requested", "progress_pending")
        assert [t["id"] for t in tasks if t.get("status") == "waiting" and not t.get("dispatch_hold")] == [EXP]
        for other in tasks:
            hold = other.get("dispatch_hold", "")
            uncertain = isinstance(hold, str) and hold.startswith(("Interrupted claim;", "Launch uncertain;", "Process observed"))
            assert not (other.get("status") in ("running", "claiming") or (
                other.get("status") == "waiting" and (other.get("launch_verification") == "pending_progress" or uncertain)))
        assert not any(mon.load_running(str(ROOT)).get("server-4", {}).values())
        closure.admission(ROOT, task)
        closure.validate_foreground_dispatch_budget(ROOT, queue, task)
        mon.ssh = strict_ssh
        os.environ["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8"
        guard()
        assert local_source(catalogue) == local_before and unrelated() == other_before
        save(HERE / "mic_dispatch_request.json",
             {"owner": EXPECTED, "recorded_at": datetime.now(timezone.utc).isoformat(),
              "id": EXP, "code_commit": COMMIT, "operation": "one_existing_canonical_FIFO_GPU0_overlay_dispatch",
              "actual_admission_and_deployment_catalogue": catalogue, "physical_gpu": 0, "gpu_uuid": UUID,
              "protected_local_before": local_before, "protected_other_state_before": other_before}, exclusive=True)
        events = []
        mon._process_queue(queue, "server-4", server["host"], server["user"], str(ROOT),
                           set(), {"0"}, events, max_tasks_per_gpu=1, allow_external_overlay=True,
                           task_memory_mb=20000, remote_code_root=NEW_ROOT, current_tasks=0, max_tasks_total=1)
        final = next(t for t in mon.load_queue(str(ROOT))["gpu_queues"]["server-4"] if t.get("id") == EXP)
        assert str(final["gpu"]) == "0"
        verified = final["status"] == "running" and final.get("launch_verified") is True and final.get("launch_verification") == "training_progress"
        observations = []
        for call in CALLS:
            steps = [(int(a), int(b)) for a, b in re.findall(r"Train\[(\d+)/\d+\]:[^\r\n]*?\|\s*(\d+)/\d+", call["stdout"])]
            if steps:
                observations.append({"recorded_at": call["recorded_at"], "native_train": list(max(steps))})
        assert local_source(catalogue) == local_before and unrelated() == other_before
        work = read(P / "research_work.json")
        candidate = next(c for c in work["candidates"] if c["id"] == CID)
        candidate.update(stage="training" if verified else "deployment",
                         training_status="running" if verified else final["status"],
                         remote_code_root=NEW_ROOT,
                         next_action=("Monitor the exact MIC PID/log on server4 GPU0; canonical increasing native steps verified; efficacy remains unknown."
                                      if verified else "Preserve original request/claim/PID/log/receipt; reconcile exact attempt; never blind retry or cold fallback."))
        work["updated_at"] = datetime.now(timezone.utc).isoformat()
        experiment = mon.load_experiment(str(ROOT), EXP)
        if experiment is not None:
            experiment["training_status"] = "running" if verified else final["status"]
            guard()
            mon.save_experiment(str(ROOT), experiment)
        save(P / "research_work.json", work)
        assert unrelated() == other_before
        result = {"owner": EXPECTED, "recorded_at": datetime.now(timezone.utc).isoformat(),
                  "canonical_dispatch_invoked_once": True, "events": events, "task_after": final,
                  "running_after": mon.load_running(str(ROOT)), "verified_native_progress": verified,
                  "native_progress_samples": observations, "physical_gpu": 0, "gpu_uuid": UUID,
                  "signals_sent": False, "blind_relaunch_performed": False,
                  "protected_other_tasks_holds_index_and_terminal_receipts_unchanged": True,
                  "transport_calls": ref(HERE / "mic_dispatch_transport_calls.json")}
        save(HERE / "mic_dispatch_result.json", result, exclusive=True)
        print(json.dumps({"id": EXP, "status": final["status"], "pid": final.get("pid"),
                          "launch_verified": final.get("launch_verified"), "log": final.get("log"),
                          "evidence": ref(HERE / "mic_dispatch_result.json")}, ensure_ascii=False))
    finally:
        mon.ssh = old_ssh
        if old_git_ssh is None:
            os.environ.pop("GIT_SSH_COMMAND", None)
        else:
            os.environ["GIT_SSH_COMMAND"] = old_git_ssh
        lock.close()


if __name__ == "__main__":
    main()
