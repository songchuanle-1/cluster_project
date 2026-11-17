"""Stdlib system-Python supervisor source; default NOP, never SSH.

Root supplies reviewed source/metadata through stdin. No persistent remote
files are produced. Own diagnostic cleanup uses identity-bound pidfds only.
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import sys
import tempfile
import time

OWNER_TOKEN = "4ecb5020c4c54abeb26dc874ed90080e"
DEADLINE = dt.datetime.fromisoformat("2026-11-10T02:06:58.009358+00:00")
ROOT = "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
PYTHON = "/home/songcl/.conda/envs/project_cluster/bin/python"
INPUT_CAP = 2 * 1024 * 1024
OUTPUT_CAP = 32 * 1024 * 1024
OUTPUTS = {}
SIGNALS = []
WORKERS = {}
HELPERS = {}
CARRIER = None
EVENT_OFFSET = 0
EVENT_PENDING = b""


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def identity(pid):
    try:
        text = Path("/proc/%d/stat" % pid).read_text()
        fields = text.rsplit(")", 1)[1].split()
        return {"pid": pid, "start_ticks": fields[19], "ppid": int(fields[1]),
                "pgrp": int(fields[2]), "uid": Path("/proc/%d" % pid).stat().st_uid}
    except (FileNotFoundError, ProcessLookupError):
        return {"pid": pid, "start_ticks": None, "absent": True}


def own_handle(pid, expected=None):
    before = identity(pid)
    if expected is not None and before.get("start_ticks") != expected.get("start_ticks"):
        return {"identity": expected, "pidfd": None, "certainty": "identity_changed_no_signal"}
    try:
        fd = os.pidfd_open(pid, 0)
    except ProcessLookupError:
        return {"identity": before, "pidfd": None, "certainty": "absent_before_pidfd"}
    after = identity(pid)
    if after.get("start_ticks") != before.get("start_ticks"):
        os.close(fd)
        return {"identity": before, "pidfd": None, "certainty": "identity_changed_no_signal"}
    return {"identity": before, "pidfd": fd, "certainty": "owned_identity_bound"}


def anonymous(name, contents=b""):
    fd = os.memfd_create("m234_trace_4ecb_" + name, 0)
    os.set_inheritable(fd, True)
    if contents:
        require(os.write(fd, contents) == len(contents), "SHORT_MEMFD_WRITE")
        os.lseek(fd, 0, os.SEEK_SET)
    return fd


def observe_workers():
    global EVENT_OFFSET, EVENT_PENDING
    descriptor = OUTPUTS["event_parent"]["fd"]
    size = min(os.fstat(descriptor).st_size, OUTPUTS["event_parent"]["cap"])
    data = os.pread(descriptor, max(0, size - EVENT_OFFSET), EVENT_OFFSET)
    EVENT_OFFSET += len(data)
    EVENT_PENDING += data
    lines = EVENT_PENDING.split(b"\n")
    EVENT_PENDING = lines.pop()
    candidate_rows = []
    for line in lines:
        try:
            row = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            continue
        if row.get("stage") not in {"worker.fork_captured", "readonly_helper.started"}:
            continue
        candidate_rows.append(row)
    # A child can reach bootstrap even if its parent fails before writing the
    # parent-side capture row. These dedicated owned FDs supply a second path.
    for worker_id in range(4):
        if worker_id in WORKERS:
            continue
        descriptor = OUTPUTS["event_worker_%d" % worker_id]["fd"]
        first = os.pread(descriptor, min(16384, os.fstat(descriptor).st_size), 0).split(b"\n", 1)[0]
        if first:
            try:
                row = json.loads(first)
                if row.get("stage") == "worker.after_fork_before_bootstrap":
                    candidate_rows.append(row)
            except (ValueError, UnicodeDecodeError):
                pass
    for row in candidate_rows:
        expected = row.get("identity", {})
        if row.get("stage") == "readonly_helper.started":
            if "uname_p" in HELPERS:
                continue
            if expected.get("uid") == 1001 and expected.get("ppid") == CARRIER["identity"]["pid"]:
                handle = own_handle(expected["pid"], expected)
                if handle["identity"].get("pgrp") == CARRIER["identity"]["pid"]:
                    HELPERS["uname_p"] = handle
                elif handle["pidfd"] is not None:
                    os.close(handle["pidfd"])
            continue
        worker_id = row.get("worker_id")
        if type(worker_id) is not int or worker_id not in range(4) or worker_id in WORKERS:
            continue
        # Evidence comes from our exact carrier's parent-only FD. Validate
        # UID/PPID/process-group before opening a stable pidfd for later use.
        if expected.get("uid") != 1001 or expected.get("ppid") != CARRIER["identity"]["pid"]:
            WORKERS[worker_id] = {"identity": expected, "pidfd": None,
                                  "certainty": "unexpected_owner_no_signal"}
            continue
        handle = own_handle(expected["pid"], expected)
        now = handle["identity"]
        if now.get("pgrp") != CARRIER["identity"]["pid"]:
            if handle["pidfd"] is not None:
                os.close(handle["pidfd"])
            handle.update(pidfd=None, certainty="unexpected_process_group_no_signal")
        WORKERS[worker_id] = handle


def pidfd_exited(handle):
    if handle.get("pidfd") is None:
        return False
    import select
    return bool(select.select([handle["pidfd"]], [], [], 0)[0])


def signal_own(handle, signum, reason):
    if handle.get("pidfd") is None or handle.get("certainty") != "owned_identity_bound":
        return False
    if pidfd_exited(handle):
        return False
    try:
        signal.pidfd_send_signal(handle["pidfd"], signum)
    except ProcessLookupError:
        return False
    SIGNALS.append({"identity": handle["identity"], "signal": int(signum),
                    "method": "pidfd_send_signal", "reason": reason})
    return True


def carrier_wait():
    if "exitcode" in CARRIER:
        return CARRIER["exitcode"]
    try:
        pid, status = os.waitpid(CARRIER["identity"]["pid"], os.WNOHANG)
    except ChildProcessError:
        CARRIER["wait_uncertain"] = True
        return None
    if pid:
        CARRIER["exitcode"] = os.waitstatus_to_exitcode(status)
    return CARRIER.get("exitcode")


def pause_observing(seconds):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        observe_workers()
        carrier_wait()
        time.sleep(min(0.025, max(0, until - time.monotonic())))


def bounded_cleanup(reason):
    observe_workers()
    if carrier_wait() is None:
        signal_own(CARRIER, signal.SIGUSR1, reason + ":COOPERATIVE_REQUEST")
    # Carrier sets done_event + None and joins, then may itself clean its
    # captured workers by pidfd. Let that path run before outer escalation.
    pause_observing(9)
    for signum in (signal.SIGTERM, signal.SIGKILL):
        observe_workers()
        for handle in list(WORKERS.values()) + list(HELPERS.values()):
            signal_own(handle, signum, reason + ":OWN_WORKER_ESCALATION")
        if carrier_wait() is None:
            signal_own(CARRIER, signum, reason + ":OWN_CARRIER_ESCALATION")
        pause_observing(2)


def read_small(path, maximum):
    try:
        with open(path, "rb") as stream:
            return stream.read(maximum).decode("utf-8", "replace")
    except (FileNotFoundError, PermissionError):
        return ""


def resident_kib(pid):
    for line in read_small("/proc/%d/status" % pid, 8192).splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    return 0


def capacity_observation(packet):
    values = {}
    for row in read_small("/proc/meminfo", 8192).splitlines():
        if row.startswith(("MemAvailable:", "SwapFree:", "Shmem:")):
            values[row.split(":", 1)[0]] = int(row.split()[1])
    shm = os.statvfs("/dev/shm")
    available_shm = shm.f_bavail * shm.f_frsize
    affinity = sorted(os.sched_getaffinity(0))
    require(values.get("MemAvailable", 0) >= packet["min_mem_available_kib"],
            "CURRENT_MEMAVAILABLE_BELOW_REVIEWED_CPU_DIAGNOSTIC_BUDGET")
    require(available_shm >= packet["min_shm_available_bytes"],
            "CURRENT_SHARING_CAPACITY_BELOW_REVIEWED_BUDGET")
    require(len(affinity) >= 4, "CPU_AFFINITY_CANNOT_SUPPORT_ORIGINAL_FOUR_WORKERS")
    membership = read_small("/proc/self/cgroup", 8192)
    group = next((row.split(":", 2)[2] for row in membership.splitlines() if row.startswith("0::")), None)
    limits = []
    if group is not None:
        path = (Path("/sys/fs/cgroup") / group.lstrip("/")).resolve()
        root = Path("/sys/fs/cgroup")
        require(path.is_relative_to(root), "CGROUP_PATH")
        for depth in range(10):
            memory_max = read_small(path / "memory.max", 128).strip()
            memory_current = read_small(path / "memory.current", 128).strip()
            pids_max = read_small(path / "pids.max", 128).strip()
            pids_current = read_small(path / "pids.current", 128).strip()
            limits.append({"path": str(path), "memory.max": memory_max, "memory.current": memory_current,
                           "pids.max": pids_max, "pids.current": pids_current})
            if memory_max.isdigit() and memory_current.isdigit():
                require(int(memory_max) - int(memory_current) >= packet["min_cgroup_memory_headroom_bytes"],
                        "CGROUP_MEMORY_HEADROOM_BELOW_REVIEWED_BUDGET")
            if pids_max.isdigit() and pids_current.isdigit():
                require(int(pids_max) - int(pids_current) >= 8, "CGROUP_PIDS_HEADROOM")
            if path == root:
                break
            path = path.parent
        else:
            raise RuntimeError("CGROUP_ANCESTOR_BOUND")
    return {"meminfo_kib": values, "shm_available_bytes": available_shm,
            "affinity": affinity, "loadavg": read_small("/proc/loadavg", 256),
            "cgroup_membership": membership, "cgroup_ancestor_limits": limits}


def main():
    global CARRIER
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-reviewed", action="store_true")
    args = parser.parse_args()
    if not args.execute_reviewed:
        print(json.dumps({"status": "DEFAULT_NOP_NO_PROCESSES_OR_REMOTE_WRITES"}))
        return
    raw = sys.stdin.buffer.read(INPUT_CAP + 1)
    require(len(raw) <= INPUT_CAP, "INPUT_BYTE_CAP")
    payload = json.loads(raw)
    packet = payload["packet"]
    source = payload["carrier_source"].encode("utf-8")
    require(payload.get("execute_root") is True and packet["owner"]["token"] == OWNER_TOKEN,
            "ROOT_EXECUTION_AND_CURRENT_OWNER_REQUIRED")
    require(packet.get("execution_authorized") is True and packet.get("status") ==
            "READY_AFTER_ACTUAL_CONSTRUCTOR_AND_PEER_REVIEW", "UNREADY_PACKET")
    require(hashlib.sha256(source).hexdigest() == packet["carrier_sha256"], "CARRIER_HASH")
    require(Path.cwd() == Path(ROOT) and os.getuid() == os.geteuid() == 1001, "RUNTIME_UID_IDENTITY")
    require(hasattr(os, "memfd_create") and hasattr(os, "pidfd_open") and
            hasattr(signal, "pidfd_send_signal"), "MEMFD_PIDFD_API_REQUIRED")
    wall_seconds = packet.get("supervisor_wall_seconds", 120)
    require(30 <= wall_seconds <= 180, "SUPERVISOR_WALL_BOUND")
    require((DEADLINE - dt.datetime.now(dt.timezone.utc)).total_seconds() > wall_seconds + 20,
            "INSUFFICIENT_LEASE_FOR_BOUNDED_OBSERVATION_AND_CLEANUP")
    require(1024 * 1024 <= packet.get("max_total_rss_kib", 0) <= 64 * 1024 * 1024,
            "EXPLICIT_SOFT_DIAGNOSTIC_RSS_BUDGET_REQUIRED")
    self_probe = os.pidfd_open(os.getpid(), 0)
    os.close(self_probe)
    capacity = capacity_observation(packet)
    ipc = tempfile.mkdtemp(prefix="m234_trace_4ecb5020_", dir="/tmp")
    packet["owned_ipc_directory"] = ipc
    for name in ["event_parent", "fault_parent"] + [
            "%s_worker_%d" % (kind, i) for kind in ("event", "fault") for i in range(4)]:
        OUTPUTS[name] = {"fd": anonymous(name), "cap": 2 * 1024 * 1024 if name.startswith("event") else 65536}
    OUTPUTS["status"] = {"fd": anonymous("status"), "cap": 65536}
    OUTPUTS["stdout"] = {"fd": anonymous("stdout"), "cap": 512 * 1024}
    OUTPUTS["stderr"] = {"fd": anonymous("stderr"), "cap": 512 * 1024}
    data_fds = {key: row["fd"] for key, row in OUTPUTS.items() if key not in {"stdout", "stderr"}}
    packet_fd = anonymous("packet", json.dumps(packet).encode())
    source_fd = anonymous("carrier_source", source)
    environment = dict(os.environ)
    environment.update(CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1",
                       TOKENIZERS_PARALLELISM="false", HF_HUB_OFFLINE="1",
                       TRANSFORMERS_OFFLINE="1", TMPDIR=ipc, GIT_OPTIONAL_LOCKS="0")
    began = time.monotonic()
    pid = os.fork()
    if pid == 0:
        try:
            os.setsid()
            os.dup2(OUTPUTS["stdout"]["fd"], 1)
            os.dup2(OUTPUTS["stderr"]["fd"], 2)
            argv = [PYTHON, "-B", "-X", "utf8", "/proc/self/fd/%d" % source_fd,
                    "--execute-reviewed", "--packet-fd", str(packet_fd),
                    "--fds-json", json.dumps(data_fds)]
            os.execve(PYTHON, argv, environment)
        except BaseException as exc:
            os.write(2, ("CARRIER_EXEC_FAILED:" + repr(exc)[:500]).encode())
            os._exit(126)
    CARRIER = {"identity": identity(pid), "pidfd": None, "certainty": "pidfd_capture_pending"}
    CARRIER = own_handle(pid)
    reason = None
    samples = []
    try:
        while True:
            observe_workers()
            code = carrier_wait()
            if code is not None:
                break
            if time.monotonic() - began >= wall_seconds or dt.datetime.now(dt.timezone.utc) >= DEADLINE:
                reason = "WALL_OR_LEASE_SOFT_BOUND"
                break
            for key, row in OUTPUTS.items():
                if os.fstat(row["fd"]).st_size > row["cap"]:
                    reason = "OUTPUT_BOUND:" + key
                    break
            total_rss = resident_kib(pid) + sum(
                resident_kib(handle["identity"]["pid"]) for handle in WORKERS.values()
                if handle.get("identity", {}).get("pid"))
            if total_rss > packet["max_total_rss_kib"]:
                reason = "OWN_DIAGNOSTIC_SOFT_RSS_BOUND"
            if len(samples) < 64 and (not samples or time.monotonic() - samples[-1]["monotonic"] >= 1):
                samples.append({"monotonic": time.monotonic(), "total_rss_kib": total_rss})
            if reason:
                break
            time.sleep(0.025)
        if reason:
            bounded_cleanup(reason)
        else:
            # Reap/finalize only our known descendants if the carrier failed
            # before reporting cleanup. Never select a PID by name or glob.
            observe_workers()
            if any(handle.get("pidfd") is not None and not pidfd_exited(handle)
                   for handle in list(WORKERS.values()) + list(HELPERS.values())):
                bounded_cleanup("KNOWN_OWN_WORKER_ALIVE_AFTER_CARRIER_EXIT")
    except BaseException as exc:
        reason = "SUPERVISOR_EXCEPTION:" + type(exc).__name__ + ":" + str(exc)[:240]
        bounded_cleanup(reason)
    output = {}
    for key, row in OUTPUTS.items():
        size = os.fstat(row["fd"]).st_size
        captured = os.pread(row["fd"], min(size, row["cap"]), 0)
        output[key] = {"bytes_written": size, "bytes_captured": len(captured),
                       "truncated": size > row["cap"], "sha256_captured": hashlib.sha256(captured).hexdigest(),
                       "base64": base64.b64encode(captured).decode("ascii")}
    worker_fates = [{"worker_id": worker_id, "identity": handle["identity"],
                     "ownership": handle["certainty"], "pidfd_exited": pidfd_exited(handle)}
                    for worker_id, handle in WORKERS.items()]
    try:
        os.rmdir(ipc)  # Empty own IPC directory only; never recursive delete.
        ipc_result = "REMOVED_EMPTY_OWN_IPC_DIRECTORY"
    except OSError as exc:
        ipc_result = "PRESERVED_NONEMPTY_OR_BUSY_OWN_IPC_DIRECTORY:" + str(exc)[:160]
    result = {"owner": packet["owner"], "kind": "REAL_TRAIN_DATA_STAGE_TRACE_SUPERVISION",
              "carrier_identity": CARRIER["identity"], "carrier_returncode": carrier_wait(),
              "carrier_pidfd_exited": pidfd_exited(CARRIER), "worker_fates": worker_fates,
              "readonly_helper_fates": [{"kind": key, "identity": row["identity"],
                                        "ownership": row["certainty"], "pidfd_exited": pidfd_exited(row)}
                                       for key, row in HELPERS.items()],
              "stop_reason": reason, "signals_sent": SIGNALS, "automatic_retry": False,
              "own_ipc_directory": ipc, "ipc_cleanup": ipc_result,
              "wall_seconds": time.monotonic() - began, "rss_observations": samples,
              "current_prelaunch_capacity": capacity,
              "captures": output, "root_cause": "UNKNOWN",
              "historical_crash_reproduced": False, "training_repair_verified": False,
              "finished_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    encoded = json.dumps(result, ensure_ascii=True).encode()
    require(len(encoded) <= OUTPUT_CAP, "TRANSPORT_BYTE_CAP")
    sys.stdout.buffer.write(encoded + b"\n")
    sys.stdout.buffer.flush()
    os._exit(0)  # Avoid unrelated interpreter/multiprocessing finalizers.


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        if CARRIER is not None:
            try:
                bounded_cleanup("SUPERVISOR_OUTER_EXCEPTION")
            except BaseException:
                pass
        failure = {"status": "SUPERVISOR_BLOCKED_OR_UNCERTAIN",
                   "error_type": type(exc).__name__, "error": str(exc)[:700],
                   "carrier": CARRIER["identity"] if CARRIER else None,
                   "workers": [{"worker_id": key, "identity": row["identity"],
                                "ownership": row["certainty"]} for key, row in WORKERS.items()],
                   "signals_sent": SIGNALS, "automatic_retry": False,
                   "root_cause": "UNKNOWN"}
        sys.stdout.write(json.dumps(failure) + "\n")
        sys.stdout.flush()
        os._exit(2)
