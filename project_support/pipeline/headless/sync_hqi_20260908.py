"""Fast-forward training code while preserving all remote uncommitted bytes."""
import hashlib
from pathlib import Path
import subprocess
import sys
import yaml


ROOT = Path("D:/project/cluster_project")


def run(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, timeout=90,
                          **kwargs).stdout


def main():
    server = sys.argv[1]
    assert server in ("server-4", "server-6")
    config = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))
    srv = config["servers"][server]
    target = f"{srv['user']}@{srv['host']}"
    remote_root = srv["remote_code_root"]
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", target]
    local = ["git", "-C", str(ROOT / "Cluster")]
    head = run(local + ["rev-parse", "HEAD"]).decode().strip()
    old = run(ssh + [f"git -C {remote_root} rev-parse HEAD"]).decode().strip()
    run(local + ["merge-base", "--is-ancestor", old, head])
    before = run(ssh + [f"git -C {remote_root} diff --binary HEAD"])
    untracked_before = run(ssh + [f"git -C {remote_root} ls-files --others --exclude-standard"])
    ref = "codex-hqi-20260908"
    run(local + ["push", f"ssh://{target}{remote_root}", f"HEAD:refs/heads/{ref}"])
    print(run(ssh + [f"git -C {remote_root} merge --ff-only {ref}"]).decode())
    after = run(ssh + [f"git -C {remote_root} diff --binary HEAD"])
    untracked_after = run(ssh + [f"git -C {remote_root} ls-files --others --exclude-standard"])
    final = run(ssh + [f"git -C {remote_root} rev-parse HEAD"]).decode().strip()
    assert before == after, "Remote tracked deployment diff changed"
    assert untracked_before == untracked_after, "Remote untracked file list changed"
    assert final == head
    print(server, final, "deployment_diff_sha256", hashlib.sha256(after).hexdigest(),
          "untracked_preserved", True)


if __name__ == "__main__":
    main()
