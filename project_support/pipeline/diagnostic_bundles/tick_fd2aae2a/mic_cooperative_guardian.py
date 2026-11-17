"""CPU-only flock protection for one already running, exact native process."""
from datetime import datetime, timezone
from pathlib import Path
import fcntl
import hashlib
import json
import os
import select
import subprocess
import sys


def starttime(pid):
    text = (Path("/proc") / str(pid) / "stat").read_text()
    return text[text.rfind(")") + 2:].split()[19]


def identity(binding):
    proc = Path("/proc") / str(binding["trainer_pid"])
    assert starttime(binding["trainer_pid"]) == binding["trainer_starttime"]
    assert proc.stat().st_uid == os.getuid() == binding["trainer_uid"]
    assert os.readlink(proc / "cwd") == binding["runtime_root"]
    assert os.readlink(proc / "fd/1") == binding["trainer_log"]
    argv = [v.decode() for v in (proc / "cmdline").read_bytes().split(b"\0") if v]
    assert argv == binding["trainer_argv"]


binding_path = Path(sys.argv[1]).resolve()
assert binding_path.name == "binding.json"
binding = json.loads(binding_path.read_text())
assert binding["operation"] == "postlaunch_existing_training_cooperative_lock_protection"
assert binding["physical_gpu"] == 0
assert binding["gpu_uuid"] == "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
assert binding["source_commit"] == "07ef534a6e44f22bd7b2d083550ebd7823d1d3d3"
assert datetime.now(timezone.utc) < datetime.fromisoformat(binding["owner"]["deadline_at"])
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == binding["guardian_script_sha256"]
assert subprocess.check_output(
    ["git", "-C", binding["runtime_root"], "rev-parse", "HEAD"], text=True,
).strip() == binding["source_commit"]
identity(binding)
state_path = binding_path.parent / "state.json"
guardian_pid = os.getpid()
guardian_start = starttime(guardian_pid)
handles = []
pidfd = None
lock_records = []


def state(status, **details):
    value = {
        "status": status, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "operation": binding["operation"],
        "binding_sha256": hashlib.sha256(binding_path.read_bytes()).hexdigest(),
        "guardian_pid": guardian_pid, "guardian_starttime": guardian_start,
        "trainer_pid": binding["trainer_pid"],
        "trainer_starttime": binding["trainer_starttime"],
        "runtime_root": binding["runtime_root"], "source_commit": binding["source_commit"],
        "physical_gpu": 0, "gpu_uuid": binding["gpu_uuid"],
        "locks": lock_records,
        "postlaunch_correction": True, "prelaunch_lock_check_proven": False,
        "GPU_model_or_NVML_calls": False, "signals_sent": False,
        "training_restarted": False,
        **details,
    }
    temporary = state_path.with_name("state." + str(guardian_pid) + ".tmp")
    with temporary.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, state_path)


result = "FAILED"
error = None
try:
    pidfd = os.pidfd_open(binding["trainer_pid"])
    identity(binding)
    for kind in ("training", "diagnostic", "exclusive"):
        path = Path("/tmp/cluster_project_gpu0_" + kind + ".lock")
        handle = path.open("r+b")  # Existing inode only; never create or unlink.
        handles.append(handle)
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        info = os.fstat(handle.fileno())
        lock_records.append({
            "kind": kind, "path": str(path), "inode": info.st_ino,
            "device_major": os.major(info.st_dev), "device_minor": os.minor(info.st_dev),
        })
    identity(binding)
    table = Path("/proc/locks").read_text().splitlines()
    for record in lock_records:
        key = "%02x:%02x:%d" % (
            record["device_major"], record["device_minor"], record["inode"],
        )
        lines = [line for line in table if len(line.split()) > 5 and line.split()[5] == key]
        assert len(lines) == 1
        fields = lines[0].split()
        assert fields[1] == "FLOCK" and fields[3] == "WRITE"
        assert int(fields[4]) == guardian_pid
        record["kernel_lock_entry"] = lines[0]
    state("HOLDING", locks_acquired_at=datetime.now(timezone.utc).isoformat())
    watcher = select.poll()
    watcher.register(pidfd, select.POLLIN)
    while not watcher.poll(5000):
        identity(binding)
    result = "RELEASED"
except (FileNotFoundError, ProcessLookupError) as exc:
    exited = False
    if pidfd is not None:
        exit_check = select.poll()
        exit_check.register(pidfd, select.POLLIN)
        exited = bool(exit_check.poll(0))
    result = "RELEASED" if exited else "FAILED"
    error = type(exc).__name__ + ": " + str(exc)
except Exception as exc:
    error = type(exc).__name__ + ": " + str(exc)
finally:
    for handle in reversed(handles):
        handle.close()
    if pidfd is not None:
        os.close(pidfd)
    state(result, released_at=datetime.now(timezone.utc).isoformat(), error=error)
if result == "FAILED":
    raise SystemExit(1)
