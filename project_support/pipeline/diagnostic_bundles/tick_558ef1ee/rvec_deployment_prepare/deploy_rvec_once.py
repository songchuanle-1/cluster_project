"""Default NOP. Reviewed root-only detached checkout and canonical safe_sync."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
MAIN = ROOT / "Cluster"
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
EXEC = TICK / "rvec_deployment_execution"
DETACHED = ROOT / "pipeline/isolated_versions/rvec_r1_558ef1ee"
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
GIT = "C:/Program Files (x86)/Git/cmd/git.exe"
SOURCE = "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
BASE = "0747f6acec1c61018ec99acf2efa5329c9b3523c"
PARENT = "0f8cc0f978b38c24e159d3a2d37344f59cc9a0be"
RUNTIME = "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
CONFIG = "configs/Quard/ctf_hcg_csort_rvec/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rvec.yaml"
BASE_CONDA = "/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh"
BASE_CONDA_SHA = "6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
OWNER = {
    "token": "558ef1ee132543f98d6897c98aff9dc9",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-09T05:05:14.672419+00:00",
    "deadline_at": "2026-11-09T06:05:14.672419+00:00",
    "context_sha256": "86e154fd6ee7f16a513f80dbe7ed7ef92c289a82ca7c0816b5418afffbe85373",
    "pending_sha256": "ce36edc3c5ca9f8b9fc76d34daaedf09a5c8d46a36200bf270e9c1c23df7d129"
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def git(code, *args):
    return subprocess.check_output(
        [GIT, "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(code), *args],
        env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"), timeout=90)


def lifecycle():
    names = ("SERVERS.yaml", "pipeline/queue.json", "pipeline/running.json",
             "pipeline/research_work.json", "pipeline/experiments.json", "pipeline/goal.json",
             "pipeline/closure_policy.json")
    return {name: sha(ROOT / name) for name in names if (ROOT / name).is_file()}


def protected():
    baseline = read(HERE / "baseline.json")
    assert git(MAIN, "rev-parse", "HEAD").decode().strip() == BASE
    index = Path(git(MAIN, "rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = MAIN / index
    assert sha(index) == baseline["real_index_sha256"]
    assert hashlib.sha256(git(MAIN, "ls-files", "--stage", "-z")).hexdigest() == baseline["real_index_entries_sha256"]
    for relative, expected in {**baseline["dirty_files_exact28"], **baseline["working_tree_r0_files_exact9"]}.items():
        assert sha(MAIN / relative) == expected, relative
    assert sha(ROOT / "SERVERS.yaml") == baseline["SERVERS_sha256"]
    assert git(MAIN, "rev-parse", "refs/pipeline/candidates/M234-RVE-r1").decode().strip() == SOURCE
    assert git(MAIN, "rev-list", "--parents", "-n", "1", SOURCE).decode().strip() == SOURCE + " " + PARENT
    return baseline


def verify_checkout():
    assert DETACHED.is_dir()
    assert DETACHED.resolve().is_relative_to((ROOT / "pipeline/isolated_versions").resolve())
    assert git(DETACHED, "rev-parse", "HEAD").decode().strip() == SOURCE
    result = subprocess.run([GIT, "--no-optional-locks", "-C", str(DETACHED), "symbolic-ref", "-q", "HEAD"],
                            capture_output=True, timeout=15)
    assert result.returncode == 1, "Exact detached HEAD required"
    assert git(DETACHED, "status", "--porcelain=v1", "--untracked-files=all", "-z") == b""
    for relative, expected in read(HERE / "baseline.json")["source_files_exact9"].items():
        assert sha(DETACHED / relative) == expected, relative


def guard(args, minimum=180):
    assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    assert os.environ.get("CODEX_THREAD_ID") == OWNER["thread_id"]
    current = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {key: current[key] for key in OWNER} == OWNER
    assert (datetime.fromisoformat(OWNER["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > minimum
    mode = read(ROOT / "pipeline/execution_mode.json")
    assert mode["mode"] == "foreground" and mode["target_thread_id"] == OWNER["thread_id"]
    for filename, field in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / filename) == OWNER[field]
    frozen = read(HERE / "FROZEN.json")
    assert frozen["owner"] == OWNER and frozen["source_commit"] == SOURCE
    assert all(sha(HERE / name) == expected for name, expected in frozen["files"].items())
    for anchor in frozen["anchors"].values():
        assert sha(Path(anchor["path"])) == anchor["sha256"]
    proof = read(ROOT / "pipeline/diagnostic_bundles/tick_b410c66a/rvec_r1_source_prepare/source_version.json")
    assert proof["source_commit"] == SOURCE and proof["source_parent_commit"] == PARENT
    assert proof["runtime_original_parent_commit"] == BASE
    for relative, expected in proof["source_files_exact9"].items():
        assert hashlib.sha256(git(MAIN, "cat-file", "blob", SOURCE + ":" + relative)).hexdigest() == expected
    receipt_path = Path(args.admission).resolve()
    assert receipt_path.is_relative_to(ROOT.resolve()) and sha(receipt_path) == args.admission_sha256
    receipt = read(receipt_path)
    assert receipt["id"] == "M234-RVE" and receipt["candidate_id"] == proof["candidate_id"]
    assert receipt["code_commit"] == SOURCE and receipt["config"] == CONFIG
    assert receipt["profile"] == "experiment_first" and receipt["implementation_revision_sha256"]
    task = {"id": "M234-RVE", "candidate_id": proof["candidate_id"], "config": CONFIG,
            "code_commit": SOURCE, "profile": "experiment_first",
            "admission_receipt": receipt_path.relative_to(ROOT).as_posix(),
            "requires_exclusive_ownership": False}
    sys.path.insert(0, str(SKILL))
    import closure
    import pipeline_monitor as monitor
    closure.admission(ROOT, task)
    peer_path = Path(args.review).resolve()
    assert peer_path.is_relative_to(ROOT.resolve()) and sha(peer_path) == args.review_sha256
    peer = read(peer_path)
    assert peer["passed"] is True and peer["owner"] == OWNER and peer["material_concerns"] == []
    assert peer["reviewer_thread_id"] not in (OWNER["thread_id"], "/root", "/root/fresh_ops")
    assert peer["FROZEN_sha256"] == sha(HERE / "FROZEN.json")
    assert peer["helper_sha256"] == sha(__file__) and peer["baseline_sha256"] == sha(HERE / "baseline.json")
    assert peer["source_commit"] == SOURCE and peer["admission_sha256"] == args.admission_sha256
    assert peer["source_review_passed"] is True and peer["canonical_sync_review_passed"] is True
    protected()
    queue = read(ROOT / "pipeline/queue.json")
    assert not [task for tasks in queue.get("gpu_queues", {}).values() for task in tasks
                if task.get("status") in ("running", "claiming")]
    assert not any(read(ROOT / "pipeline/running.json").values())
    return closure, monitor, task


REMOTE_OBSERVE = r"""
import fcntl,hashlib,json,os,pathlib,socket,stat,subprocess
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
root=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_nsd_20261107')
head=subprocess.check_output(['/usr/bin/git','--no-optional-locks','-C',str(root),'rev-parse','HEAD'],text=True).strip()
assert head==EXPECTED_HEAD
for proc in pathlib.Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  if proc.stat().st_uid==1001 and (proc/'cwd').resolve()==root:
   argv=(proc/'cmdline').read_bytes().split(b'\0')
   assert b'tools/train.py' not in argv and b'tools/test.py' not in argv,'Existing same-root trainer/test preserved'
 except (OSError,RuntimeError):pass
locks=[]
for kind,ino in [('training',92537152),('diagnostic',92537153),('exclusive',92537154)]:
 path='/tmp/cluster_project_gpu0_'+kind+'.lock'
 fd=os.open(path,os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  a,b=os.fstat(fd),os.lstat(path)
  assert stat.S_ISREG(a.st_mode) and stat.S_ISREG(b.st_mode)
  assert (a.st_dev,a.st_ino)==(b.st_dev,b.st_ino)==(66308,ino)
  fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
  c=os.lstat(path);assert (c.st_dev,c.st_ino)==(66308,ino)
  locks.append({'kind':kind,'device':a.st_dev,'inode':a.st_ino,'nonblocking_available':True})
 finally:os.close(fd)
base=pathlib.Path('/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0'
hashes={}
for name,expected in EXPECTED_FILES.items():
 actual=hashlib.sha256((root/name).read_bytes()).hexdigest();assert actual==expected,name;hashes[name]=actual
print(json.dumps({'hostname':socket.gethostname(),'uid':os.getuid(),'runtime_HEAD':head,
 'original_locks':locks,'source_files':hashes,'no_same_root_trainer':True,
 'GPU_compute':False,'signals_sent':False,'base_conda_sha256':hashlib.sha256(base.read_bytes()).hexdigest()}))
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--phase", choices=("checkout", "sync"))
    for option in ("admission", "admission-sha256", "review", "review-sha256"):
        parser.add_argument("--" + option)
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_GIT_MUTATION_SSH_TORCH_GPU_OR_STATE_WRITE"}))
        return
    assert args.phase and all((args.admission, args.admission_sha256, args.review, args.review_sha256))
    closure, monitor, task = guard(args)
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        closure, monitor, task = guard(args)
        before = lifecycle()
        EXEC.mkdir(exist_ok=True)
        intent, result = (EXEC / (args.phase + "_" + name + ".json") for name in ("intent", "result"))
        assert not intent.exists() and not result.exists(), "Existing or uncertain action; reconcile, never replay"
        if args.phase == "checkout":
            assert not DETACHED.exists(), "Never overwrite or reuse an uncertain checkout"
            hooks = EXEC / "empty_hooks"
            assert not hooks.exists()
            hooks.mkdir(exist_ok=False)
            save(intent, {"owner": OWNER, "source_commit": SOURCE, "detached": str(DETACHED),
                          "admission_sha256": args.admission_sha256, "review_sha256": args.review_sha256,
                          "lifecycle_before": before, "no_replay": True})
            command = [GIT, "--no-optional-locks", "-c", "core.fsmonitor=false",
                       "-c", "core.autocrlf=false", "-c", "core.eol=lf",
                       "-c", "core.hooksPath=" + str(hooks), "-C", str(MAIN),
                       "worktree", "add", "--detach", str(DETACHED), SOURCE]
            run = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                 timeout=120, env=dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_LFS_SKIP_SMUDGE="1"))
            save(EXEC / "checkout_command.json", {"argv": command, "returncode": run.returncode,
                                                  "stdout": run.stdout, "stderr": run.stderr})
            assert run.returncode == 0, "Preserve actual checkout failure; no cleanup/replay"
            verify_checkout()
            protected()
            assert lifecycle() == before
            save(result, {"owner": OWNER, "passed": True, "source_commit": SOURCE, "detached": str(DETACHED),
                          "main_HEAD": BASE, "main_index_user28_r0nine_preserved": True,
                          "lifecycle_unchanged": True, "training_started": False, "SSH_GPU": False})
        else:
            assert read(EXEC / "checkout_result.json")["owner"] == OWNER
            verify_checkout()
            server = monitor.load_servers(str(ROOT))["server-4"]
            baseline = read(HERE / "baseline.json")
            assert server["remote_code_root"] == RUNTIME and server["conda_source"] == baseline["original_conda_source"]
            assert server["host"] == "192.168.1.115" and server["user"] == "songcl"
            assert server["expected_hostname"] == "dl04-MS-7E06" and server["allowed_gpus"] == [0]
            assert server["max_tasks_per_gpu"] == 1 and server["allow_external_overlay"] is True
            assert server["task_memory_mb"] == 20000
            server = dict(server, conda_source=BASE_CONDA)
            calls = []

            def strict_ssh(host, user, command, timeout=120):
                guard(args, 90)
                assert (host, user) == ("192.168.1.115", "songcl")
                prefix = 'test "$(hostname)" = dl04-MS-7E06 && test "$(id -u)" = 1001 && '
                argv = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
                        "-o", "ConnectTimeout=8", "songcl@192.168.1.115", prefix + command]
                run = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                                     errors="replace", timeout=timeout)
                number = len(calls)
                save(EXEC / ("sync_ssh_%02d.json" % number), {
                    "command_sha256": hashlib.sha256(command.encode()).hexdigest(),
                    "returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr})
                calls.append({"number": number, "returncode": run.returncode})
                assert run.returncode == 0, "Preserve actual SSH outcome; no replay"
                return run.stdout.strip()

            def observe(head, files):
                program = "EXPECTED_HEAD=" + repr(head) + "\nEXPECTED_FILES=" + repr(files) + "\n" + REMOTE_OBSERVE
                return json.loads(strict_ssh(server["host"], server["user"],
                    "/usr/bin/python3 -I -B -c " + shlex.quote(program)))

            initial = observe(BASE, {})
            save(intent, {"owner": OWNER, "source_commit": SOURCE, "runtime_before": initial,
                          "detached": str(DETACHED), "admission_sha256": args.admission_sha256,
                          "canonical_safe_sync": True, "base_conda_sha256": BASE_CONDA_SHA,
                          "no_replay": True, "lifecycle_before": before})
            previous = os.environ.get("GIT_SSH_COMMAND")
            try:
                os.environ["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8"
                assert closure.safe_sync(ROOT, DETACHED, server, strict_ssh) is True
            finally:
                if previous is None:
                    os.environ.pop("GIT_SSH_COMMAND", None)
                else:
                    os.environ["GIT_SSH_COMMAND"] = previous
            code_hashes = {name: expected for name, expected in baseline["source_files_exact9"].items()
                           if name.endswith(".py")}
            actual = observe(SOURCE, code_hashes)
            protected()
            verify_checkout()
            assert lifecycle() == before
            save(result, {"owner": OWNER, "passed": True, "source_commit": SOURCE,
                          "runtime_root": RUNTIME, "runtime_code_commit": SOURCE, "runtime_before": BASE,
                          "detached": str(DETACHED), "actual": actual, "canonical_safe_sync": True,
                          "source_integrity_before_after": True, "source_verified": True,
                          "source_files_exact9": baseline["source_files_exact9"], "main_HEAD": BASE,
                          "main_index_user28_r0nine_preserved": True, "lifecycle_unchanged": True,
                          "SERVERS_changed": False, "queue_changed": False,
                          "GPU_compute": False, "training_started": False, "signals_sent": False,
                          "admission_sha256": args.admission_sha256, "SSH_calls": calls})
        print(json.dumps({"phase": args.phase, "result": str(result), "sha256": sha(result),
                          "source_commit": SOURCE, "training_started": False}))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
