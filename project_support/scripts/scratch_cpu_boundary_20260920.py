"""Scratch-only CPU probe launcher. Linux enforcement requires a real host run.

Uses bubblewrap's documented bind/namespace interface, not Python audit hooks.
The public operation is a synthetic filesystem probe, never a native diagnostic.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import subprocess
import uuid

from cpu_diagnostic_bootstrap_20260920 import (
    SCRATCH_ROOT, observe_runtime, validate_runtime)


PROBE = r"""
import errno, json, os, pathlib, sys
scratch, sentinel = map(pathlib.Path, sys.argv[1:])
assert sys.flags.isolated and sys.dont_write_bytecode
assert os.environ['CUDA_VISIBLE_DEVICES'] == ''
assert 'torch' not in sys.modules
denied = []
for flags in (os.O_WRONLY, os.O_RDWR, os.O_WRONLY | os.O_TRUNC):
    try:
        fd = os.open(sentinel, flags)
    except OSError as error:
        if error.errno != errno.EROFS:
            raise
        denied.append(flags)
    else:
        os.close(fd)
        raise RuntimeError('Read-only sentinel accepted write access')
try:
    os.mkdir(str(sentinel) + '.new')
except OSError as error:
    if error.errno != errno.EROFS:
        raise
else:
    raise RuntimeError('Read-only parent accepted mkdir')
target = scratch / 'probe-output'
with target.open('xb') as stream:
    stream.write(b'scratch-write-ok')
assert target.read_bytes() == b'scratch-write-ok'
assert sentinel.read_bytes() == b'read-only-sentinel'
assert not list(pathlib.Path('/dev').glob('nvidia*'))
print(json.dumps(dict(contract='scratch-probe-v1', denied_opens=len(denied),
                     denied_mkdir=True, scratch_write=True, native_imports=False)))
"""


def canonical(value):
    if (not isinstance(value, str) or not value.startswith("/")
            or value.startswith("//") or "\\" in value or "\x00" in value
            or str(PurePosixPath(value)) != value
            or ".." in PurePosixPath(value).parts):
        raise ValueError("Require canonical absolute POSIX path")
    return PurePosixPath(value)


def probe_command(executable, bwrap, run):
    """Construct argv only; does not certify mounts or authorize native work."""
    executable, bwrap, run = map(canonical, (executable, bwrap, run))
    root = PurePosixPath(SCRATCH_ROOT)
    if run.parent != root or not run.name.startswith("cpu-probe-"):
        raise ValueError("Probe must be an immediate child of diagnostic scratch")
    if executable.is_relative_to(root) or bwrap.is_relative_to(root):
        raise ValueError("Executables must be outside writable diagnostic scratch")
    output = str(run / "output")
    command = [
        str(bwrap), "--unshare-all", "--unshare-user", "--disable-userns",
        "--die-with-parent", "--new-session", "--cap-drop", "ALL",
        "--ro-bind", "/", "/", "--proc", "/proc", "--remount-ro", "/proc",
        "--dev", "/dev", "--remount-ro", "/dev/pts", "--remount-ro", "/dev",
        "--tmpfs", "/run", "--remount-ro", "/run",
        "--bind", output, output, "--bind", output + "/tmp", "/tmp",
        "--clearenv", "--setenv", "CUDA_VISIBLE_DEVICES", "",
        "--setenv", "HOME", output + "/home",
        "--setenv", "TMPDIR", "/tmp",
        "--setenv", "XDG_CACHE_HOME", output + "/cache",
        "--setenv", "PATH", "/usr/bin:/bin",
        "--chdir", output, "--",
        str(executable), "-I", "-B", "-c", PROBE, output, str(run / "sentinel")]
    return command


def checked_path(value, directory=False):
    path = Path(value)
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError("Symlink in boundary path")
    if path.resolve() != path.absolute():
        raise ValueError("Redirected boundary path")
    if not (path.is_dir() if directory else path.is_file()):
        raise ValueError("Missing boundary path")
    if not directory and path.stat().st_nlink != 1:
        raise ValueError("Hardlinked boundary executable")
    return path


def run_probe(expected_executable, bwrap, bwrap_sha256):
    """Run only the stdlib filesystem probe after real server/runtime checks.

    No fallback to an unsandboxed child. Unsupported bwrap/kernel fails closed.
    An eventual native child must repeat the probe before importing producers.
    """
    if platform.system() != "Linux":
        raise ValueError("Probe execution is restricted to Linux server-4")
    observation = observe_runtime()
    validate_runtime(observation, expected_executable)
    canonical(bwrap)
    binary = checked_path(bwrap)
    if (not isinstance(bwrap_sha256, str) or len(bwrap_sha256) != 64
            or any(c not in "0123456789abcdef" for c in bwrap_sha256)
            or hashlib.sha256(binary.read_bytes()).hexdigest() != bwrap_sha256):
        raise ValueError("Independently pinned bubblewrap digest differs")
    checked_path(expected_executable)
    root = checked_path(SCRATCH_ROOT, directory=True)
    # Provision a new private fixture. All host-side writes stay under this root.
    run = root / ("cpu-probe-" + uuid.uuid4().hex)
    command = probe_command(expected_executable, str(binary), str(run))
    run.mkdir(mode=0o700)
    output = run / "output"
    output.mkdir(mode=0o700)
    for name in ("tmp", "home", "cache"):
        (output / name).mkdir(mode=0o700)
    sentinel = run / "sentinel"
    with sentinel.open("xb") as stream:
        stream.write(b"read-only-sentinel")
    completed = subprocess.run(
        command, stdin=subprocess.DEVNULL, capture_output=True, text=True,
        close_fds=True, env={"PATH": "/usr/bin:/bin"}, cwd=str(run),
        check=True, timeout=30)
    result = json.loads(completed.stdout)
    expected = dict(contract="scratch-probe-v1", denied_opens=3,
                    denied_mkdir=True, scratch_write=True, native_imports=False)
    if result != expected:
        raise ValueError("Incomplete scratch probe receipt")
    if (sentinel.read_bytes() != b"read-only-sentinel"
            or (run / "sentinel.new").exists()
            or (output / "probe-output").read_bytes() != b"scratch-write-ok"):
        raise ValueError("Host-side probe bytes differ")
    return dict(
        scratch=str(run), boundary_probe_passed=True, native_execution=False,
        native_execution_authorized=False, bubblewrap_sha256=bwrap_sha256,
        receipt=result,
        limitations=[
            "Probe is not native extension compatibility or resource validation.",
            "Same-child probe and pinned imports are not yet connected.",
            "Trusted producer boundary, not a general hostile-code sandbox.",
            "Host root is readable; no confidentiality guarantee.",
            "Filesystem path checks assume no concurrent hostile host mutation."])
