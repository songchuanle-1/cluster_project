"""Root-only one-time canonical HVD dispatch. Default NOP; never removes holds."""
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
PIPE = ROOT / "pipeline"
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
EXEC = TICK / "hvd_dispatch_execute"
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
EXP = "M230-HVD"
CID = "hierarchy-native-variance-decomposition-composition"
COMMIT = "d20eb221eff6584b67d4e9b5673559d0e1cb735b"
CONFIG = "configs/Quard/ctf_hcg_csort_hvd/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hvd.yaml"
RUNTIME = "/data/songcl/Project/Cluster_project/Cluster_hvd_20261106"
UUID = "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
RECEIPT_SHA = "c92fcd22366cd5d84253c33ab37b2b72857915e239cfc5bb7741a58baa549a33"
EXPECTED = {
    "token": "12e364dc14cd4e1195532c7fd295b834",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-06T11:09:29.664423+00:00",
    "deadline_at": "2026-11-06T12:09:29.664423+00:00",
    "context_sha256": "bf1e90947d091f4e8fe53f8876d130ac0d5493d8ff0a82e1547eb900459588a1",
    "pending_sha256": "6877a9553b1a86ab70fe0e29c1442ff1e70b52c875adc38549034c975f87f162",
}
CALLS = []
ARGS = None


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reference(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT.resolve())
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def guard(seconds=0):
    owner = read(PIPE / "headless/.foreground.lockdir/owner.json")
    assert {key: owner.get(key) for key in EXPECTED} == EXPECTED
    assert os.environ.get("CODEX_THREAD_ID") == EXPECTED["thread_id"]
    assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    assert read(PIPE / "execution_mode.json") == {
        "mode": "foreground", "target_thread_id": EXPECTED["thread_id"]}
    assert (datetime.fromisoformat(EXPECTED["deadline_at"]) -
            datetime.now(timezone.utc)).total_seconds() > seconds
    assert sha(PIPE / "headless/.tick_context.json") == EXPECTED["context_sha256"]
    assert sha(PIPE / "headless/.tick_context_state.next.json") == EXPECTED["pending_sha256"]
    assert sha(__file__) == read(HERE / "FROZEN.json")["files"]["dispatch_hvd_once.py"]


def save(name, value, replace=False):
    guard()
    path = EXEC / name
    assert path.parent == EXEC and EXEC.is_dir()
    target = path.with_name(path.name + ".tmp") if replace else path
    with target.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    if replace:
        guard()
        os.replace(target, path)


def checked(path, expected_sha):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT.resolve()) and sha(path) == expected_sha
    return read(path)


def objects(value, depth=0):
    """Read the ACTUAL CPU runner's nested returncode/stdout JSON schema."""
    assert depth < 20
    if isinstance(value, dict):
        yield value
        for key, child in value.items():
            if key not in ("stdin_program", "work_before"):
                yield from objects(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child, depth + 1)
    elif isinstance(value, str):
        try:
            child = json.loads(value)
        except (ValueError, TypeError):
            return
        yield from objects(child, depth + 1)


def validate_cpu_proof(raw, shim_sha):
    assert raw.get("passed") is True and raw.get("hostname") == "dl04-MS-7E06"
    assert raw.get("runtime_root") == RUNTIME and raw.get("runtime_code_commit") == COMMIT
    assert raw.get("actual_user") == "songcl" and raw.get("actual_uid") == raw.get("actual_euid") == 1001
    assert {key: raw.get("root_owner_provenance", {}).get(key) for key in EXPECTED} == EXPECTED
    core = raw["real_exec_lock_proof"]
    assert all(core.get(key) is True for key in ("passed", "same_Bash_exec_PID", "exact_special_and_empty_argv", "three_retained_non_CLOEXEC_FDs", "three_real_contended_locks"))
    assert core.get("uid") == 1001 and core.get("model_GPU_execution") is False
    routes = raw["routing"]
    expected_cases = {"exact6", "duplicate_GPU", "GPU1", "other_config", "missing_num_gpus", "duplicate_num_gpus", "Python_B_prefix", "absolute_train_alias"}
    assert {item["case"] for item in routes} == expected_cases and len(routes) == len(expected_cases)
    assert all(item["passed"] is True and item["no_actual_training_target_executed"] is True and item["returncode"] == (0 if item["case"] == "exact6" else 126) for item in routes)
    assert raw["normal_CPU_passthrough"]["passed"] is True and raw["normal_CPU_passthrough"]["argv_exact"] is True
    assert raw["three_locks_released_after_CPU_exit"] is True and raw["original_conda_source_unchanged"] is True
    assert all(raw[key] is False for key in ("GPU_or_model_or_training_execution", "signals_or_background_guardian", "SERVERS_queue_source_checkpoint_or_oldstage_changed"))
    return core


def accepted_inputs(args, closure):
    guard()
    receipt_path = PIPE / "admissions/M230-HVD.json"
    receipt = checked(receipt_path, RECEIPT_SHA)
    assert all(receipt.get(key) == value for key, value in {
        "id": EXP, "candidate_id": CID, "code_commit": COMMIT,
        "config": CONFIG, "profile": "experiment_first",
        "goal_sha256": sha(PIPE / "goal.json")}.items())
    proof_path, review_path = Path(args.lock_proof).resolve(), Path(args.peer_review).resolve()
    proof = checked(proof_path, args.lock_proof_sha256)
    review = checked(review_path, args.peer_review_sha256)
    result = validate_cpu_proof(proof, args.shim_sha256)
    binding_path = proof_path.parent / "binding.json"
    binding = checked(binding_path, proof["binding_sha256"])
    assert binding["root_owner_provenance"] == EXPECTED
    assert binding["runtime_root"] == RUNTIME and binding["runtime_code_commit"] == COMMIT
    assert binding["files"]["server4_conda_hvd_three_locks.sh"] == args.shim_sha256
    assert binding["remote_stage"] + "/server4_conda_hvd_three_locks.sh" == args.shim_path
    runtime_path = Path(args.runtime_proof).resolve()
    runtime = checked(runtime_path, args.runtime_proof_sha256)
    assert runtime["runtime_root"] == RUNTIME and runtime["runtime_code_commit"] == COMMIT
    assert runtime["source_verified"] is True and runtime["old_roots_preserved"] is True
    assert runtime["old_roots_before"] == runtime["old_roots_after"]
    assert review.get("passed") is True
    assert review.get("material_concerns", review.get("blocking_issues")) == []
    refs = list(objects(review))
    assert any(node.get("path") == reference(proof_path)["path"] and
               node.get("sha256") == args.lock_proof_sha256 for node in refs)
    # Peer review must cover the actual shim, including canonical Popen argv routing.
    # Exact reviewed proof binds its immutable binding.json, which binds shim SHA.
    assert sha(ROOT / "SERVERS.yaml") == args.servers_sha256
    version_path = PIPE / "diagnostic_bundles/tick_1138a3fc/hvd_compatible_source_version.json"
    version = checked(version_path, "7e3c09ea021de7350e74a7797e535c91990e3a9b226a20af1ed1917c06e8bc41")
    assert version["code_commit"] == COMMIT
    paths = version["source_files_exact9"]
    assert len(paths) == 9 and CONFIG in paths
    assert runtime["source_paths"] == paths
    task = {"id": EXP, "candidate_id": CID, "code_commit": COMMIT, "config": CONFIG,
            "admission_receipt": "pipeline/admissions/M230-HVD.json", "profile": "experiment_first"}
    closure.admission(ROOT, task)
    return {"receipt": reference(receipt_path), "actual_cpu_lock_proof": reference(proof_path),
            "actual_lock_and_canonical_routing_review": reference(review_path),
            "CPU_binding": reference(binding_path), "runtime_deployment": reference(runtime_path),
            "source_version": reference(version_path), "source_files_exact9": paths,
            "CPU_result": result, "shim_path": args.shim_path, "shim_sha256": args.shim_sha256,
            "SERVERS_sha256": args.servers_sha256}


def local_state(catalogue):
    code = ROOT / "Cluster"
    git = ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(code)]
    query = lambda *args: subprocess.check_output(git + list(args))
    assert query("rev-parse", "HEAD").decode().strip() == COMMIT
    index = Path(query("rev-parse", "--git-path", "index").decode().strip())
    index = index if index.is_absolute() else code / index
    baseline = read(PIPE / "diagnostic_bundles/tick_0f3c54ec/protected_assets_before.json")
    assert len(baseline["dirty_files"]) == 20
    users = {name: sha(code / name) for name in baseline["dirty_files"]}
    assert users == baseline["dirty_files"]
    sources = {name: sha(code / name) for name in catalogue["source_files_exact9"]}
    assert sources == catalogue["source_files_exact9"]
    return {"head": COMMIT, "index_sha256": sha(index),
            "all_index_entries_sha256": hashlib.sha256(query("ls-files", "--stage", "-z")).hexdigest(),
            "status_hex": query("status", "--porcelain=v1", "--untracked-files=all", "-z").hex(),
            "protected20": users, "HVD_exact9": sources}


def unrelated():
    queue, running = copy.deepcopy(read(PIPE / "queue.json")), copy.deepcopy(read(PIPE / "running.json"))
    for tasks in queue["gpu_queues"].values():
        tasks[:] = [task for task in tasks if task.get("id") != EXP]
    for server in list(running):
        running[server] = {gpu: task for gpu, task in running[server].items() if task != EXP}
        if not running[server]:
            del running[server]
    names = ("SERVERS.yaml", "pipeline/goal.json", "pipeline/closure_policy.json",
             "pipeline/execution_mode.json", "pipeline/experiments.csv", "pipeline/research_work.json",
             "pipeline/experiments/M206-CGCA.json", "pipeline/experiments/M227-LFT.json",
             "pipeline/experiments/M229-MIC.json", "pipeline/admissions/M230-HVD.json",
             "pipeline/authorizations/server4_gpu0_overlay_20261104.json")
    return {"queue_except_HVD": queue, "running_except_HVD": running,
            "settings_other_results_and_research": {name: sha(ROOT / name) for name in names}}


PROBE = r'''
import socket,json,subprocess,sys,os,pathlib,hashlib
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06'
assert datetime.now(timezone.utc)<datetime.fromisoformat(P['deadline'])
assert hashlib.sha256(pathlib.Path(P['shim']).read_bytes()).hexdigest()==P['shim_sha']
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,utilization.gpu,memory.used,memory.total','--format=csv,noheader,nounits'],text=True).strip().split(',')
row=[x.strip() for x in row]
assert row[0]=='0' and row[1]==P['uuid']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
ob={'observed_at':datetime.now(timezone.utc).isoformat(),'physical_gpu':0,'gpu_uuid':row[1],'utilization':int(row[2]),'memory_used_mib':int(row[3]),'memory_total_mib':int(row[4]),'memory_free_mib':int(row[4])-int(row[3]),'contexts_raw':contexts,'external_overlay_permitted':True,'project_max_tasks':1,'required_new_task_memory_mib':20000,'shim_sha256':P['shim_sha']}
sys.stderr.write('HVD_GPU0_PRELAUNCH='+json.dumps(ob)+'\n');sys.stderr.flush()
if not P['launch']:
 print(', '.join([row[0],row[2],row[3],row[4]]))
else:
 assert ob['memory_free_mib']>=20000
 for proc in pathlib.Path('/proc').glob('[0-9]*'):
  try:
   argv=(proc/'cmdline').read_bytes().split(b'\0');cwd=os.readlink(proc/'cwd')
  except (OSError,ValueError):continue
  assert not (b'tools/train.py' in argv and cwd.startswith('/data/songcl/Project/Cluster_project/')),'Existing project trainer; reconcile'
 # Do not hold competing outer locks: the reviewed production shim owns and
 # inherits the three actual flock descriptors into the trainer.
 stage=pathlib.Path(P['stage']);stage.mkdir(exist_ok=False)
 with (stage/'prelaunch_gpu0.json').open('x') as f:
  json.dump(ob,f);f.flush();os.fsync(f.fileno())
 result=subprocess.run(['/bin/bash','-lc',P['command']],capture_output=True,text=True,timeout=120,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 sys.stdout.write(result.stdout);sys.stderr.write(result.stderr)
 raise SystemExit(result.returncode)
'''


def strict_ssh(host, user, command, timeout=8):
    guard()
    assert (host, user) == ("192.168.1.115", "songcl")
    inventory = "nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null"
    launch = "proc=subprocess.Popen(" in command and "tools/train.py" in command
    if "Popen" in command and "tools/train.py" in command:
        assert launch and command.count("proc=subprocess.Popen(") == 1
    if command == inventory or launch:
        if launch:
            assert not any(call["canonical_launch_request"] for call in CALLS), "Never repeat Popen request"
            assert RUNTIME in command and CONFIG in command and ARGS.shim_path in command
        params = {"deadline": EXPECTED["deadline_at"], "shim": ARGS.shim_path,
                  "shim_sha": ARGS.shim_sha256, "uuid": UUID, "launch": launch,
                  "command": command, "stage": "/data/songcl/Project/Cluster_project/pipeline/hvd_dispatch_" + EXPECTED["token"][:8]}
        remote = "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c " + shlex.quote("P=" + repr(params) + "\n" + PROBE)
    else:
        assert "nvidia-smi" not in command, "Unexpected/GPU1 inventory query"
        assert not re.search(r"\bkill(?:all)?\b|\bpkill\b|\bsudo\b", command)
        remote = ("PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c " +
                  shlex.quote("import socket;assert socket.gethostname()=='dl04-MS-7E06'") +
                  " && " + command)
    args = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
            "-o", "ConnectTimeout=8", user + "@" + host, remote]
    process = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=max(timeout, 150))
    call = {"recorded_at": datetime.now(timezone.utc).isoformat(), "command": args,
            "returncode": process.returncode, "stdout": process.stdout, "stderr": process.stderr,
            "canonical_launch_request": launch, "physical_gpu": 0}
    CALLS.append(call)
    save("transport_calls.json", CALLS, replace=True)
    for line in process.stderr.splitlines():
        if line.startswith("HVD_GPU0_PRELAUNCH="):
            value = json.loads(line.split("=", 1)[1])
            if not launch:
                save("initial_gpu0_selection_probe.json", value)
    assert process.returncode == 0, "SSH failed; preserve original intent/claim, reconcile, never retry"
    return process.stdout.strip()


def live_inherited_locks(pid, ssh):
    code = r'''
import pathlib,os,json
p=pathlib.Path('/proc')/str(PID);assert p.is_dir()
state=(p/'stat').read_text();start=state[state.rfind(')')+2:].split()[19]
assert os.readlink(p/'cwd')==ROOT
fds={}
for f in (p/'fd').iterdir():
 try:target=os.readlink(f)
 except OSError:continue
 if target in PATHS:fds[target]=int(f.name)
assert set(fds)==set(PATHS)
table=pathlib.Path('/proc/locks').read_text().splitlines();held=[]
for path in PATHS:
 st=pathlib.Path(path).stat();key='%02x:%02x:%d'%(os.major(st.st_dev),os.minor(st.st_dev),st.st_ino)
 rows=[row for row in table if len(row.split())>5 and row.split()[5]==key]
 assert len(rows)==1 and rows[0].split()[1]=='FLOCK' and rows[0].split()[3]=='WRITE' and int(rows[0].split()[4])==PID
 held.extend(rows)
print(json.dumps({'pid':PID,'starttime':start,'three_inherited_fds':fds,'kernel_locks':held,'read_only':True,'GPU_or_signals':False}))
'''
    values = "PID=" + repr(pid) + "\nROOT=" + repr(RUNTIME) + "\nPATHS=" + repr(
        ["/tmp/cluster_project_gpu0_" + kind + ".lock" for kind in ("training", "diagnostic", "exclusive")]) + "\n"
    output = ssh("192.168.1.115", "songcl",
                 "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c " + shlex.quote(values + code))
    return json.loads(output)


def main():
    global ARGS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    for name in ("servers-sha256", "shim-path", "shim-sha256", "lock-proof",
                 "lock-proof-sha256", "peer-review", "peer-review-sha256", "runtime-proof", "runtime-proof-sha256"):
        parser.add_argument("--" + name)
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_DISPATCH", "id": EXP,
                          "actual_CPU_proof_peer_review_final_settings_required": True}))
        return
    ARGS = args
    assert all(getattr(args, name) for name in ("servers_sha256", "shim_path", "shim_sha256",
               "lock_proof", "lock_proof_sha256", "peer_review", "peer_review_sha256", "runtime_proof", "runtime_proof_sha256"))
    guard(180)
    assert not EXEC.exists(), "Existing execution directory/intent: reconcile, never replay"
    sys.path.insert(0, str(SKILL))
    import pipeline_monitor as mon
    import closure
    catalogue = accepted_inputs(args, closure)
    lock = mon.acquire_lock(str(ROOT))
    assert lock is not None
    original_ssh, original_git_ssh = mon.ssh, os.environ.get("GIT_SSH_COMMAND")
    try:
        guard(150)
        assert accepted_inputs(args, closure) == catalogue
        server = mon.load_servers(str(ROOT))["server-4"]
        assert all(server.get(key) == value for key, value in {
            "host": "192.168.1.115", "user": "songcl", "expected_hostname": "dl04-MS-7E06",
            "remote_code_root": RUNTIME, "allowed_gpus": [0], "max_tasks_per_gpu": 1,
            "dispatch_enabled": True, "allow_external_overlay": True, "task_memory_mb": 20000,
            "conda_source": args.shim_path}.items())
        import yaml
        raw_server = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]["server-4"]
        assert raw_server["expected_gpu_uuid"] == UUID
        assert str(raw_server["expected_gpu_uuids"].get("0", raw_server["expected_gpu_uuids"].get(0))) == UUID
        queue = mon.load_queue(str(ROOT))
        tasks = queue["gpu_queues"]["server-4"]
        selected = [task for task in tasks if task.get("id") == EXP]
        assert len(selected) == 1
        task = selected[0]
        assert all(task.get(key) == value for key, value in {
            "status": "waiting", "code_commit": COMMIT, "config": CONFIG,
            "admission_receipt": "pipeline/admissions/M230-HVD.json",
            "requires_exclusive_ownership": False}.items())
        assert str(task["gpu"]) == "0"
        assert not any(task.get(key) for key in ("pid", "log", "dispatch_hold", "resume_from", "launch_verified"))
        assert task.get("launch_verification") != "pending_progress"
        assert task.get("dispatch_phase") not in ("launch_requested", "progress_pending")
        assert [other["id"] for other in tasks if other.get("status") == "waiting" and not other.get("dispatch_hold")] == [EXP]
        assert not [other for values in queue["gpu_queues"].values() for other in values if other.get("status") in ("running", "claiming")]
        assert not any(mon.load_running(str(ROOT)).values())
        for tid in ("M206-CGCA", "M227-LFT"):
            paused = [other for other in tasks if other.get("id") == tid]
            assert len(paused) == 1 and paused[0].get("resume_authorized") is False
            assert paused[0].get("dispatch_hold") and not paused[0].get("pid")
        closure.admission(ROOT, task)
        closure.validate_foreground_dispatch_budget(ROOT, queue, task)
        before_local, before_other = local_state(catalogue), unrelated()
        EXEC.mkdir(exist_ok=False)
        save("dispatch_request.json", {"owner": EXPECTED, "id": EXP,
             "operation": "ONCE_EXISTING_CANONICAL_FIFO_DISPATCH", "catalogue": catalogue,
             "settings": reference(ROOT / "SERVERS.yaml"), "protected_local": before_local,
             "protected_unrelated": before_other, "script": reference(__file__)})
        mon.ssh = strict_ssh
        os.environ["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8"
        events = []
        mon._process_queue(queue, "server-4", server["host"], server["user"], str(ROOT),
                           set(), {"0"}, events, max_tasks_per_gpu=1,
                           allow_external_overlay=True, task_memory_mb=20000,
                           remote_code_root=RUNTIME, current_tasks=0, max_tasks_total=1)
        final = next(other for other in mon.load_queue(str(ROOT))["gpu_queues"]["server-4"] if other.get("id") == EXP)
        verified = final.get("status") == "running" and final.get("launch_verified") is True and final.get("launch_verification") == "training_progress"
        inherited = live_inherited_locks(final["pid"], strict_ssh) if verified else None
        assert local_state(catalogue) == before_local and unrelated() == before_other
        result = {"owner": EXPECTED, "canonical_dispatch_invoked_once": True,
                  "task_after": final, "events": events, "verified_native_progress": verified,
                  "live_inherited_three_lock_proof": inherited,
                  "initial_numeric_GPU0_probe": reference(EXEC / "initial_gpu0_selection_probe.json"),
                  "transport_calls": reference(EXEC / "transport_calls.json"),
                  "holds_and_unrelated_state_unchanged": True, "signals_or_blind_relaunch": False}
        save("dispatch_result.json", result)
        print(json.dumps({"id": EXP, "pid": final.get("pid"), "verified_native_progress": verified,
                          "evidence": reference(EXEC / "dispatch_result.json")}))
    finally:
        mon.ssh = original_ssh
        if original_git_ssh is None:
            os.environ.pop("GIT_SSH_COMMAND", None)
        else:
            os.environ["GIT_SSH_COMMAND"] = original_git_ssh
        lock.close()


if __name__ == "__main__":
    main()
