"""Default NOP. Reviewed root-only sync of the existing clean candidate through canonical safe_sync."""
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
EXEC = TICK / "cso_deployment_execution"
DETACHED = ROOT / "pipeline/isolated_versions/m236_cso_integrated_7caf419d"
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
GIT = "C:/Program Files (x86)/Git/cmd/git.exe"
SOURCE = "5413102c57b526035f3920b5e7a81f3b58ad764d"
BASE = "0747f6acec1c61018ec99acf2efa5329c9b3523c"
PARENT = "b1e639b3ceb14bb5c65d9f81a084d41c834b951c"
RUNTIME = "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
CONFIG = "configs/Quard/ctf_hcg_csort_cso/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cso.yaml"
BASE_CONDA = "/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh"
BASE_CONDA_SHA = "6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
OWNER = {
    "token": "c1fe217800894083b65baac45f79aa83",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-14T01:52:47.538159+00:00",
    "deadline_at": "2026-11-14T02:52:47.538159+00:00",
    "context_sha256": "e33442420ba4c77b839918c43c944153092f834b2d316bb8979f843d3cdf82a4",
    "pending_sha256": "3d0bc5d2092b154a1acdb483f3d9185e95e9aa411b2089930f01dc1fd96875e6"
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
        [GIT, "--no-optional-locks", "-c", "safe.directory=" + Path(code).resolve().as_posix(), "-c", "core.fsmonitor=false", "-C", str(code), *args],
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
    assert git(MAIN, "rev-list", "--parents", "-n", "1", SOURCE).decode().strip() == SOURCE + " " + PARENT
    assert hashlib.sha256(git(MAIN, "status", "--porcelain=v1", "--untracked-files=all", "-z")).hexdigest() == baseline["main_porcelain_sha256"]
    return baseline


def verify_checkout():
    assert DETACHED.is_dir()
    assert DETACHED.resolve().is_relative_to((ROOT / "pipeline/isolated_versions").resolve())
    assert git(DETACHED, "rev-parse", "HEAD").decode().strip() == SOURCE
    result = subprocess.run([GIT, "--no-optional-locks", "-c", "safe.directory=" + DETACHED.resolve().as_posix(), "-C", str(DETACHED), "symbolic-ref", "-q", "HEAD"],
                            capture_output=True, timeout=15)
    assert result.returncode == 1, "Exact detached HEAD required"
    assert git(DETACHED, "status", "--porcelain=v1", "--untracked-files=all", "-z") == b""
    for relative, expected in read(HERE / "baseline.json")["source_files_exact9"].items():
        assert sha(DETACHED / relative) == expected, relative


def guard(args, minimum=180):
    assert sys.dont_write_bytecode and not sys.flags.optimize and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
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
    proof = read(HERE / "existing_checkout_proof.json")
    assert proof["owner"] == OWNER and proof["source_commit"] == SOURCE
    assert proof["source_parent_commit"] == PARENT and proof["existing_checkout_reused"] is True
    assert proof["new_checkout_performed"] is False and proof["clean"] is True
    for relative, expected in proof["files_exact9"].items():
        assert hashlib.sha256(git(DETACHED, "cat-file", "blob", SOURCE + ":" + relative)).hexdigest() == expected
    verify_checkout()
    receipt_path = Path(args.admission).resolve()
    assert receipt_path.is_relative_to(ROOT.resolve()) and sha(receipt_path) == args.admission_sha256
    receipt = read(receipt_path)
    assert receipt["id"] == "M236-CSO" and receipt["candidate_id"] == "fine-leaf-full-covariance-shape-composition"
    assert receipt["code_commit"] == SOURCE and receipt["config"] == CONFIG
    assert receipt["profile"] == "experiment_first"
    current_native_gate_binding(receipt)
    task = {"id": "M236-CSO", "candidate_id": "fine-leaf-full-covariance-shape-composition", "config": CONFIG,
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
    assert peer["reviewer_thread_id"] not in (OWNER["thread_id"], "/root", "/root/fresh_ops", "/root/cso_readiness", "/root/cso_native_ops")
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



def current_native_gate_binding(receipt):
    """Future real gates only; no prospective template may authorize safe_sync."""
    version_path = TICK / "cso_version_binding/version_bound_evidence.json"
    normalized_path = TICK / "cso_version_binding/native_smoke.version_bound.json"
    version, normalized = read(version_path), read(normalized_path)
    assert receipt.get("normalization_owner", receipt.get("owner")) == OWNER
    for field, path in (("version_association", version_path), ("native_smoke", normalized_path)):
        item = receipt[field]
        assert (ROOT / item["path"]).resolve() == path.resolve() and sha(path) == item["sha256"]
    assert version["owner"] == normalized["normalization_owner"] == OWNER
    assert version["passed"] is True and version["material_concerns"] == []
    assert version["kind"] == "DERIVED_EXACT_BYTE_VERSION_ASSOCIATION_NOT_NEW_EXECUTION"
    assert version["associated_code_commit"] == normalized["code_commit"] == SOURCE
    assert version["actual_execution_code_commit"] == normalized["original_execution_code_commit"] == "af45707d7b6089f764843337c5f88af285383f88"
    assert version["actual_source_parent_commit"] == "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
    assert version["actual_runtime_HEAD"] == normalized["runtime_original_parent_commit"] == PARENT
    assert version["files_exact9_sha256"] == read(HERE / "baseline.json")["source_files_exact9"]
    assert version["new_execution_claimed"] is False and version["raw_actual_source_owner_or_metadata_modified"] is False
    inputs = {}
    for item in version["inputs"]:
        path = (ROOT / item["path"]).resolve()
        assert path.is_relative_to(ROOT.resolve()) and sha(path) == item["sha256"]
        inputs[path] = item["sha256"]
    assert sha(Path(version["producer"]["path"]) if Path(version["producer"]["path"]).is_absolute() else ROOT / version["producer"]["path"]) == version["producer"]["sha256"]
    for mode, flag in (("smoke", "native_smoke_passed"), ("resources", "resource_gate_passed")):
        actual_path = TICK / ("cso_native_execution/run_" + mode + "_candidate_actual.json")
        assert inputs[actual_path.resolve()] == sha(actual_path)
        record = read(actual_path)
        assert record["owner"] == OWNER and record["certainty"] == "terminal" and record["returncode"] == 0
        observation = record["observation"]
        assert json.loads(record["stdout"]) == observation
        assert observation["certainty"] == "terminal" and observation["returncode"] == 0
        result = observation["result"]
        assert result["execution_completed"] is True and result["owner"] == OWNER
        assert result["mode"] == mode and result["target"] == "candidate"
        assert result["code_commit"] == "af45707d7b6089f764843337c5f88af285383f88"
        assert result["physical_gpu"] == 0 and result["gpu_uuid"] == "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
        if mode == "smoke":
            assert result["optimizer_steps"] == result["native_criterion_backwards"] == result["native_loss_forwards"] == 2
            assert result["native_smoke_checks_passed"] is True and result["backward_finite"] is True
            assert result["original_common_initialization_comparison"]["passed"] is True
            assert result["original_common_initialization_comparison"]["candidate_tensor_count"] == 841
            assert len(result["native_tracked_after_hash"]) == 9 and result["native_tracked_each_parameter_updated"] is True
        else:
            assert (result["batch_size"], result["lang_num_max"], result["warmup"], result["repeat"]) == (1, 1, 20, 100)
            assert result["profile"]["within10G"] is True and result["source_body_executed_without_replacement"] is True
        reviews = []
        for path in inputs:
            if path.is_relative_to(TICK.resolve()) and path.suffix == ".json":
                value = read(path)
                if value.get("actual_sha256") == sha(actual_path) and value.get(flag) is True:
                    reviews.append(value)
        assert len(reviews) == 1
        peer = reviews[0]
        assert peer["owner"] == OWNER and peer["passed"] is True and peer["material_concerns"] == []
        assert peer["reviewer_thread_id"] not in (OWNER["thread_id"], "/root", "/root/cso_readiness", "/root/cso_native_ops")
    review_item = receipt["version_association_review"]
    review_path = (ROOT / review_item["path"]).resolve()
    assert review_path.is_relative_to(TICK.resolve()) and sha(review_path) == review_item["sha256"]
    peer = read(review_path)
    assert peer["owner"] == OWNER and peer["passed"] is True and peer["material_concerns"] == []
    assert peer["reviewer_thread_id"] not in (OWNER["thread_id"], "/root", "/root/cso_readiness", "/root/cso_native_ops")
    assert peer["version_bound_evidence_sha256"] == sha(version_path) and peer["normalized_smoke_sha256"] == sha(normalized_path)
    assert peer["associated_commit"] == SOURCE and peer["commit_parent"] == PARENT
    assert peer["exact_nine_added_blobs_verified"] is True and peer["commit_worktree_clean"] is True


def scoped_safe_sync(closure, server, strict_ssh):
    """Keep canonical safe_sync untouched; add only process-local exact worktree trust."""
    previous_count = os.environ.get("GIT_CONFIG_COUNT")
    count = int(previous_count or "0")
    key, value = "GIT_CONFIG_KEY_" + str(count), "GIT_CONFIG_VALUE_" + str(count)
    previous_key, previous_value = os.environ.get(key), os.environ.get(value)
    try:
        os.environ["GIT_CONFIG_COUNT"] = str(count + 1)
        os.environ[key] = "safe.directory"
        os.environ[value] = DETACHED.resolve().as_posix()
        return closure.safe_sync(ROOT, DETACHED, server, strict_ssh)
    finally:
        for name, old in (("GIT_CONFIG_COUNT", previous_count), (key, previous_key), (value, previous_value)):
            if old is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = old



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
    parser.add_argument("--phase", choices=("sync",), default="sync")
    for option in ("admission", "admission-sha256", "review", "review-sha256"):
        parser.add_argument("--" + option)
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_GIT_MUTATION_SSH_TORCH_GPU_OR_STATE_WRITE"}))
        return
    assert all((args.admission, args.admission_sha256, args.review, args.review_sha256))
    assert sys.flags.utf8_mode, "Use python -X utf8 -B to preserve canonical UTF8 configuration reading"
    closure, monitor, task = guard(args)
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        closure, monitor, task = guard(args)
        before = lifecycle()
        verify_checkout()
        EXEC.mkdir(exist_ok=True)
        intent, actual, result = (EXEC / name for name in ("sync_intent.json", "sync.actual.json", "sync_result.json"))
        assert not any(path.exists() for path in (intent, actual, result)), "Existing or uncertain sync; reconcile, never replay"
        server = monitor.load_servers(str(ROOT))["server-4"]
        baseline = read(HERE / "baseline.json")
        assert server["remote_code_root"] == RUNTIME and server["conda_source"] == baseline["original_conda_source"]
        assert server["host"] == "192.168.1.115" and server["user"] == "songcl"
        assert server["expected_hostname"] == "dl04-MS-7E06" and server["allowed_gpus"] == [0]
        assert server["max_tasks_per_gpu"] == 1 and server["allow_external_overlay"] is True
        assert server["task_memory_mb"] == 20000 and server["conda_env"] == "project_cluster"
        server = dict(server, conda_source=BASE_CONDA)
        calls = []
        save(intent, {"owner": OWNER, "phase": "sync", "source_commit": SOURCE, "expected_runtime_before": PARENT,
                      "detached": str(DETACHED), "existing_clean_checkout_reused": True,
                      "admission_sha256": args.admission_sha256, "review_sha256": args.review_sha256,
                      "canonical_safe_sync": True, "base_conda_sha256": BASE_CONDA_SHA,
                      "no_replay": True, "lifecycle_before": before, "training_started": False})
        record = {"owner": OWNER, "phase": "sync", "certainty": "uncertain", "passed": False,
                  "source_commit": SOURCE, "runtime_root": RUNTIME, "runtime_before": PARENT,
                  "detached": str(DETACHED), "intent_sha256": sha(intent),
                  "admission_sha256": args.admission_sha256, "review_sha256": args.review_sha256,
                  "canonical_safe_sync": True, "training_started": False,
                  "GPU_compute": False, "signals_sent": False, "automatic_retry": False}
        try:
            def strict_ssh(host, user, command, timeout=120):
                guard(args, 90)
                assert (host, user) == ("192.168.1.115", "songcl")
                prefix = 'test "$(hostname)" = dl04-MS-7E06 && test "$(id -u)" = 1001 && '
                argv = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
                        "-o", "ConnectTimeout=8", "-o", "PasswordAuthentication=no",
                        "-o", "KbdInteractiveAuthentication=no", "songcl@192.168.1.115", prefix + command]
                number = len(calls)
                try:
                    run = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                                         errors="replace", timeout=timeout)
                except BaseException as error:
                    save(EXEC / ("sync_ssh_%02d.json" % number), {
                        "command_sha256": hashlib.sha256(command.encode()).hexdigest(),
                        "certainty": "uncertain", "error_type": type(error).__name__, "error": str(error)})
                    raise
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

            initial = observe(PARENT, {})
            record["runtime_before_observation"] = initial
            previous = os.environ.get("GIT_SSH_COMMAND")
            try:
                os.environ["GIT_SSH_COMMAND"] = ("ssh -o BatchMode=yes -o StrictHostKeyChecking=yes "
                    "-o ConnectTimeout=8 -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no")
                assert scoped_safe_sync(closure, server, strict_ssh) is True
            finally:
                if previous is None:
                    os.environ.pop("GIT_SSH_COMMAND", None)
                else:
                    os.environ["GIT_SSH_COMMAND"] = previous
            code_hashes = {name: expected for name, expected in baseline["source_files_exact9"].items()
                           if name.endswith(".py")}
            observed = observe(SOURCE, code_hashes)
            protected()
            verify_checkout()
            assert lifecycle() == before
            record.update(certainty="terminal", passed=True, runtime_code_commit=SOURCE, actual=observed,
                source_integrity_before_after=True, source_verified=True,
                source_files_exact9=baseline["source_files_exact9"], main_HEAD=BASE,
                main_index_user28_r0nine_preserved=True, lifecycle_unchanged=True,
                SERVERS_changed=False, queue_changed=False, old_consumed_entry_executed=False,
                server_copy_conda_source=BASE_CONDA, SSH_calls=calls,
                completed_at=datetime.now(timezone.utc).isoformat())
            save(result, record)
            record["canonical_sync_result"] = {"path": str(result), "sha256": sha(result)}
            save(actual, record)
        except BaseException as error:
            record.update(error_type=type(error).__name__, error=str(error), SSH_calls=calls,
                          reason="PRESERVE_PARTIAL_OR_UNCERTAIN_SYNC_NO_AUTOMATIC_REPLAY")
            if not actual.exists():
                save(actual, record)
            raise
        print(json.dumps({"phase": "sync", "result": str(result), "actual": str(actual),
                          "sha256": sha(actual), "source_commit": SOURCE, "training_started": False}))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
