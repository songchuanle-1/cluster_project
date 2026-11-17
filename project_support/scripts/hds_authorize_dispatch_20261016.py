"""Apply one source-bound user exception and use the canonical dispatcher."""
import argparse
import ast
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
TOKEN = "04dd082c4615443f9db9cf8a1a7e496b"
CID = "m95-hierarchical-mask-feature-path-audit"
EXP = "M202-HDS"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1"
CONFIG = f"configs/Quard/ctf_hcg_csort_hds_canon_r1/{NAME}.yaml"
PRIOR = "pipeline/diagnostic_bundles/memory_trace_cc39552e325049f5b8ac15dd3e055b06"
BUNDLE = ROOT / "pipeline/diagnostic_bundles/hds_authorized_04dd082c"
AUTH = "pipeline/authorizations/hds_flops_exception_20261016_04dd082c.json"
OLD_GOAL = "0579017d274fde882de816864dd9729551408c6c4605be098652545fce9f0cc2"
sys.path.insert(0, str(SKILL))
os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
import closure
import foreground_tick as tick
import pipeline_monitor as monitor
import yaml


def now():
    return datetime.now(timezone.utc).isoformat()


def guard():
    owner = tick.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert owner["deadline_at"] == "2026-10-16T06:40:26.269948+00:00"
    assert datetime.fromisoformat(owner["deadline_at"]) > datetime.now(timezone.utc)
    return owner


def save(path, value):
    guard()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tick.save(path, value)


def ev(path):
    return {"path": path, "sha256": tick.digest(ROOT / path)}


def add_evidence(candidate, *paths):
    for path in paths:
        entry = ev(path)
        if entry not in candidate.setdefault("evidence", []):
            candidate["evidence"].append(entry)


def work_candidate():
    work = tick.load(ROOT / "pipeline/research_work.json")
    return work, next(c for c in work["candidates"] if c["id"] == CID)


def checked_ssh(host, user, command, timeout=60):
    assert host == "192.168.1.120" and user == "songcl"
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
         "-o", "ConnectTimeout=10", f"{user}@{host}", command],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    if result.returncode:
        raise RuntimeError(f"SSH exit {result.returncode}: {result.stderr[-1200:]}")
    return result.stdout.strip()


def verified_sources(commit=None):
    manifest = tick.load(ROOT / PRIOR / "independent_upload.json")["local_files"]
    for item in manifest:
        assert tick.digest(ROOT / item["path"]) == item["sha256"], item["path"]
        if commit:
            relative = item["path"].removeprefix("Cluster/")
            payload = subprocess.check_output(
                ["git", "-C", str(ROOT / "Cluster"), "show", f"{commit}:{relative}"]
            )
            assert hashlib.sha256(payload).hexdigest() == item["sha256"], relative
    dirty = "Cluster/scripts/validate_pdc_20261009.py"
    assert tick.digest(ROOT / dirty) == (
        "00d58e60d96a61272d4c8719fbca85fab449252ea84311ee3af09be015b26c26"
    )
    return manifest


def prepare():
    guard()
    assert not (ROOT / AUTH).exists()
    assert tick.digest(ROOT / "pipeline/goal.json") == OLD_GOAL
    work, candidate = work_candidate()
    assert candidate["stage"] == "blocked"
    assert len(candidate["revision_history"]) == 2
    assert all(r["result"] == "passed" for r in candidate["revision_history"])
    for gate in candidate["gates"].values():
        for entry in gate["evidence"]:
            closure.artifact(ROOT, entry)
    for name in ("diagnosis", "controls", "native_backward", "independence"):
        assert candidate["gates"][name]["passed"] is True
    assert candidate["gates"]["resources"]["passed"] is False
    manifest = verified_sources()
    save(BUNDLE / "original_gates.json", {
        "recorded_at": now(), "candidate_id": CID, "gates": candidate["gates"],
        "blocker": candidate["blocker"], "failure_scope": candidate["failure_scope"],
        "old_goal_sha256": OLD_GOAL, "revision_count": 2,
    })
    authorization = {
        "schema_version": 1, "recorded_at": now(), "thread_id": os.environ["CODEX_THREAD_ID"],
        "token": TOKEN, "candidate_id": CID, "experiment_id": EXP,
        "user_quote": "10G也可以的 超出也不多",
        "interpretation": "Explicit acceptance of this already-measured 10.034588748G realization only.",
        "standard_counted_flops": 10034588748,
        "default_limit_flops": 10000000000, "excess_percent": 0.34588748,
        "implementation_revision_sha256": closure.revision_digest(candidate["revision_history"][-1]),
        "source_files": manifest,
        "frozen_upload": ev(PRIOR + "/independent_upload.json"),
        "resource_measurement": ev(PRIOR + "/resource_analysis.json"),
        "scope": "No source/config change, revision3, global FLOPs increase, gate bypass, seed/schedule/data change or auxiliary-route reopening.",
        "preserved_negative_gates": ev(str((BUNDLE / "original_gates.json").relative_to(ROOT)).replace("\\", "/")),
    }
    save(ROOT / AUTH, authorization)
    goal = tick.load(ROOT / "pipeline/goal.json")
    original_constraints = list(goal["constraints"])
    goal["constraints"].append(
        "[USER-FLOPS-EXCEPTION 2026-10-16] User explicitly accepts the small measured overrun "
        "for SAME m95-hierarchical-mask-feature-path-audit / M202-HDS: 10.034588748G counted "
        "FLOPs (0.34588748% above 10G), bound to the exact ten tested source/config hashes and "
        "passed revision2 in pipeline/authorizations/hds_flops_exception_20261016_04dd082c.json. "
        "This prospective candidate-specific exception supersedes ONLY its default10G rejection; "
        "the default10G for every other realization, original failed evidence, two-revision limit, "
        "memory/latency review, all other gates/bans, seed1999, schedule, data/validation boundaries "
        "and server3GPU1/server4GPU0 permissions remain unchanged. No code change/revision3 is authorized."
    )
    goal.setdefault("resource_exceptions", []).append({
        "candidate_id": CID, "experiment_id": EXP, "authorization": ev(AUTH),
        "max_standard_counted_flops": 10034588748,
        "implementation_revision_sha256": authorization["implementation_revision_sha256"],
    })
    assert goal["constraints"][:-1] == original_constraints
    save(ROOT / "pipeline/goal.json", goal)
    result = {
        "recorded_at": now(), "candidate_id": CID, "files": manifest,
        "all_tested_bytes_unchanged": True, "implementation_revisions": 2,
        "authorization": ev(AUTH), "goal": ev("pipeline/goal.json"),
        "original_failure_preserved": authorization["preserved_negative_gates"],
        "resource_review": {
            "standard_counted_flops": 10034588748, "baseline_counted_flops": 9762532428,
            "median_latency_ms": [83.1302, 83.6800],
            "inference_peak_bytes": [928491008, 928491008],
            "matched_train_peak_bytes": [4293406720, 4499342848],
            "relative_train_peak_increase": 0.047965669555760204,
            "passed_under_specific_user_exception": True,
        },
        "limitations": "Four TRAIN scenes/16 expressions; no optimizer or efficacy evidence; inference resource sample is one fixed VAL expression, not performance selection.",
    }
    save(BUNDLE / "authorization_review.json", result)
    review = ev(str((BUNDLE / "authorization_review.json").relative_to(ROOT)).replace("\\", "/"))
    candidate.setdefault("gate_history", []).append({
        "recorded_at": now(), "reason": "Prospective explicit user exception, not a repair or retroactive original PASS.",
        "evidence": [authorization["preserved_negative_gates"], ev(AUTH)],
    })
    for name in ("resources", "constraints"):
        old = candidate["gates"][name]
        candidate["gates"][name] = {
            "passed": True,
            "status": "Passed prospectively for exact unchanged revision2 under explicit source-bound USER-FLOPS-EXCEPTION; original default10G FAIL retained. All other applicable constraints unchanged.",
            "evidence": [*old["evidence"], ev(AUTH), review, ev("pipeline/goal.json")],
        }
    candidate.update(stage="validation", experiment_id=EXP,
                     next_action="Commit unchanged tested candidate only, bind admission receipt, safely dispatch on server3 physicalGPU1 and verify increasing native steps.",
                     authorization=ev(AUTH))
    for key in ("blocker", "blocker_kind", "retry_after", "unblock_condition"):
        candidate.pop(key, None)
    add_evidence(candidate, AUTH, str((BUNDLE / "authorization_review.json").relative_to(ROOT)).replace("\\", "/"),
                 str((BUNDLE / "original_gates.json").relative_to(ROOT)).replace("\\", "/"))
    scope = {
        "recorded_at": now(), "authorization": ev(AUTH),
        "mainline": goal["research_mainline"],
        "auxiliary_ids": [c["id"] for c in work["candidates"]
                          if c.get("blocker_kind") == "auxiliary_scope_hold"],
        "decision": "Only existing primary HDS realization is authorized. Auxiliary holds remain human scope blocks, not GPU/VRAM blocks. No new independent route or duplicate train run.",
    }
    save(BUNDLE / "scope_check.json", scope)
    for item in work["candidates"]:
        if item.get("blocker_kind") == "auxiliary_scope_hold":
            item["retry_after"] = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
            add_evidence(item, str((BUNDLE / "scope_check.json").relative_to(ROOT)).replace("\\", "/"))
    work["design_cycle"] = {
        "stop_reason": "external_resource_blocked", "attempted_ids": [CID],
        "evidence": [review, ev(str((BUNDLE / "scope_check.json").relative_to(ROOT)).replace("\\", "/"))],
        "resume_condition": "After this one authorized primary experiment launches, use its real training/terminal evidence. Remaining auxiliary candidates need explicit scope authorization, not free GPUs.",
        "scope": "Human scope blocks only for remaining held candidates; no GPU exhaustion, deadline, or scientific route exhaustion claim.",
    }
    save(ROOT / "pipeline/research_work.json", work)
    print(json.dumps({"prepared": True, "candidate_id": CID, "goal_sha256": tick.digest(ROOT / "pipeline/goal.json"),
                      "source_files": len(manifest), "revision_count": 2}))


def guard_source(server, manifest):
    model_files = {item["path"].removeprefix("Cluster/"): item["sha256"]
                   for item in manifest if item["path"].endswith(".py")}
    config = yaml.safe_load((ROOT / "Cluster" / CONFIG).read_text(encoding="utf-8"))
    mappings = [("/home/songcl/data/data", server["data_root"].rstrip("/")),
                ("/home/songcl/3dres/project/cluster_project/Checkpoints", server["work_dir"].rstrip("/"))]

    def adapt(value):
        if isinstance(value, dict):
            return {key: adapt(item) for key, item in value.items()}
        if isinstance(value, list):
            return [adapt(item) for item in value]
        if isinstance(value, str):
            for source, target in mappings:
                value = value.replace(source, target)
        return value

    expected = adapt(config)
    return f'''"""Hold all original project GPU1 locks for the native train lifetime."""
import fcntl, hashlib, json, os, pathlib, subprocess, sys, yaml
from datetime import datetime, timezone
root = pathlib.Path({server["remote_code_root"]!r})
assert pathlib.Path.cwd().resolve() == root.resolve()
assert sys.argv[1:] == ["tools/train.py", {CONFIG!r}, "--gpu_ids", "1", "--num_gpus", "1"]
assert subprocess.check_output(["hostname"], text=True).strip() == "sysu311-MS-7C59"
handles = []
for name in ("m201_migration", "exclusive", "parameter_transport"):
    handle = open("/tmp/cluster_project_gpu1_" + name + ".lock", "a+b")
    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    os.set_inheritable(handle.fileno(), True)
    handles.append(handle)
gpu = subprocess.check_output(["nvidia-smi", "-i", "1", "--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu", "--format=csv,noheader,nounits"], text=True).strip()
parts = [part.strip() for part in gpu.split(",")]
assert parts[0] == "1" and parts[1] == "GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0"
assert int(parts[2]) < 1000 and int(parts[3]) > 20000 and int(parts[4]) < 10
contexts = subprocess.check_output(["nvidia-smi", "-i", "1", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"], text=True).strip()
assert not contexts, "Foreign contexts block launch; never evict them."
for relative, digest in {model_files!r}.items():
    assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == digest, relative
assert yaml.safe_load((root / {CONFIG!r}).read_text()) == {expected!r}
assert pathlib.Path({server["data_root"]!r}).is_dir()
assert pathlib.Path({expected["train"]["pretrain"]!r}).is_file()
print("HDS_GPU_LEASE=" + json.dumps({{"at": datetime.now(timezone.utc).isoformat(), "pid": os.getpid(), "gpu": gpu, "flocks": 3, "fd_inherited_by_native_train": True}}), flush=True)
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
os.environ["PYTHONUNBUFFERED"] = "1"
import ctypes, runpy, torch
manager = pathlib.Path("/sdc1/songcl/Project/Cluster_project/pipeline/runtime/hds_torch_shm_manager_04dd082c")
assert hashlib.sha256(manager.read_bytes()).hexdigest() == "e3cd7b2a6e4b9fa2b6ed265a4a9b5d7613f51477c99fc5e99a59de35653c6161"
lib = ctypes.CDLL(str(pathlib.Path(torch.__file__).parent / "lib/libshm.so"))
initialize = getattr(lib, "_Z11libshm_initPKc")
initialize.argtypes = [ctypes.c_char_p]
initialize.restype = None
initialize(os.fsencode(str(manager)))
dummy = torch.zeros(1, device="cuda")
torch.cuda.synchronize()
own = subprocess.check_output(["nvidia-smi", "--query-compute-apps=pid,gpu_uuid", "--format=csv,noheader,nounits"], text=True)
own = [line for line in own.splitlines() if line.split(",")[0].strip() == str(os.getpid())]
assert len(own) == 1 and "GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0" in own[0], own
del dummy
print("HDS_RUNTIME_READY=" + json.dumps({{"physical_gpu1_confirmed": True, "project_only_shm_manager": str(manager), "sharing_strategy_unchanged": "file_system"}}), flush=True)
sys.argv = sys.argv[1:]
if os.environ.pop("HDS_GUARD_CHECK_ONLY", "") == "1":
    print("HDS_COMPLETE_GUARD_CHECK_PASS", flush=True)
else:
    runpy.run_path(sys.argv[0], run_name="__main__")
'''


def deploy_guard(server, source):
    remote = server["remote_code_root"].rsplit("/", 1)[0] + "/pipeline/runtime/hds_launch_guard_04dd082c_v4.py"
    digest = hashlib.sha256(source.encode()).hexdigest()
    program = (
        "import pathlib,hashlib\n"
        f"p=pathlib.Path({remote!r})\n"
        f"s={source!r}.encode('utf-8')\n"
        "p.parent.mkdir(parents=True,exist_ok=True)\n"
        "assert not p.exists() or p.read_bytes()==s\n"
        "p.write_bytes(s)\n"
        f"assert hashlib.sha256(p.read_bytes()).hexdigest()=={digest!r}\n"
        "print(hashlib.sha256(p.read_bytes()).hexdigest())\n"
    )
    output = checked_ssh(server["host"], server["user"],
                         "/home/songcl/.conda/envs/3d-stmn/bin/python -B -c " + shlex.quote(program))
    assert output == digest
    save(BUNDLE / "launch_guard_v4_deployed.json", {
        "recorded_at": now(), "path": remote, "sha256": digest,
        "scope": "Project-only launcher guard; no model/shared environment/checker changes.",
    })
    return remote


class InsertGuard(ast.NodeTransformer):
    def __init__(self, remote):
        self.remote = remote
        self.count = 0

    def visit_Call(self, node):
        self.generic_visit(node)
        if (isinstance(node.func, ast.Attribute) and node.func.attr == "Popen"
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess"):
            argv = node.args[0]
            assert isinstance(argv, ast.List)
            assert isinstance(argv.elts[0], ast.Constant) and argv.elts[0].value == "python"
            assert isinstance(argv.elts[1], ast.Constant) and argv.elts[1].value == "tools/train.py"
            argv.elts.insert(1, ast.Constant(self.remote))
            self.count += 1
        return node


def admit_dispatch(decision, retry=False, shm_retry=False, guard_retry=False):
    guard()
    work, candidate = work_candidate()
    assert candidate["stage"] == ("deployment" if retry else "validation")
    if retry:
        failure = tick.load(BUNDLE / "placement_failure_stopped.json")
        assert failure["training_steps_observed"] == 0
        assert failure["foreign_pid_preserved"] == 23959
    if shm_retry:
        assert retry
        failure = tick.load(BUNDLE / "shm_failure_stopped.json")
        assert failure["training_steps_observed"] == 0 and failure["foreign_pid_preserved"] == 23959
        transport = tick.load(BUNDLE / "project_shm_transport_test.json")
        assert transport["cpu_tensor_queue_passed"] and transport["two_persistent_workers_four_batches_passed"]
        assert transport["shared_packages_changed"] is False
    if guard_retry:
        assert shm_retry and retry
        failure = tick.load(BUNDLE / "guard_assert_failure_review.json")
        assert failure["training_steps"] == 0 and failure["native_main_reached"] is False
    commit = closure.git(ROOT / "Cluster", "rev-parse", "HEAD")
    assert commit != "f8457d3b657e66306a7fce1afb3d81d8ab874669"
    manifest = verified_sources(commit)
    authorization = tick.load(ROOT / AUTH)
    assert authorization["implementation_revision_sha256"] == closure.revision_digest(candidate["revision_history"][-1])
    assert len(candidate["revision_history"]) == 2
    servers = monitor.load_servers(str(ROOT))
    server = servers["server-3"]
    assert server["host"] == "192.168.1.120"
    assert server["allowed_gpus"] == [1] and server["dispatch_enabled"]
    assert server["max_tasks_per_gpu"] == 1
    decision_evidence = ev(decision)
    design = "pipeline/designs/exp_design_20261016_hier_support.md"
    assert "Post-Training Plan Frozen 2026-10-16" in (ROOT / design).read_text(encoding="utf-8")
    guard_program = guard_source(server, manifest)
    compile(guard_program, "<project-gpu1-launch-guard>", "exec")
    remote_guard = deploy_guard(server, guard_program)
    if guard_retry:
        check = ("source " + shlex.quote(server["conda_source"]) + " && conda activate "
                 + shlex.quote(server["conda_env"]) + " && cd "
                 + shlex.quote(server["remote_code_root"]) + " && HDS_GUARD_CHECK_ONLY=1 "
                 + "PYTHONPATH=" + shlex.quote(server["remote_code_root"] + ":" + server["remote_code_root"] + "/framework/lib")
                 + " python -B " + shlex.quote(remote_guard) + " tools/train.py " + shlex.quote(CONFIG)
                 + " --gpu_ids 1 --num_gpus 1")
        output = checked_ssh(server["host"], server["user"], check)
        assert "HDS_COMPLETE_GUARD_CHECK_PASS" in output
        save(BUNDLE / "complete_guard_check.json", {"recorded_at": now(), "output": output,
             "passed": True, "training_executed": False,
             "guard": ev("pipeline/diagnostic_bundles/hds_authorized_04dd082c/launch_guard_v4_deployed.json")})
    task = {
        "id": EXP, "label": "M202-HDS hierarchical disjoint-support point-feature update",
        "config": CONFIG, "status": "waiting", "gpu": 1, "code_commit": commit,
        "admission_receipt": f"pipeline/admissions/{EXP}.json",
    }
    candidate.update(stage="admission", experiment_id=EXP, code_commit=commit,
                     next_action="Canonical gated ff-only sync; native GPU1 lease guard and step verification.")
    receipt = {
        "id": EXP, "candidate_id": CID, "config": CONFIG, "code_commit": commit,
        "goal_sha256": tick.digest(ROOT / "pipeline/goal.json"),
        "implementation_revision_sha256": closure.revision_digest(candidate["revision_history"][-1]),
        "decision": decision_evidence, "gates": candidate["gates"],
        "post_training_evaluation": ev(design), "user_resource_exception": ev(AUTH),
        "recorded_at": now(),
        "limitations": "Admission only; no trained efficacy, population benefit, generalized memory safety or independent novelty claim.",
    }
    if retry:
        old_receipt = tick.load(ROOT / task["admission_receipt"])
        assert old_receipt["code_commit"] == receipt["code_commit"]
        assert old_receipt["goal_sha256"] == receipt["goal_sha256"]
        assert old_receipt["gates"] == receipt["gates"]
    else:
        assert not (ROOT / task["admission_receipt"]).exists()
        save(ROOT / task["admission_receipt"], receipt)
    add_evidence(candidate, task["admission_receipt"], design, decision)
    save(ROOT / "pipeline/research_work.json", work)
    closure.admission(ROOT, task)
    original_ssh = monitor.ssh
    original_launch = closure.safe_launch

    def launch_with_lease(project, target, item, gpu, ssh):
        assert target["name"] == "server-3" and item["id"] == EXP and str(gpu) == "1"

        def guarded(host, user, command, timeout=60):
            tokens = shlex.split(command)
            assert tokens[-2] == "-c" and tokens[-3] == "python"
            transformer = InsertGuard(remote_guard)
            tree = transformer.visit(ast.parse(tokens[-1]))
            assert transformer.count == 1
            program = ast.unparse(ast.fix_missing_locations(tree))
            compile(program, "<canonical-launch-with-project-locks>", "exec")
            prefix = ("source " + shlex.quote(target["conda_source"]) + " && conda activate "
                      + shlex.quote(target["conda_env"]) + " && python -c ")
            return checked_ssh(host, user, prefix + shlex.quote(program), timeout)
        return original_launch(project, target, item, gpu, guarded)

    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None, "Canonical project lock unavailable"
    try:
        queue = monitor.load_queue(str(ROOT))
        all_tasks = [item for items in queue["gpu_queues"].values() for item in items]
        matches = [item for item in all_tasks if item["id"] == EXP]
        assert len(matches) == (1 if retry else 0)
        assert not any(item["id"] != EXP and item["status"] in ("waiting", "claiming", "running") for item in all_tasks)
        monitor.ssh = checked_ssh
        closure.safe_launch = launch_with_lease
        if retry:
            previous = matches[0]
            assert previous["pid"] == (32568 if guard_retry else 19680 if shm_retry else 3660)
            assert previous["launch_verified"] is False
            earlier_attempts = previous.get("launch_attempts", [])
            archived = {key: value for key, value in previous.items() if key != "launch_attempts"}
            previous.clear()
            previous.update(task, retries=3 if guard_retry else 2 if shm_retry else 1,
                            launch_attempts=[*earlier_attempts, archived])
        else:
            queue["gpu_queues"].setdefault("server-3", []).append(task)
        monitor.save_queue(str(ROOT), queue)
        monitor._process_queue(
            queue, "server-3", server["host"], server["user"], str(ROOT), set(), {"1"}, [],
            max_tasks_per_gpu=1, allow_external_overlay=False,
            task_memory_mb=server["task_memory_mb"], remote_code_root=server["remote_code_root"],
            current_tasks=0, max_tasks_total=1,
        )
    finally:
        monitor.ssh = original_ssh
        closure.safe_launch = original_launch
        lock.close()
        actual = next((item for item in monitor.load_queue(str(ROOT))["gpu_queues"].get("server-3", [])
                       if item["id"] == EXP), None)
        dispatch_file = ("dispatch_verified_guard.json" if guard_retry else "dispatch_shm_fix.json" if shm_retry else
                         "dispatch_binding_fix.json" if retry else "dispatch_result.json")
        save(BUNDLE / dispatch_file, {
            "recorded_at": now(), "task": actual, "admission": ev(task["admission_receipt"]),
            "canonical_dispatcher": "pipeline_monitor._process_queue",
            "no_repeated_preflight": True,
            "project_guard": ev(str((BUNDLE / "launch_guard_v4_deployed.json").relative_to(ROOT)).replace("\\", "/")),
        })
        work, candidate = work_candidate()
        candidate["stage"] = "training" if actual and actual.get("launch_verified") else "deployment"
        candidate["next_action"] = (
            "Monitor native training/validation and frozen post-training plan. No tuning, blind restart, duplicate launch or efficacy claim."
            if candidate["stage"] == "training" else
            "Reconcile exact config/PID/log/sync state before any further action; never relaunch uncertain process."
        )
        add_evidence(candidate, str((BUNDLE / dispatch_file).relative_to(ROOT)).replace("\\", "/"))
        save(ROOT / "pipeline/research_work.json", work)
    print(json.dumps({"task": actual, "code_commit": commit}, ensure_ascii=False))


def observe():
    guard()
    queue = monitor.load_queue(str(ROOT))
    task = next(t for t in queue["gpu_queues"]["server-3"] if t["id"] == EXP)
    server = monitor.load_servers(str(ROOT))["server-3"]
    assert task.get("pid") and task.get("log")
    content = checked_ssh(server["host"], server["user"],
                          f"tail -c 24000 {shlex.quote(task['log'])}")
    progress = closure.steps(content)
    gpu = checked_ssh(server["host"], server["user"],
        "nvidia-smi -i 1 --query-gpu=index,uuid,memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits")
    contexts = checked_ssh(server["host"], server["user"],
        "nvidia-smi -i 1 --query-compute-apps=pid,used_memory --format=csv,noheader,nounits")
    all_contexts = checked_ssh(server["host"], server["user"],
        "nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv,noheader,nounits")
    own_contexts = [line for line in all_contexts.splitlines()
                    if line.split(",")[0].strip() == str(task["pid"])]
    expected_placement = bool(own_contexts) and all(
        "GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0" in line for line in own_contexts)
    prefix = checked_ssh(server["host"], server["user"], f"head -c 600 {shlex.quote(task['log'])}")
    result = {
        "recorded_at": now(), "id": EXP, "pid": task["pid"], "log": task["log"],
        "steps_last": progress[-8:], "increasing_native_steps": len(set(progress)) >= 2,
        "crash_markers": [marker for marker in ("Traceback", "CUDA out of memory", "RuntimeError")
                          if marker in content],
        "gpu": gpu, "contexts": contexts, "task_launch_verified": task.get("launch_verified"),
        "lease_guard_present": "HDS_GPU_LEASE=" in prefix,
        "own_contexts": own_contexts, "expected_gpu1_placement": expected_placement,
    }
    observation_file = ("postlaunch_verified_guard.json" if task.get("retries") == 3 else
                        "postlaunch_after_shm_fix.json" if task.get("retries") == 2 else
                        "postlaunch_after_binding_fix.json" if task["pid"] != 3660 else "postlaunch_observation.json")
    assert not (BUNDLE / observation_file).exists()
    if result["increasing_native_steps"] and not result["crash_markers"] and expected_placement:
        lock = monitor.acquire_lock(str(ROOT))
        assert lock is not None
        try:
            queue = monitor.load_queue(str(ROOT))
            actual = next(t for t in queue["gpu_queues"]["server-3"] if t["id"] == EXP)
            assert actual["pid"] == task["pid"]
            actual.update(launch_verified=True, launch_verification="training_progress")
            actual.pop("dispatch_hold", None)
            monitor.save_queue(str(ROOT), queue)
            experiment = monitor.load_experiment(str(ROOT), EXP)
            experiment.update(launch_verified=True, launch_verification="training_progress")
            monitor.save_experiment(str(ROOT), experiment)
            result["task_launch_verified"] = True
        finally:
            lock.close()
    save(BUNDLE / observation_file, result)
    work, candidate = work_candidate()
    if result["task_launch_verified"] and expected_placement:
        candidate["stage"] = "training"
        candidate["next_action"] = "Monitor native validation against frozen post-training plan; no tuning/restart/duplicate run."
    add_evidence(candidate, str((BUNDLE / observation_file).relative_to(ROOT)).replace("\\", "/"))
    save(ROOT / "pipeline/research_work.json", work)
    print(json.dumps(result, ensure_ascii=False))


def confirm_scope():
    guard()
    work, candidate = work_candidate()
    held = [c for c in work["candidates"] if c["id"] != CID and c.get("stage") == "blocked"
            and c.get("blocker_kind") == "human_authorization"
            and "auxiliary only" in c.get("blocker", "")]
    assert len(held) == 4
    path = "pipeline/diagnostic_bundles/hds_authorized_04dd082c/auxiliary_scope_confirmed.json"
    save(ROOT / path, {"recorded_at": now(), "ids": [c["id"] for c in held],
         "correction": "Actual blocker_kind is human_authorization, not auxiliary_scope_hold; original empty filter result retained.",
         "decision": "Four existing auxiliary routes remain scope-held, not scientifically rejected or GPU-blocked. No promotion/recovery authorized.",
         "authorization": ev(AUTH), "goal": ev("pipeline/goal.json")})
    for item in held:
        item["retry_after"] = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
        add_evidence(item, path)
    add_evidence(candidate, path, "pipeline/diagnostic_bundles/hds_authorized_04dd082c/placement_failure_stopped.json")
    work["design_cycle"]["evidence"].append(ev(path))
    save(ROOT / "pipeline/research_work.json", work)
    print(json.dumps({"auxiliary_holds_confirmed": len(held), "gpu_block_claimed": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "dispatch", "retry", "shm-retry", "guard-retry", "observe", "scope"))
    parser.add_argument("--decision")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    elif args.action in ("dispatch", "retry", "shm-retry", "guard-retry"):
        assert args.decision
        admit_dispatch(args.decision, retry=args.action != "dispatch",
                       shm_retry=args.action in ("shm-retry", "guard-retry"), guard_retry=args.action == "guard-retry")
    elif args.action == "scope":
        confirm_scope()
    else:
        observe()
