"""Read-only current-owner verification of the already deployed NDE source."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import shlex
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "8a3431facc69449d9cbb681e512733aa"
SOURCE = "0747f6acec1c61018ec99acf2efa5329c9b3523c"
BASE_CONDA = "/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh"
BASE_CONDA_SHA = "6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import closure
import pipeline_monitor as monitor
import source_integrity


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, value):
    with Path(p).open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")


def ref(p):
    p = Path(p).resolve()
    return {"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)}


def main():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    owner = {k: owner[k] for k in (
        "token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")}
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sys.dont_write_bytecode and os.environ["GIT_OPTIONAL_LOCKS"] == "0"
    previous = ROOT / "pipeline/diagnostic_bundles/tick_2218a502"
    task = read(previous / "canonical_admission_validation.json")["task"]
    closure.admission(ROOT, task)
    assert sha(ROOT / task["admission_receipt"]) == "52bf897dc89729063ffb429035b1cd07f14d3ea8d3e690812a4e3adfb48ed266"
    old_ff = read(previous / "nde_deployment_execute/ff_result.json")
    assert old_ff["local_head"] == SOURCE and old_ff["exact9_additions"] is True
    assert old_ff["owner"]["token"] == "2218a50249ea45588e5138890a7f4160"
    assert closure.git(ROOT / "Cluster", "rev-parse", "HEAD") == SOURCE
    old_assets = read(previous / "protected_assets_before.json")
    assert all(sha(ROOT / "Cluster" / n) == d for n, d in old_assets["files"].items())
    index = Path(closure.git(ROOT / "Cluster", "rev-parse", "--git-path", "index"))
    if not index.is_absolute():
        index = ROOT / "Cluster" / index
    assert sha(index) == old_ff["index_sha256_after"]
    server = monitor.load_servers(str(ROOT))["server-4"]
    assert server["allowed_gpus"] == [0] and server["max_tasks_per_gpu"] == 1
    assert server["allow_external_overlay"] is True and server["task_memory_mb"] == 20000
    assert (server["host"], server["user"], server["expected_hostname"]) == (
        "192.168.1.115", "songcl", "dl04-MS-7E06")
    root = server["remote_code_root"]
    assert root == "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
    calls = []

    def ssh(host, user, command, timeout=60):
        assert (host, user) == ("192.168.1.115", "songcl")
        p = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
             "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
             'test "$(hostname)" = dl04-MS-7E06 && ' + command],
            capture_output=True, text=True, encoding="utf8", errors="replace", timeout=timeout)
        n = len(calls)
        stdout, stderr = HERE / f"observe_{n:02d}.stdout", HERE / f"observe_{n:02d}.stderr"
        stdout.write_text(p.stdout, encoding="utf8")
        stderr.write_text(p.stderr, encoding="utf8")
        calls.append({"returncode": p.returncode,
                      "command_sha256": hashlib.sha256(command.encode()).hexdigest(),
                      "stdout": ref(stdout), "stderr": ref(stderr)})
        assert p.returncode == 0, p.stderr[-800:]
        return p.stdout.strip()

    program = r'''
from pathlib import Path
import hashlib,json,os,socket,stat,subprocess
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
r=Path(P['root'])
h=subprocess.check_output(['/usr/bin/git','--no-optional-locks','-C',str(r),'rev-parse','HEAD'],text=True).strip()
assert h==P['source']
assert hashlib.sha256(Path(P['base']).read_bytes()).hexdigest()==P['base_sha']
so=r/'framework/lib/pointgroup_ops/pointgroup_ops_ext.cpython-310-x86_64-linux-gnu.so'
so_sha=hashlib.sha256(so.read_bytes()).hexdigest()
assert so_sha=='c86f516858d480e2583a437deb598279bc626e74975a060b17d75bf03f630033'
sources={n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in P['files']}
assert sources==P['files']
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.free,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert gpu.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
tasks=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  argv=(p/'cmdline').read_bytes().split(b'\0')
  if any(a==b'tools/train.py' or a.endswith(b'/tools/train.py') for a in argv):
   cwd=(p/'cwd').resolve()
   if str(cwd).startswith('/data/songcl/Project/Cluster_project/'):
    tasks.append({'pid':int(p.name),'cwd':str(cwd)})
 except (OSError,RuntimeError):pass
assert not tasks,'Unknown live project trainer: reconcile before production stage'
locks=[]
for k,ino in [('training',92537152),('diagnostic',92537153),('exclusive',92537154)]:
 p=Path('/tmp/cluster_project_gpu0_'+k+'.lock');s=os.lstat(p)
 assert stat.S_ISREG(s.st_mode) and s.st_uid==1001 and (s.st_dev,s.st_ino)==(66308,ino)
 locks.append({'path':str(p),'dev':s.st_dev,'ino':s.st_ino})
print(json.dumps({'hostname':socket.gethostname(),'uid':os.getuid(),'root_exists':r.is_dir(),
 'head':h,'base_conda_sha256':P['base_sha'],'source_files':sources,'so_sha256':so_sha,
 'gpu0':gpu,'project_trainers':tasks,'locks':locks,'signals_sent':False,'GPU_compute':False}))
'''
    source = read(ROOT / "pipeline/diagnostic_bundles/tick_4fa1481e/nde_revision1_source/source_version.json")
    paths = source["source_files"]
    params = {"root": root, "source": SOURCE, "base": BASE_CONDA,
              "base_sha": BASE_CONDA_SHA, "files": paths}
    actual = json.loads(ssh(server["host"], server["user"],
                           "/usr/bin/python3 -I -B -c " + shlex.quote("P=" + repr(params) + "\n" + program)))
    cpu_server = dict(server, conda_source=BASE_CONDA)
    mappings = [(m["source"], server[m["server_key"]].rstrip("/"))
                for m in read(ROOT / "pipeline/closure_policy.json")["path_mappings"]]
    source_integrity.verify_git(cpu_server, SOURCE, mappings, ssh)
    save(HERE / "nde_runtime_deployment.json", {
        "recorded_at": datetime.now(timezone.utc).isoformat(), "owner": owner,
        "local_head": SOURCE, "runtime_root": root, "runtime_code_commit": actual["head"],
        "source_verified": True, "old_roots_preserved": actual["root_exists"],
        "YAML_mapping_verified": True, "runtime_verification_only_no_sync": True,
        "historical_FF": ref(previous / "nde_deployment_execute/ff_result.json"),
        "historical_safe_sync": ref(previous / "nde_runtime_deployment.json"),
        "CPU_only_conda_source": BASE_CONDA, "CPU_base_sha256": BASE_CONDA_SHA,
        "actual": actual, "ssh_calls": calls, "training_started": False,
    })
    print(json.dumps({"passed": True, "source": SOURCE,
                      "gpu0": actual["gpu0"], "project_trainers": 0,
                      "historical_FF_owner_preserved": True, "no_sync_or_GPU_compute": True}))


if __name__ == "__main__":
    main()
