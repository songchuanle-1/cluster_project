"""Current-owner once-only controller for the reviewed CPU lock guardian."""
from datetime import datetime, timezone
from pathlib import Path
import base64
import hashlib
import json
import os
import shlex
import subprocess

ROOT = Path("D:/project/cluster_project")
PIPE = ROOT / "pipeline"
HERE = Path(__file__).resolve().parent
TOKEN = "20c15273b622479495bada469c5f3c99"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
STAGE = "/data/songcl/Project/Cluster_project/pipeline/cooperative_guards/m230_20c15273"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guard():
    value = read(PIPE / "headless/.foreground.lockdir/owner.json")
    assert value["token"] == TOKEN and value["thread_id"] == os.environ["CODEX_THREAD_ID"] == THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(value["deadline_at"])
    assert sha(PIPE / "headless/.tick_context.json") == value["context_sha256"]
    assert sha(PIPE / "headless/.tick_context_state.next.json") == value["pending_sha256"]
    return {k: value[k] for k in (
        "token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256",
    )}


owner = guard()
request = HERE / "guardian_start_request.json"
result_path = HERE / "guardian_start_result.json"
assert not request.exists() and not result_path.exists(), "Reconcile any existing CPU start; never replay"
binding_path = HERE / "binding.json"
binding = read(binding_path)
assert binding["owner"] == owner
assert binding["postlaunch_correction"] is True and binding["prelaunch_lock_check_proven"] is False
script_path = HERE / "guardian.py"
assert sha(script_path) == binding["guardian_script_sha256"] == "83cda70864923f77da6ac0d3a69f303dbd257a2396ff2680a0b3f22749851cc4"
remote_path = HERE / "remote_guardian_start.py"
assert sha(remote_path) == binding["remote_start_program_sha256"]
assert sha(PIPE / "authorizations/server4_gpu0_overlay_20261104.json") == binding["resource_authorization_sha256"] == "783ffc27d48872940c2e15adcb85f6bb5f9b94492a8abd88694799f483d20e88"
assert sha(ROOT / "SERVERS.yaml") == binding["servers_sha256"] == "6a87d428190d77955500b34d58bff0310eecb13c8b233c7b3e4fd7ef253787a7"
assert sha(PIPE / "admissions/M230-HVD.json") == binding["admission_receipt_sha256"] == "c92fcd22366cd5d84253c33ab37b2b72857915e239cfc5bb7741a58baa549a33"
assert sha(HERE / "hvd_live_before.json") == binding["observation_sha256"]
task = next(t for t in read(PIPE / "queue.json")["gpu_queues"]["server-4"] if t["id"] == "M230-HVD")
assert task["pid"] == binding["trainer_pid"] == 2829477
assert task["status"] == "running" and task["launch_verified"] is True
assert task["code_commit"] == binding["source_commit"] and task["log"] == binding["trainer_log"]
assert str(task["gpu"]) == "0"
packet = {
    "binding": binding, "stage": STAGE,
    "script_base64": base64.b64encode(script_path.read_bytes()).decode("ascii"),
}
command = [
    "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
    "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
    "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c " + shlex.quote(remote_path.read_text(encoding="utf8")),
]
with request.open("x", encoding="utf8") as stream:
    json.dump({
        "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Once-only CPU guardian for existing exact trainer; no GPU/trainer launch/signals.",
        "binding_sha256": sha(binding_path), "binding": binding,
        "guardian_script_sha256": sha(script_path), "remote_start_sha256": sha(remote_path),
        "actual_command": command,
    }, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
guard()
completed = subprocess.run(
    command, input=json.dumps(packet), capture_output=True,
    encoding="utf8", errors="replace", timeout=40,
)
with result_path.open("x", encoding="utf8") as stream:
    json.dump({
        "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr,
        "request_sha256": sha(request), "binding_sha256": sha(binding_path),
        "guardian_script_sha256": sha(script_path), "actual_command": command,
    }, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
assert completed.returncode == 0, "Preserve exact result and reconcile; no replay: " + completed.stderr[-1500:]
result = json.loads(completed.stdout)
assert result["state"]["status"] == "HOLDING" and result["live_three_locks_confirmed"] is True
print(json.dumps({
    "guardian_pid": result["spawn"]["guardian_pid"],
    "guardian_starttime": result["spawn"]["guardian_starttime"],
    "trainer_pid": result["state"]["trainer_pid"], "three_locks": "HOLDING",
    "postlaunch_correction": True, "prelaunch_lock_check_proven": False,
    "training_restarted": False, "training_launches": 0, "signals_sent": False,
    "evidence": {"path": result_path.relative_to(ROOT).as_posix(), "sha256": sha(result_path)},
}))
