"""Byte-identical core for separately hash-bound PSC proof/production entries."""
import errno

import fcntl

import hashlib

import json

import os

from pathlib import Path

import socket

import stat

import subprocess

import sys
from datetime import datetime, timezone
from types import ModuleType

EXPECTED_OWNER = {'token': 'c1fe217800894083b65baac45f79aa83', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-14T01:52:47.538159+00:00', 'deadline_at': '2026-11-14T02:52:47.538159+00:00', 'context_sha256': 'e33442420ba4c77b839918c43c944153092f834b2d316bb8979f843d3cdf82a4', 'pending_sha256': '3d0bc5d2092b154a1acdb483f3d9185e95e9aa411b2089930f01dc1fd96875e6'}
DIRECT_FREE_GUARD_SOURCE = b'"""NOT_APPROVED source draft. Running this file always performs a NOP.\n\nFuture reviewed native_runtime.observe and production prelaunch/marker callers\nmay invoke require_direct_free_memory after their original identity/lock guards.\nThis file is not wired into any deployment, entry, launcher or native test.\n"""\nimport json\nimport subprocess\n\n\nclass ResourceRefused(RuntimeError):\n    pass\n\n\ndef require_direct_free_memory():\n    """Future native observation/prelaunch/locked marker guard; no signals."""\n    argv = ["/usr/bin/nvidia-smi", "-i", "0",\n            "--query-gpu=index,uuid,memory.free,memory.used,memory.total,utilization.gpu",\n            "--format=csv,noheader,nounits"]\n    child = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n                             env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})\n    try:\n        stdout, stderr = child.communicate(timeout=10)\n    except subprocess.TimeoutExpired:\n        raise ResourceRefused("Uncertain resource query; preserve child PID " +\n                              str(child.pid) + "; no signal or retry")\n    if child.returncode:\n        raise ResourceRefused("Resource query failed; no launch or marker consumption")\n    fields = [part.strip() for part in stdout.decode("utf-8").strip().split(",")]\n    if len(fields) != 6 or fields[:2] != ["0", "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"]:\n        raise ResourceRefused("Physical GPU0 identity or resource row mismatch")\n    free_mib = int(fields[2])\n    if free_mib < 20000:\n        raise ResourceRefused("Direct memory.free below unchanged 20000 MiB gate")\n    return {"index": 0, "uuid": fields[1], "memory_free_mib": free_mib,\n            "memory_used_mib": int(fields[3]), "memory_total_mib": int(fields[4]),\n            "utilization_percent": int(fields[5]),\n            "memory_free_queried_directly": True}\n\n\nif __name__ == "__main__":\n    print(json.dumps({"status": "DEFAULT_NOP_NOT_APPROVED_SOURCE_DRAFT",\n                      "resource_query_performed": False,\n                      "deployment_or_training_authorized": False}))\n'
DIRECT_FREE_GUARD_SHA256 = '1d48570e42ee34e012194ccf412e475a12608396f946e0eac27902907006c111'

def refuse(message, code=126):
    print("PSC PATH lock refusal: " + message, file=sys.stderr, flush=True)
    raise SystemExit(code)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def script_target(args):
    """Identify Python script/module mode without parsing -c/stdin contents."""
    index = 0
    while index < len(args):
        value = args[index]
        if value == "-" or value == "-c" or value.startswith("-c"):
            return None
        if value == "-m":
            return "module:" + args[index + 1] if index + 1 < len(args) else None
        if value.startswith("-m") and len(value) > 2:
            return "module:" + value[2:]
        if value == "--":
            return args[index + 1] if index + 1 < len(args) else None
        if value in ("-W", "-X", "--check-hash-based-pycs"):
            index += 2
            continue
        if value.startswith("-") and not value.startswith("--"):
            # CPython permits short-option clusters such as -Bm tools.train.
            # Do not misclassify those as harmless non-training script mode.
            for offset, option in enumerate(value[1:], 1):
                if option in ("c", "m"):
                    payload = value[offset + 1:]
                    if not payload and index + 1 < len(args):
                        payload = args[index + 1]
                    return "module:" + payload if option == "m" else None
                if option in ("W", "X"):
                    # The rest is an option value, not another Python flag.
                    if not value[offset + 1:]:
                        index += 1
                    break
        if not value.startswith("-"):
            return value
        index += 1
    return None

def is_training(target):
    if target is None:
        return False
    if target.startswith("module:"):
        return target[7:] in ("tools.train", "tools.train.py")
    return Path(target).name == "train.py"

def checked_file(path, expected_uid, *, regular=True):
    metadata = os.lstat(path)
    if stat.S_ISLNK(metadata.st_mode):
        refuse("symlink at protected file " + str(path))
    if regular and not stat.S_ISREG(metadata.st_mode):
        refuse("non-regular protected file " + str(path))
    if metadata.st_uid != expected_uid:
        refuse("protected file owner mismatch " + str(path))
    return metadata


def require_project_cap1():
    project = Path(BINDING["runtime_root"]).parent
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit() or int(proc.name) == os.getpid():
            continue
        try:
            if proc.stat().st_uid != BINDING["uid"]:
                continue
            raw = (proc / "cmdline").read_bytes()
            argv = [value.decode(errors="replace") for value in raw.split(b"\0") if value]
            # Handle direct scripts, -m and short option clusters using the reviewed parser.
            trainer = bool(argv) and (is_training(script_target(argv[1:])) or
                any(value == "tools/train.py" or value.endswith("/tools/train.py") for value in argv))
            cwd = os.readlink(proc / "cwd")
            same_project = cwd == str(project) or cwd.startswith(str(project) + "/")
            if trainer and same_project:
                refuse("Existing same-project trainer occupies cap1; preserve every job", 75)
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            refuse("Uncertain same-user process identity; preserve and refuse", 75)


def require_locked_direct_free():
    if hashlib.sha256(DIRECT_FREE_GUARD_SOURCE).hexdigest() != DIRECT_FREE_GUARD_SHA256:
        refuse("Direct-free helper source identity mismatch")
    module = ModuleType("cso_locked_direct_free_guard")
    exec(compile(DIRECT_FREE_GUARD_SOURCE, "reviewed_direct_memory_free_guard.py", "exec"), module.__dict__)
    measured = module.require_direct_free_memory()
    if measured["index"] != 0 or measured["uuid"] != BINDING["expected_gpu_uuid"]:
        refuse("Direct-free physical GPU0 identity mismatch")
    if measured["memory_free_mib"] < BINDING["required_free_memory_mib"]:
        refuse("Direct memory.free below unchanged 20000 MiB gate", 75)
    if datetime.now(timezone.utc) >= datetime.fromisoformat(EXPECTED_OWNER["deadline_at"]):
        refuse("Current foreground owner expired during direct-free query")
    return measured


def validate_training(args):
    # No proof/test/override environment is read by this branch.
    if BINDING["owner"] != EXPECTED_OWNER or BINDING["owner_deadline_at"] != EXPECTED_OWNER["deadline_at"]:
        refuse("Current six-field owner binding mismatch")
    generated, deadline = (datetime.fromisoformat(EXPECTED_OWNER[key]) for key in ("generated_at", "deadline_at"))
    if not generated <= datetime.now(timezone.utc) < deadline:
        refuse("Current foreground execution owner expired")
    if BINDING["physical_gpu"] != 0 or BINDING["max_project_tasks"] != 1 or BINDING["required_free_memory_mib"] != 20000:
        refuse("GPU0 cap1/direct-free resource contract mismatch")
    if BINDING["expected_gpu_uuid"] != "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c":
        refuse("GPU0 UUID binding mismatch")
    if BINDING["kind"] not in ("production", "cpu-proof"):
        refuse("disabled draft; no active production binding")
    if args != BINDING["argv"]:
        refuse("only the exact new PSC six-argument launch is permitted")
    if socket.gethostname() != BINDING["hostname"]:
        refuse("hostname mismatch")
    if os.getuid() != os.geteuid() or os.getuid() != BINDING["uid"]:
        refuse("UID mismatch")
    root = Path(BINDING["runtime_root"])
    if Path.cwd().resolve() != root or root.resolve() != root:
        refuse("runtime root mismatch")
    if Path(sys.argv[0]).resolve() != Path(BINDING["entry"]):
        refuse("wrapper location mismatch")
    checked_file(BINDING["entry"], BINDING["uid"])
    if os.environ.get("CONDA_PREFIX") != BINDING["conda_prefix"]:
        refuse("conda environment mismatch")
    if os.environ.get("CUDA_VISIBLE_DEVICES") not in (None, "0"):
        refuse("inherited CUDA visibility conflicts with physical GPU0")
    real_python = Path(BINDING["python"]).resolve(strict=True)
    if str(real_python) != BINDING["python_realpath"]:
        refuse("original conda interpreter realpath mismatch")
    if sha(real_python) != BINDING["python_sha256"]:
        refuse("original conda interpreter hash mismatch")
    if not BINDING["activation_receipt_sha256"]:
        refuse("missing independently reviewed activation receipt identity")
    if len(BINDING["source_files"]) != 8:
        refuse("missing exact eight-code-file source binding")
    for relative, expected in BINDING["source_files"].items():
        filename = root / relative
        if filename.resolve() != filename or not filename.is_relative_to(root):
            refuse("source path outside exact runtime tree")
        checked_file(filename, BINDING["uid"])
        if sha(filename) != expected:
            refuse("runtime source hash mismatch: " + relative)
    config = root / BINDING["argv"][1]
    checked_file(config, BINDING["uid"])
    if sha(config) != BINDING["runtime_config_sha256"]:
        refuse("deterministically adapted runtime YAML hash mismatch")
    # Do not accept caller GIT_DIR/CONFIG/PATH overrides as a source identity.
    git_env = {
        "PATH": "/usr/bin:/bin", "GIT_OPTIONAL_LOCKS": "0",
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_CONFIG_GLOBAL": "/dev/null", "LANG": "C",
    }
    result = subprocess.run(
        ["/usr/bin/git", "--no-optional-locks", "-c", "core.fsmonitor=false",
         "-C", str(root), "rev-parse", "--verify", "HEAD"],
        env=git_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, check=False)
    if result.returncode or result.stdout.strip() != BINDING["source_commit"]:
        refuse("runtime Git HEAD differs from reviewed PSC source")

def check_lock_inode(descriptor, specification):
    opened = os.fstat(descriptor)
    current = os.lstat(specification["path"])
    if not stat.S_ISREG(opened.st_mode) or not stat.S_ISREG(current.st_mode):
        refuse("lock is not an existing regular file")
    identity = (specification["dev"], specification["ino"])
    if None in identity or (opened.st_dev, opened.st_ino) != identity:
        refuse("opened lock inode differs from reviewed existing inode")
    if (current.st_dev, current.st_ino) != identity:
        refuse("lock path replaced while opening or acquiring")
    if opened.st_uid != BINDING["uid"] or opened.st_nlink != 1:
        refuse("lock owner or link count mismatch")

def locked_exec(args):
    descriptors = []
    try:
        for specification in BINDING["lock_files"]:
            # Never create/truncate/replace/unlink an original cooperative lock.
            descriptor = os.open(
                specification["path"], os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC)
            descriptors.append(descriptor)
            check_lock_inode(descriptor, specification)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                if error.errno in (errno.EAGAIN, errno.EACCES):
                    refuse("cooperative lock busy", 75)
                raise
        for descriptor, specification in zip(descriptors, BINDING["lock_files"]):
            check_lock_inode(descriptor, specification)
            os.set_inheritable(descriptor, True)
            if not os.get_inheritable(descriptor):
                refuse("lock FD remains close-on-exec")
        # Revalidate source/interpreter/owner under all three retained original locks.
        validate_training(args)
        require_project_cap1()
        last_moment_direct_free = require_locked_direct_free()
        # A failed/uncertain exec consumes this artifact too. Never remove or
        # automatically clear this one-shot marker, including after normal exit.
        stage = Path(BINDING["stage"])
        metadata = os.lstat(stage)
        if (not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != BINDING["uid"]
                or metadata.st_mode & 0o022 or stage.resolve() != stage):
            refuse("one-shot stage must be an owned, non-writable real directory")
        marker = Path(BINDING["one_shot_marker"])
        if marker.parent != stage:
            refuse("one-shot marker outside fixed activation stage")
        descriptor = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        try:
            payload = json.dumps({
                "pid": os.getpid(), "uid": os.getuid(), "argv": args,
                "runtime_root": BINDING["runtime_root"],
                "source_commit": BINDING["source_commit"],
                "activation_receipt_sha256": BINDING["activation_receipt_sha256"],
                "owner": EXPECTED_OWNER, "last_moment_direct_free": last_moment_direct_free,
                "same_project_cap1_verified_with_three_original_locks_held": True,
                "lock_inodes": BINDING["lock_files"],
            }, sort_keys=True).encode("utf-8") + b"\n"
            os.write(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        # FD numbers are opened after canonical Popen(close_fds=True). They
        # survive this execve because each was made inheritable above.
        os.execve(BINDING["python"], [BINDING["python"], "-B", *args], os.environ.copy())
    finally:
        # Only reached on refusal/error, never after successful exec.
        for descriptor in reversed(descriptors):
            os.close(descriptor)

def main():
    args = sys.argv[1:]
    if not is_training(script_target(args)):
        # No mutable PATH search, shell function, env executable or proof switch.
        os.execve(BINDING["python"], [BINDING["python"], "-B", *args], os.environ.copy())
    validate_training(args)
    require_project_cap1()
    locked_exec(args)


def run(binding):
    global BINDING
    BINDING = binding
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        refuse(type(error).__name__ + ": " + str(error))
