"""Use canonical safe_sync for the existing admitted NDE runtime, once."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import shlex
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
TICK = Path(__file__).resolve().parent
TOKEN = "2218a50249ea45588e5138890a7f4160"
SOURCE = "0747f6acec1c61018ec99acf2efa5329c9b3523c"
BASE = "f6257de79148581334ee495e6e2d60ccb525457c"
RUNTIME = "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import closure
import pipeline_monitor as monitor


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, v):
    with Path(p).open("x", encoding="utf-8") as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    keys = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
    owner = {k: owner[k] for k in keys}
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 180
    assert sys.dont_write_bytecode and os.environ["GIT_OPTIONAL_LOCKS"] == "0"
    validation = read(TICK / "canonical_admission_validation.json")
    closure.admission(ROOT, validation["task"])
    ff = read(TICK / "nde_deployment_execute/ff_result.json")
    assert ff["owner"] == owner and ff["local_head"] == SOURCE and ff["exact9_additions"]
    assert closure.git(ROOT / "Cluster", "rev-parse", "HEAD") == SOURCE
    server = monitor.load_servers(str(ROOT))["server-4"]
    assert (server["host"], server["user"], server["remote_code_root"]) == (
        "192.168.1.115", "songcl", RUNTIME)
    assert server["allowed_gpus"] == [0] and server["task_memory_mb"] == 20000
    assert server["max_tasks_per_gpu"] == 1 and server["allow_external_overlay"] is True
    intent = TICK / "same_root_sync_intent.json"
    assert not intent.exists(), "Unknown previous sync: reconcile; never replay."
    calls = []

    def strict_ssh(host, user, command, timeout=120):
        assert (host, user) == ("192.168.1.115", "songcl")
        assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
        cmd = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
               "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
               'test "$(hostname)" = dl04-MS-7E06 && ' + command]
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
        n = len(calls)
        stdout = TICK / f"same_root_sync_{n:02d}.stdout"
        stderr = TICK / f"same_root_sync_{n:02d}.stderr"
        stdout.write_text(p.stdout, encoding="utf-8")
        stderr.write_text(p.stderr, encoding="utf-8")
        calls.append({"command_sha256": hashlib.sha256(command.encode()).hexdigest(),
                      "returncode": p.returncode,
                      "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr)})
        assert p.returncode == 0, p.stderr[-700:]
        return p.stdout.strip()

    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    original_ssh = monitor.ssh
    prior_git_ssh = os.environ.get("GIT_SSH_COMMAND")
    try:
        remote_before = strict_ssh(server["host"], server["user"],
                                  "git --no-optional-locks -C " + shlex.quote(RUNTIME) + " rev-parse HEAD")
        assert remote_before == BASE
        save(intent, {"owner": owner, "remote_root": RUNTIME, "remote_before": remote_before,
                      "source": SOURCE, "canonical_receipt": validation["receipt"],
                      "canonical_safe_sync": True, "no_replay": True})
        monitor.ssh = strict_ssh
        os.environ["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8"
        assert closure.safe_sync(ROOT, ROOT / "Cluster", server, monitor.ssh) is True
        config = validation["task"]["config"]
        program = (
            "from pathlib import Path;import hashlib,json,subprocess;"
            f"r=Path({RUNTIME!r});c=r/{config!r};"
            "h=subprocess.check_output(['git','--no-optional-locks','-C',str(r),'rev-parse','HEAD'],text=True).strip();"
            f"assert h=={SOURCE!r};"
            "s=r/'framework/lib/pointgroup_ops/pointgroup_ops_ext.cpython-310-x86_64-linux-gnu.so';"
            "so=hashlib.sha256(s.read_bytes()).hexdigest();"
            "assert so=='c86f516858d480e2583a437deb598279bc626e74975a060b17d75bf03f630033';"
            "print(json.dumps({'head':h,'root_exists':r.is_dir(),'yaml_sha256':hashlib.sha256(c.read_bytes()).hexdigest(),'so_sha256':so}))"
        )
        actual = json.loads(strict_ssh(server["host"], server["user"],
                                      "/usr/bin/python3 -I -B -c " + shlex.quote(program)))
        assert actual["yaml_sha256"] == "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"
        save(TICK / "nde_runtime_deployment.json", {
            "recorded_at": datetime.now(timezone.utc).isoformat(), "owner": owner,
            "local_head": SOURCE, "runtime_root": RUNTIME, "runtime_code_commit": actual["head"],
            "remote_before": remote_before, "source_verified": True,
            "old_roots_preserved": actual["root_exists"], "YAML_mapping_verified": True,
            "YAML_mapping_scope": "canonical safe_sync verifier plus unchanged original candidate YAML; canonical safe_launch adaptation remains prospective",
            "canonical_safe_sync": True, "actual": actual, "ssh_calls": calls,
            "GPU_compute": False, "training_started": False,
        })
        print(json.dumps({"passed": True, "same_existing_root": RUNTIME,
                          "source": actual["head"], "source_verified": True, "training_started": False}))
    finally:
        monitor.ssh = original_ssh
        if prior_git_ssh is None:
            os.environ.pop("GIT_SSH_COMMAND", None)
        else:
            os.environ["GIT_SSH_COMMAND"] = prior_git_ssh
        lock.close()


if __name__ == "__main__":
    main()
