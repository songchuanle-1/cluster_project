"""One-shot foreground Linux CPU proof of the actual PATH/direct-Popen route.

This runner only creates an isolated project-local CPU fixture. It cannot
render production, touch original project locks, run a real train.py, use CUDA,
signal a process, delete a marker, change SERVERS or activate production.
"""
from datetime import datetime, timezone
import argparse
import errno
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pwd
import shlex
import socket
import stat
import subprocess
import sys
import time
from types import ModuleType


PROJECT = Path("/data/songcl/Project/Cluster_project")
BASE_CONDA = PROJECT / "pipeline/runtime/server4_conda_4ca73fba.sh"
BASE_CONDA_SHA = "6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
REAL_PYTHON = "/home/songcl/.conda/envs/project_cluster/bin/python"
REAL_PREFIX = "/home/songcl/.conda/envs/project_cluster"
CONFIG = "configs/Quard/ctf_hcg_csort_psc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psc.yaml"
EXACT_ARGS = ["tools/train.py", CONFIG, "--gpu_ids", "0", "--num_gpus", "1"]
PACKET = ("cpu_proof_runner.py", "entry_factory.py", "lock_core.py")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_new(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def finish(process, timeout=12):
    try:
        out, err = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # Preserve the uncertain PID. Never kill, terminate or replay a proof.
        raise RuntimeError("CPU proof uncertain; preserve PID " + str(process.pid))
    return {"pid": process.pid, "rc": process.returncode, "stdout": out, "stderr": err}


def command(argv, **kwargs):
    return finish(subprocess.Popen(argv, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, **kwargs))


def wait_file(path, seconds=8):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        if Path(path).is_file():
            return json.loads(Path(path).read_text(encoding="utf-8"))
        time.sleep(0.025)
    raise RuntimeError("CPU handshake absent; no signal/retry: " + str(path))


def lock_identity(path):
    metadata = Path(path).stat()
    return {"path": str(path), "dev": metadata.st_dev, "ino": metadata.st_ino}


def kernel_records(specifications, pid):
    wanted = {(os.major(item["dev"]), os.minor(item["dev"]), item["ino"])
              for item in specifications}
    found = []
    for line in Path("/proc/locks").read_text().splitlines():
        parts = line.split()
        if len(parts) < 8 or parts[1:4] != ["FLOCK", "ADVISORY", "WRITE"]:
            continue
        major, minor, inode = parts[5].split(":")
        identity = (int(major, 16), int(minor, 16), int(inode))
        if identity in wanted and int(parts[4]) == pid:
            found.append(line)
    assert len(found) == 3, {"kernel_records": found, "expected_pid": pid}
    return found


def assert_locks_free(specifications):
    handles = []
    try:
        for item in specifications:
            handle = os.open(item["path"], os.O_RDWR | os.O_NOFOLLOW)
            handles.append(handle)
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        for handle in reversed(handles):
            os.close(handle)


def sentinel_source(ready, release, lock_paths):
    return f'''import fcntl,json,os,stat,sys,time
from pathlib import Path
with open({str(ready.parent / "sentinel-entry-audit.jsonl")!r},"a") as audit:
 audit.write(json.dumps({{"pid":os.getpid(),"argv":sys.argv}})+"\\n")
locks={lock_paths!r}
held=[]
for name in os.listdir("/proc/self/fd"):
 try:
  fd=int(name);p=os.readlink("/proc/self/fd/"+name)
  if p in locks:
   s=os.fstat(fd)
   held.append({{"path":p,"fd":fd,"dev":s.st_dev,"ino":s.st_ino,
                 "cloexec":bool(fcntl.fcntl(fd,fcntl.F_GETFD)&fcntl.FD_CLOEXEC)}})
 except OSError:pass
assert len(held)==3 and {{x["path"] for x in held}}==set(locks)
assert all(not x["cloexec"] for x in held)
with open({str(ready)!r},"x") as out:
 json.dump({{"pid":os.getpid(),"ppid":os.getppid(),"uid":os.getuid(),
            "argv":sys.argv,"cwd":os.getcwd(),"executable":sys.executable,
            "held":held,"CPU_only_no_model_GPU":True}},out)
deadline=time.monotonic()+25
while not Path({str(release)!r}).exists():
 if time.monotonic()>deadline:raise RuntimeError("CPU release handshake expired naturally")
 time.sleep(.025)
'''


def shim_source(entry):
    # Same original conda helper and post-activate priority mechanism as draft.
    return f'''#!/usr/bin/env bash
source {shlex.quote(str(BASE_CONDA))} || return "$?"
declare -F __conda_activate >/dev/null || return 126
_psc_bin={shlex.quote(str(Path(entry).parent))}
_psc_prepend_python() {{
 [[ "${{CONDA_PREFIX:-}}" == {shlex.quote(REAL_PREFIX)} ]] || return 126
 unset -f python 2>/dev/null || return 126
 unalias python 2>/dev/null || :
 export PATH="$_psc_bin:$PATH"
 hash -r
 [[ "$(type -P python)" == "$_psc_bin/python" && "$(type -t python)" == file ]] || return 126
}}
conda() {{
 [[ "$#" == 2 && "$1" == activate && "$2" == project_cluster ]] || return 126
 __conda_activate "$@" || return "$?"
 _psc_prepend_python
}}
return 0
'''


def shell_prefix(shim):
    return ("source " + shlex.quote(str(shim)) +
            " && conda activate project_cluster && ")


def start_canonical(shim, root, args, launch_record, log, env_extra=None):
    # The actual delegated outer Python performs the canonical direct Popen.
    # No shell=True, pass_fds, helper call or inherited parent lock FDs.
    program = f'''import json,os,pathlib,subprocess,sys
root=pathlib.Path({str(root)!r})
env=os.environ.copy()
env["PYTHONPATH"]=str(root)+":"+str(root/"framework/lib")+":"+env.get("PYTHONPATH","")
pyver=".".join(str(value) for value in sys.version_info[:2])
env["LD_LIBRARY_PATH"]=env["CONDA_PREFIX"]+"/lib:"+env["CONDA_PREFIX"]+"/lib/python"+pyver+"/site-packages/torch/lib:"+env.get("LD_LIBRARY_PATH","")
env["TMPDIR"]={str(root / "ipc")!r}
with open({str(log)!r},"ab",buffering=0) as out:
 proc=subprocess.Popen(["python"]+{args!r},cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
with open({str(launch_record)!r},"x") as out:
 json.dump({{"pid":proc.pid,"outer_pid":os.getpid(),"PATH":env["PATH"],"python_executable":sys.executable}},out)
raise SystemExit(proc.wait())
'''
    return subprocess.Popen(
        ["/bin/bash", "-c", shell_prefix(shim) + "python -B -c " + shlex.quote(program)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env={**os.environ, **(env_extra or {})})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--request-sha256", required=True)
    args = parser.parse_args()
    request_path = Path(args.request).resolve()
    assert sha(request_path) == args.request_sha256
    request = json.loads(request_path.read_text(encoding="utf-8"))
    assert sys.flags.isolated and sys.dont_write_bytecode, "Use /usr/bin/python3 -I -B"
    assert request["kind"] == "CPU_PROOF_ONLY" and request["execution_authorized"] is True
    assert request["production_activation_authorized"] is False
    assert socket.gethostname() == "dl04-MS-7E06"
    assert os.getuid() == os.geteuid() == 1001
    assert pwd.getpwuid(os.getuid()).pw_name == "songcl"
    stage = request_path.parent
    assert stage.parent == PROJECT / "pipeline/runtime"
    assert stage.name == "psc_path_cpu_" + request["owner"]["token"][:8]
    assert stage.resolve() == stage
    assert request["owner"]["thread_id"] == "01a159c5-29ab-7a22-ba7f-e79174757253"
    deadline = datetime.fromisoformat(request["owner"]["deadline_at"])
    assert (deadline - datetime.now(timezone.utc)).total_seconds() >= 100
    assert request["proof_only_paths_must_stay_inside_stage"] is True
    assert stat.S_IMODE(stage.stat().st_mode) == 0o700
    assert not (stage / "cpu_proof_result.json").exists()
    assert not (stage / "fixture").exists(), "Never replay an existing/uncertain fixture"
    assert sha(BASE_CONDA) == BASE_CONDA_SHA
    assert sys.version_info >= (3, 9)
    for filename in PACKET:
        assert sha(stage / filename) == request["files"][filename]
    core = (stage / "lock_core.py").read_bytes()
    factory = ModuleType("psc_entry_factory")
    exec(compile((stage / "entry_factory.py").read_bytes(),
                 str(stage / "entry_factory.py"), "exec"), factory.__dict__)
    events = []
    fixture = stage / "fixture"
    fixture.mkdir(mode=0o700)
    (fixture / "tools").mkdir()
    (fixture / "ipc").mkdir()
    config = fixture / CONFIG
    config.parent.mkdir(parents=True)
    config.write_text("cpu_fixture_only: true\n")
    locks = []
    for label in ("training", "diagnostic", "exclusive"):
        path = fixture / ("proof-" + label + ".lock")
        with path.open("xb"):
            pass
        locks.append(lock_identity(path))
    ready, release = fixture / "sentinel-ready.json", fixture / "release"
    train = fixture / "tools/train.py"
    train.write_text(sentinel_source(ready, release, [item["path"] for item in locks]))
    source_files = {"tools/train.py": sha(train)}
    for index in range(7):
        path = fixture / ("fixture_source_" + str(index) + ".py")
        path.write_text("# Isolated CPU proof fixture; no model imports.\n")
        source_files[path.name] = sha(path)
    git_env = {
        "PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": "/dev/null", "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_AUTHOR_NAME": "CPU proof", "GIT_AUTHOR_EMAIL": "proof@invalid",
        "GIT_COMMITTER_NAME": "CPU proof", "GIT_COMMITTER_EMAIL": "proof@invalid",
    }
    for tail in (["init", "-q"], ["add", "--", "tools/train.py", CONFIG,
                                 *[key for key in source_files if key != "tools/train.py"]],
                 ["-c", "commit.gpgsign=false", "commit", "-qm", "Isolated CPU fixture"]):
        observation = command(["/usr/bin/git", "-C", str(fixture), *tail], env=git_env)
        assert observation["rc"] == 0, observation
    head = command(["/usr/bin/git", "-C", str(fixture), "rev-parse", "HEAD"], env=git_env)
    assert head["rc"] == 0
    base_binding = {
        "kind": "cpu-proof", "hostname": "dl04-MS-7E06", "uid": 1001,
        "runtime_root": str(fixture), "source_commit": head["stdout"].strip(),
        "conda_prefix": REAL_PREFIX, "python": REAL_PYTHON,
        "python_realpath": str(Path(REAL_PYTHON).resolve(strict=True)),
        "python_sha256": sha(Path(REAL_PYTHON).resolve()),
        "runtime_config_sha256": sha(config),
        "activation_receipt_sha256": args.request_sha256,
        "source_files": source_files, "argv": EXACT_ARGS, "lock_files": locks,
    }
    for item in locks:
        assert Path(item["path"]).is_relative_to(stage)
        assert "/tmp/cluster_project_gpu0_" not in item["path"]
    entries = []

    def make_entry(label, changes=None):
        location = stage / label
        binding = {**base_binding, **(changes or {}), "stage": str(location),
                   "entry": str(location / "bin/python"),
                   "one_shot_marker": str(location / "train-consumed.json")}
        metadata = factory.render_entry(location, binding, core, "cpu-proof")
        shim = location / "conda_source.sh"
        shim.write_text(shim_source(metadata["entry"]))
        shim.chmod(0o600)
        metadata["shim"] = str(shim)
        entries.append(metadata)
        return metadata, binding

    entry, binding = make_entry("accepted")
    shim = Path(entry["shim"])
    resolution = command(["/bin/bash", "-c", shell_prefix(shim) +
                          'printf "%s\\n" "$(type -t python)" "$(type -P python)"'])
    assert resolution["rc"] == 0, resolution
    assert resolution["stdout"].splitlines() == ["file", entry["entry"]]
    events.append({"check": "actual_conda_activate_then_real_PATH_executable",
                   "passed": True, "observation": resolution})
    assert_locks_free(locks)
    active = start_canonical(shim, fixture, EXACT_ARGS, fixture / "launch.json",
                             fixture / "accepted.log")
    actual = wait_file(ready)
    launch = wait_file(fixture / "launch.json")
    audit = fixture / "sentinel-entry-audit.jsonl"
    initial_audit_sha = sha(audit)
    assert len(audit.read_text().splitlines()) == 1
    assert actual["pid"] == launch["pid"]
    assert actual["uid"] == 1001 and actual["cwd"] == str(fixture)
    assert actual["argv"] == ["tools/train.py", *EXACT_ARGS[1:]]
    assert Path(actual["executable"]).resolve() == Path(REAL_PYTHON).resolve()
    assert len(actual["held"]) == 3 and all(not item["cloexec"] for item in actual["held"])
    kernel = kernel_records(locks, actual["pid"])
    contention = []
    for item in locks:
        descriptor = os.open(item["path"], os.O_RDWR | os.O_NOFOLLOW)
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                assert error.errno in (errno.EAGAIN, errno.EACCES)
                contention.append({"path": item["path"], "errno": error.errno})
            else:
                raise AssertionError("Kernel lock did not contend")
        finally:
            os.close(descriptor)
    contender, _ = make_entry("contender")
    failed = start_canonical(Path(contender["shim"]), fixture, EXACT_ARGS,
                             fixture / "contender-launch.json", fixture / "contender.log")
    refusal = finish(failed)
    assert refusal["rc"] == 75, refusal
    assert sha(audit) == initial_audit_sha, "Contender entered CPU target unexpectedly"
    assert not (Path(contender["stage"]) / "train-consumed.json").exists()
    release.write_text("Normal CPU sentinel release; no signal.\n")
    accepted_exit = finish(active)
    assert accepted_exit["rc"] == 0, accepted_exit
    assert_locks_free(locks)
    for item in locks:
        assert lock_identity(item["path"]) == item
    events.append({"check": "actual_direct_Popen_exec_FDs_three_kernel_FLOCK_contention_natural_release",
                   "passed": True, "sentinel": actual, "launcher": launch,
                   "kernel_records": kernel, "independent_contention": contention,
                   "competing_direct_Popen": refusal, "natural_exit": accepted_exit})
    replay = start_canonical(shim, fixture, EXACT_ARGS, fixture / "replay-launch.json",
                             fixture / "replay.log")
    replay_result = finish(replay)
    assert replay_result["rc"] == 126, replay_result
    assert sha(audit) == initial_audit_sha, "Consumed entry executed CPU target"
    assert_locks_free(locks)
    events.append({"check": "consumed_entry_refuses_after_locks_naturally_free",
                   "passed": True, "observation": replay_result})
    negative_cases = [
        ("GPU1", [*EXACT_ARGS[:3], "1", *EXACT_ARGS[4:]], {}),
        ("wrong_config", ["tools/train.py", "other.yaml", *EXACT_ARGS[2:]], {}),
        ("duplicate_GPU", EXACT_ARGS + ["--gpu_ids", "0"], {}),
        ("resume", EXACT_ARGS + ["--resume", "unused.pth"], {}),
        ("python_B", ["-B", *EXACT_ARGS], {}),
        ("clustered_python_module", ["-Bm", "tools.train", *EXACT_ARGS[1:]], {}),
        ("absolute_train", [str(train), *EXACT_ARGS[1:]], {}),
        ("wrong_source", EXACT_ARGS, {"source_commit": "0" * 40}),
        ("wrong_config_hash", EXACT_ARGS, {"runtime_config_sha256": "0" * 64}),
        ("wrong_UID", EXACT_ARGS, {"uid": 1002}),
    ]
    for label, argv, changes in negative_cases:
        rejected, _ = make_entry("reject-" + label, changes)
        process = start_canonical(Path(rejected["shim"]), fixture, argv,
                                  fixture / (label + "-launch.json"),
                                  fixture / (label + ".log"))
        result = finish(process)
        assert result["rc"] != 0, (label, result)
        assert sha(audit) == initial_audit_sha, (label, "CPU target entered")
        assert not (Path(rejected["stage"]) / "train-consumed.json").exists()
        assert_locks_free(locks)
        events.append({"check": label + "_refused_before_sentinel",
                       "passed": True, "observation": result})
    for position in range(3):
        partial, _ = make_entry("partial-contention-" + str(position))
        descriptor = os.open(locks[position]["path"], os.O_RDWR | os.O_NOFOLLOW)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            process = start_canonical(Path(partial["shim"]), fixture, EXACT_ARGS,
                                      fixture / ("partial-" + str(position) + "-launch.json"),
                                      fixture / ("partial-" + str(position) + ".log"))
            result = finish(process)
            assert result["rc"] == 75, result
            assert sha(audit) == initial_audit_sha
        finally:
            os.close(descriptor)
        assert_locks_free(locks)
        events.append({"check": "lock_" + str(position) + "_busy_partial_acquisitions_released",
                       "passed": True, "observation": result})
    expected = ["a b", "*", "$literal", ""]
    normal_code = ("import json,sys;assert sys.argv[1:]==" + repr(expected) +
                   ";print(json.dumps({'argv':sys.argv[1:],'python':sys.executable}))")
    normal = command(["/bin/bash", "-c", shell_prefix(shim) + "python -B -c " +
                      shlex.quote(normal_code) + " " + shlex.join(expected)])
    assert normal["rc"] == 0 and json.loads(normal["stdout"])["argv"] == expected
    stdin = subprocess.Popen(["/bin/bash", "-c", shell_prefix(shim) +
                              "python -B - " + shlex.join(expected)],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
    try:
        stdout, stderr = stdin.communicate(normal_code + "\n", timeout=8)
    except subprocess.TimeoutExpired:
        raise RuntimeError("CPU stdin uncertain PID " + str(stdin.pid))
    assert stdin.returncode == 0 and json.loads(stdout)["argv"] == expected
    assert sha(audit) == initial_audit_sha
    assert_locks_free(locks)
    events.append({"check": "original_conda_Python_c_and_stdin_exact_argv_passthrough",
                   "passed": True, "c_observation": normal,
                   "stdin_observation": {"pid": stdin.pid, "rc": stdin.returncode,
                                         "stdout": stdout, "stderr": stderr}})
    assert datetime.now(timezone.utc) < deadline
    assert sha(BASE_CONDA) == BASE_CONDA_SHA
    assert all(sha(stage / name) == request["files"][name] for name in PACKET)
    assert_locks_free(locks)
    result = {
        "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "passed": True, "kind": "CPU_PROOF_ONLY", "request_sha256": args.request_sha256,
        "owner": request["owner"], "hostname": socket.gethostname(), "uid": os.getuid(),
        "stage": str(stage), "fixture_source_commit": head["stdout"].strip(),
        "byte_identical_core_sha256": hashlib.sha256(core).hexdigest(),
        "events": events, "entry_artifacts": entries,
        "production_source_runtime_or_locks_used": False,
        "model_GPU_training_signals_or_production_activation": False,
        "production_runtime_head": "NOT_CHECKED_NOT_DEPLOYED_BY_THIS_PROOF",
        "proof_fixture_does_not_validate_real_PSC_source": True,
        "independent_review": "PENDING_ROOT_PEER_REVIEW",
    }
    save_new(stage / "cpu_proof_result.json", result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
