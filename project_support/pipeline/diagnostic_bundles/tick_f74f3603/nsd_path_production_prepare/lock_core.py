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

def validate_training(args):
    # No proof/test/override environment is read by this branch.
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
                "lock_inodes": BINDING["lock_files"],
            }, sort_keys=True).encode("utf-8") + b"\n"
            os.write(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        # FD numbers are opened after canonical Popen(close_fds=True). They
        # survive this execve because each was made inheritable above.
        os.execve(BINDING["python"], [BINDING["python"], *args], os.environ.copy())
    finally:
        # Only reached on refusal/error, never after successful exec.
        for descriptor in reversed(descriptors):
            os.close(descriptor)

def main():
    args = sys.argv[1:]
    if not is_training(script_target(args)):
        # No mutable PATH search, shell function, env executable or proof switch.
        os.execve(BINDING["python"], [BINDING["python"], *args], os.environ.copy())
    validate_training(args)
    locked_exec(args)


def run(binding):
    global BINDING
    BINDING = binding
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        refuse(type(error).__name__ + ": " + str(error))
