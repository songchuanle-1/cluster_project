"""Scoped real detached-source resolver; no fake Git result or global persistent edit."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path("D:/project/cluster_project")
MAIN = ROOT / "Cluster"
DETACHED = ROOT / "pipeline/isolated_versions/rvec_r1_558ef1ee"
BASELINE = ROOT / "pipeline/diagnostic_bundles/tick_558ef1ee/rvec_deployment_prepare/baseline.json"
BASE = "0747f6acec1c61018ec99acf2efa5329c9b3523c"
SOURCE = "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
GIT = "C:/Program Files (x86)/Git/cmd/git.exe"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(code, *args):
    return subprocess.check_output(
        [GIT, "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(code), *args],
        env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"), timeout=30)


def verify():
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert git(MAIN, "rev-parse", "HEAD").decode().strip() == BASE
    index = Path(git(MAIN, "rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = MAIN / index
    assert sha(index) == baseline["real_index_sha256"]
    assert hashlib.sha256(git(MAIN, "ls-files", "--stage", "-z")).hexdigest() == baseline["real_index_entries_sha256"]
    for relative, expected in {**baseline["dirty_files_exact28"], **baseline["working_tree_r0_files_exact9"]}.items():
        assert sha(MAIN / relative) == expected, relative
    assert DETACHED.resolve().is_relative_to((ROOT / "pipeline/isolated_versions").resolve())
    assert git(DETACHED, "rev-parse", "HEAD").decode().strip() == SOURCE
    result = subprocess.run([GIT, "--no-optional-locks", "-C", str(DETACHED), "symbolic-ref", "-q", "HEAD"],
                            capture_output=True, timeout=15)
    assert result.returncode == 1
    assert git(DETACHED, "status", "--porcelain=v1", "--untracked-files=all", "-z") == b""
    for relative, expected in baseline["source_files_exact9"].items():
        assert sha(DETACHED / relative) == expected, relative
    return str(DETACHED)


@contextmanager
def scoped(monitor):
    original = monitor.find_local_code_dir
    verify()

    def resolve(project):
        if Path(project).resolve() == ROOT.resolve():
            return verify()
        return original(project)

    monitor.find_local_code_dir = resolve
    try:
        yield
    finally:
        monitor.find_local_code_dir = original
        verify()
