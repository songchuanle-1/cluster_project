"""Bounded process/receipt handoff, not host authorization or a native CLI.

Callers still owe verified runtime, pinned executables/dependencies, private
scratch provisioning and the sandbox argv. Local tests use synthetic children.
"""
import math
import os
import signal
import subprocess
import threading
import time

from scratch_collation_launch_20260920 import verify_completion


def bounded_process(command, cwd, timeout=300, max_output_bytes=1024 * 1024):
    """Drain both pipes with bounded memory; always reap the immediate child.

Linux children run in a new session and their process group is cleaned up,
including when a descendant keeps a pipe open after the leader exits.
Windows is for child-only synthetic tests, not native diagnostic execution.
"""
    if (not isinstance(command, (list, tuple)) or not command
            or any(not isinstance(arg, str) or "\x00" in arg for arg in command)
            or not os.path.isabs(command[0])):
        raise ValueError("Explicit absolute executable and argv required")
    if (type(timeout) not in (int, float) or not math.isfinite(timeout)
            or not 0 < timeout <= 3600
            or type(max_output_bytes) is not int
            or not 0 < max_output_bytes <= 16 * 1024 * 1024):
        raise ValueError("Finite timeout and bounded output budget required")
    buffers = [bytearray(), bytearray()]
    overflow = threading.Event()
    errors = []
    lock = threading.Lock()
    process = subprocess.Popen(
        list(command), cwd=cwd, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True,
        env={"PATH": os.defpath}, start_new_session=(os.name == "posix"))

    def drain(pipe, index):
        try:
            while True:
                chunk = os.read(pipe.fileno(), 16384)
                if not chunk:
                    break
                with lock:
                    remaining = max_output_bytes - sum(map(len, buffers))
                    buffers[index].extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        overflow.set()
        except OSError as error:
            errors.append(error)
        finally:
            pipe.close()

    threads = [threading.Thread(target=drain, args=(pipe, i), daemon=True)
               for i, pipe in enumerate((process.stdout, process.stderr))]
    deadline = time.monotonic() + timeout
    timed_out = False
    try:
        for thread in threads:
            thread.start()
        while process.poll() is None:
            if overflow.is_set():
                break
            if time.monotonic() >= deadline:
                timed_out = True
                break
            time.sleep(0.01)
    finally:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        elif process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        for thread in threads:
            if thread.ident is not None:
                thread.join(timeout=5)
    if any(thread.is_alive() for thread in threads):
        raise RuntimeError("Child pipe cleanup incomplete")
    if timed_out:
        raise TimeoutError("Collation child exceeded timeout")
    if overflow.is_set():
        raise ValueError("Collation child exceeded combined output budget")
    if errors:
        raise RuntimeError("Child output drain failed") from errors[0]
    return subprocess.CompletedProcess(
        list(command), process.returncode,
        buffers[0].decode("utf-8"), buffers[1].decode("utf-8"))


def complete_handoff(command, run, manifest_sha256, expected_binding,
                     expected_full_binding_sha256, expected_indices, *,
                     timeout=300, max_output_bytes=1024 * 1024):
    """Connect bounded completion to existing read-only artifact verification.

    Internal integration only: this function does not supply runtime authorization,
    provisioning, executable attestation, or sandbox command validation.
    """
    from pathlib import Path

    completed = bounded_process(command, run, timeout, max_output_bytes)
    return verify_completion(
        completed, Path(run) / "output", manifest_sha256, expected_binding,
        expected_full_binding_sha256, expected_indices)
