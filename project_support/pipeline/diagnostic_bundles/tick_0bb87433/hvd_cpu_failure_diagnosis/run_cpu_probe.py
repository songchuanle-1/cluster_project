"""Once-only child CPU observation; root ownership is provenance, not impersonation."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import shlex
import subprocess

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "0bb874337dde412e98bbbaac369f3370"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
assert owner["token"] == TOKEN
assert owner["thread_id"] == "01a159c5-29ab-7a22-ba7f-e79174757253"
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
assert sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
provenance = {k: owner[k] for k in (
    "token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256",
)}
request_path = HERE / "cpu_request.json"
result_path = HERE / "cpu_observation.json"
assert not request_path.exists() and not result_path.exists(), "Never replay a probe with uncertain output"
script = HERE / "remote_cpu_probe.py"
command = [
    "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
    "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
    "CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 "
    "/home/songcl/.conda/envs/project_cluster/bin/python -B -",
]
request = {
    "recorded_at": datetime.now(timezone.utc).isoformat(),
    "root_owner_provenance_only": provenance,
    "actual_child_thread_id": os.environ.get("CODEX_THREAD_ID"),
    "actual_command": command, "script_sha256": sha(script),
    "authorized_scope": "One read-only CPU installed-library/custom-attention observation; no GPU/NVML/training/checkpoint/source/env/package mutation/restart/signals.",
}
with request_path.open("x", encoding="utf8") as stream:
    json.dump(request, stream, indent=2)
    stream.write("\n")
completed = subprocess.run(
    command, input=script.read_text(encoding="utf8"), capture_output=True,
    text=True, encoding="utf8", errors="replace", timeout=90,
)
record = {
    "recorded_at": datetime.now(timezone.utc).isoformat(),
    "root_owner_provenance_only": provenance,
    "actual_child_thread_id": os.environ.get("CODEX_THREAD_ID"),
    "request_sha256": sha(request_path), "script_sha256": sha(script),
    "actual_command": command, "returncode": completed.returncode,
    "stderr": completed.stderr,
    "observation": json.loads(completed.stdout) if completed.returncode == 0 else None,
    "raw_stdout_if_failed": completed.stdout if completed.returncode else None,
}
with result_path.open("x", encoding="utf8") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
assert completed.returncode == 0, completed.stderr[-2000:]
observed = record["observation"]
print(json.dumps({
    "returncode": completed.returncode,
    "torch": observed.get("torch"),
    "cpu_reproduction": observed.get("cpu_reproduction"),
    "probe_error": observed.get("probe_error"),
    "conclusion": observed.get("conclusion"),
    "evidence_path": str(result_path), "evidence_sha256": sha(result_path),
}, ensure_ascii=False))
