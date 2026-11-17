"""Once-only CPU guardian startup; this program never launches a trainer."""
from datetime import datetime, timezone
from pathlib import Path
import base64
import hashlib
import json
import os
import socket
import subprocess
import sys
import time

assert socket.gethostname() == "dl04-MS-7E06"
packet = json.load(sys.stdin)
binding = packet["binding"]
stage = Path(packet["stage"])
assert str(stage) == "/data/songcl/Project/Cluster_project/pipeline/cooperative_guards/m230_20c15273"
assert binding["project"] == "cluster_project" and binding["experiment_id"] == "M230-HVD"
assert binding["owner"]["token"] == "20c15273b622479495bada469c5f3c99"
assert binding["postlaunch_correction"] is True and binding["prelaunch_lock_check_proven"] is False
assert datetime.now(timezone.utc) < datetime.fromisoformat(binding["owner"]["deadline_at"])
assert binding["trainer_pid"] == 2829477 and binding["trainer_starttime"] == "158248846"
assert binding["trainer_uid"] == os.getuid() == 1001
proc = Path("/proc") / str(binding["trainer_pid"])


def starttime(pid):
    text = (Path("/proc") / str(pid) / "stat").read_text()
    return text[text.rfind(")") + 2:].split()[19]


def trainer():
    assert starttime(binding["trainer_pid"]) == binding["trainer_starttime"]
    assert proc.stat().st_uid == os.getuid() == binding["trainer_uid"]
    assert os.readlink(proc / "cwd") == binding["runtime_root"]
    assert os.readlink(proc / "fd/1") == binding["trainer_log"]
    assert [x.decode() for x in (proc / "cmdline").read_bytes().split(b"\0") if x] == binding["trainer_argv"]


trainer()
assert subprocess.check_output(
    ["git", "-C", binding["runtime_root"], "rev-parse", "HEAD"], text=True,
).strip() == binding["source_commit"]
script = base64.b64decode(packet["script_base64"])
assert hashlib.sha256(script).hexdigest() == binding["guardian_script_sha256"]
assert not stage.exists(), "Existing stage/start must reconcile; never replay"
assert not Path("/data/songcl/Project/Cluster_project/pipeline/cooperative_guards/m230_12e364dc").exists()
for record in binding["expected_existing_lockfiles"]:
    info = Path(record["path"]).stat()
    assert info.st_ino == record["inode"]
    assert os.major(info.st_dev) == record["device_major"]
    assert os.minor(info.st_dev) == record["device_minor"]
stage.parent.mkdir(parents=True, exist_ok=True)
stage.mkdir()
code = stage / "guardian.py"
binding_path = stage / "binding.json"
with code.open("xb") as stream:
    stream.write(script)
with binding_path.open("x") as stream:
    json.dump(binding, stream, indent=2)
    stream.write("\n")
trainer()
assert datetime.now(timezone.utc) < datetime.fromisoformat(binding["owner"]["deadline_at"])
with (stage / "guardian_stdout.log").open("ab", buffering=0) as out:
    child = subprocess.Popen(
        ["/usr/bin/python3", "-B", str(code), str(binding_path)],
        cwd=stage, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
        start_new_session=True,
    )
spawn = {
    "guardian_pid": child.pid, "guardian_starttime": starttime(child.pid),
    "recorded_at": datetime.now(timezone.utc).isoformat(),
}
with (stage / "spawn.json").open("x") as stream:
    json.dump(spawn, stream, indent=2)
    stream.write("\n")
state = None
for _ in range(50):
    if (stage / "state.json").exists():
        state = json.loads((stage / "state.json").read_text())
        break
    if child.poll() is not None:
        break
    time.sleep(.2)
if state is None or state.get("status") != "HOLDING":
    print(json.dumps({
        "stage": str(stage), "spawn": spawn, "binding": binding, "state": state,
        "stderr_tail": (stage / "guardian_stdout.log").read_text(errors="replace")[-2000:],
        "requires_reconciliation": True,
    }))
    raise SystemExit(2)
assert state["guardian_pid"] == spawn["guardian_pid"]
assert state["guardian_starttime"] == spawn["guardian_starttime"]
assert child.poll() is None
assert starttime(child.pid) == spawn["guardian_starttime"]
trainer()
assert len(state["locks"]) == 3 and state["trainer_pid"] == binding["trainer_pid"]
table = Path("/proc/locks").read_text().splitlines()
live_locks = []
for record in state["locks"]:
    info = Path(record["path"]).stat()
    assert info.st_ino == record["inode"]
    key = "%02x:%02x:%d" % (record["device_major"], record["device_minor"], record["inode"])
    rows = [line for line in table if len(line.split()) > 5 and line.split()[5] == key]
    assert len(rows) == 1
    fields = rows[0].split()
    assert fields[1] == "FLOCK" and fields[3] == "WRITE" and int(fields[4]) == child.pid
    live_locks.append(rows[0])
assert child.poll() is None
print(json.dumps({
    "stage": str(stage), "spawn": spawn, "binding": binding, "state": state,
    "live_lock_table": live_locks, "live_three_locks_confirmed": True,
    "trainer_unchanged": True, "CPU_guardian_only": True, "training_launches": 0,
    "signals_sent": False, "postlaunch_correction": True,
    "prelaunch_lock_check_proven": False,
}))
