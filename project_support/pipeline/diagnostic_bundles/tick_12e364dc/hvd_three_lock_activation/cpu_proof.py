"""Bounded foreground CPU proof. No model/GPU, daemon, signals or shared edits."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import fcntl
import hashlib
import json
import os
import pwd
import shlex
import socket
import subprocess
import sys

EXPECTED_STAGE = Path("/data/songcl/Project/Cluster_project/pipeline/runtime/hvd_three_lock_12e364dc")
ROOT = "/data/songcl/Project/Cluster_project/Cluster_hvd_20261106"
PYTHON = "/home/songcl/.conda/envs/project_cluster/bin/python"
CONFIG = "configs/Quard/ctf_hcg_csort_hvd/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hvd.yaml"
LOCKS = ["/tmp/cluster_project_gpu0_" + kind + ".lock" for kind in ("training", "diagnostic", "exclusive")]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def foreground(argv, **kwargs):
    process = subprocess.Popen(argv, **kwargs)
    try:
        stdout, stderr = process.communicate(timeout=25)
    except subprocess.TimeoutExpired:
        # Never signal or relaunch even our own uncertain CPU child.
        raise RuntimeError("CPU probe timed out; preserve child PID " + str(process.pid))
    return {"pid": process.pid, "returncode": process.returncode, "stdout": stdout, "stderr": stderr}


def locks_free():
    handles = []
    try:
        for path in LOCKS:
            handle = open(path, "a+b")
            handles.append(handle)
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    finally:
        for handle in reversed(handles):
            handle.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binding", required=True)
    args = parser.parse_args()
    stage = Path(__file__).resolve().parent
    assert socket.gethostname() == "dl04-MS-7E06"
    assert pwd.getpwuid(os.getuid()).pw_name == "songcl" and os.getuid() == os.geteuid() != 0
    assert stage == EXPECTED_STAGE
    binding = json.loads(Path(args.binding).read_bytes())
    owner = binding["root_owner_provenance"]
    def guard():
        assert owner["token"] == "12e364dc14cd4e1195532c7fd295b834"
        assert owner["thread_id"] == "01a159c5-29ab-7a22-ba7f-e79174757253"
        assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
        assert binding["runtime_root"] == ROOT and binding["source_commit"] == binding["runtime_code_commit"] == "d20eb221eff6584b67d4e9b5673559d0e1cb735b"
        assert binding["physical_gpu"] == 0 and binding["allowed_gpus"] == [0]
        for name, expected in binding["files"].items():
            assert sha(stage / name) == expected
        assert sha(binding["original_conda_source"]["path"]) == binding["original_conda_source"]["sha256"]
    guard()
    assert locks_free()
    head = foreground(["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", ROOT, "rev-parse", "HEAD"],
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert head["returncode"] == 0 and head["stdout"].strip() == binding["runtime_code_commit"]
    prefix = "source " + shlex.quote(str(stage / "server4_conda_hvd_three_locks.sh")) + " && conda activate project_cluster && cd " + shlex.quote(ROOT) + " && "
    sentinel = r'''
import fcntl,json,os,sys
assert os.getpid()==int(os.environ["HVD_CPU_EXPECTED_PID"])
assert os.getuid()==os.geteuid()==int(os.environ["HVD_CPU_EXPECTED_UID"])
assert sys.executable=="/home/songcl/.conda/envs/project_cluster/bin/python"
assert sys.argv[1:]==["special space","*","$literal","","--cpu-only"]
paths=["/tmp/cluster_project_gpu0_"+kind+".lock" for kind in ["training","diagnostic","exclusive"]]
held={}
for item in os.listdir("/proc/self/fd"):
 try:
  target=os.readlink("/proc/self/fd/"+item)
  if target in paths:held[target]=int(item)
 except OSError:pass
assert set(held)==set(paths)
for path,fd in held.items():
 assert not(fcntl.fcntl(fd,fcntl.F_GETFD)&fcntl.FD_CLOEXEC)
 with open(path,"a+b") as contender:
  try:fcntl.flock(contender,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:pass
  else:raise AssertionError("Project lock not retained by actual exec target")
print(json.dumps({"passed":True,"pid":os.getpid(),"uid":os.getuid(),"same_Bash_exec_PID":True,"exact_special_and_empty_argv":True,"three_retained_non_CLOEXEC_FDs":True,"three_real_contended_locks":True,"model_GPU_execution":False}))
'''
    script = prefix + "export HVD_CPU_EXPECTED_PID=$BASHPID HVD_CPU_EXPECTED_UID=$UID && _hvd_gpu0_locked_exec \"$CONDA_PREFIX/bin/python\" -B -c " + shlex.quote(sentinel) + " " + shlex.join(["special space", "*", "$literal", "", "--cpu-only"])
    actual = foreground(["/bin/bash", "-c", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert actual["returncode"] == 0, actual
    inherited = json.loads(actual["stdout"].strip())
    assert inherited["passed"] is True and inherited["pid"] == actual["pid"]
    assert locks_free()
    expected = ["tools/train.py", CONFIG, "--gpu_ids", "0", "--num_gpus", "1"]
    tripwire = "import json,sys;print(json.dumps({'tripwire_only':True,'argv':sys.argv[1:]}))"
    override = "_hvd_gpu0_locked_exec() { command \"$CONDA_PREFIX/bin/python\" -B -c " + shlex.quote(tripwire) + " \"$@\"; }; "
    cases = [
        ("exact6", expected, 0),
        ("duplicate_GPU", expected + ["--gpu_ids", "0"], 126),
        ("GPU1", ["tools/train.py", CONFIG, "--gpu_ids", "1", "--num_gpus", "1"], 126),
        ("other_config", ["tools/train.py", "configs/foreign.yaml", "--gpu_ids", "0", "--num_gpus", "1"], 126),
        ("missing_num_gpus", expected[:4], 126),
        ("duplicate_num_gpus", expected + ["--num_gpus", "1"], 126),
        ("Python_B_prefix", ["-B"] + expected, 126),
        ("absolute_train_alias", [ROOT + "/tools/train.py"] + expected[1:], 126),
    ]
    routing = []
    for name, argv, expected_rc in cases:
        guard()
        # The helper is replaced by a CPU-only tripwire in this short test shell;
        # accepted argv can never execute train.py during a route test.
        result = foreground(["/bin/bash", "-c", prefix + override + "python " + shlex.join(argv)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert result["returncode"] == expected_rc, {"case": name, **result}
        if expected_rc == 0:
            observation = json.loads(result["stdout"].strip())
            assert observation == {"tripwire_only": True, "argv": [PYTHON] + expected}
        else:
            assert not result["stdout"].strip()
        routing.append({"case": name, "returncode": result["returncode"], "passed": True,
                        "no_actual_training_target_executed": True})
    cpu = "import json,os,sys;assert sys.argv[1:]==['a b','','*','$literal'];print(json.dumps({'passed':True,'argv_exact':True,'python':sys.executable,'uid':os.getuid()}))"
    normal = foreground(["/bin/bash", "-c", prefix + "python -B -c " + shlex.quote(cpu) + " " + shlex.join(["a b", "", "*", "$literal"])],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert normal["returncode"] == 0 and json.loads(normal["stdout"])["passed"] is True, normal
    assert locks_free()
    guard()
    result = {
        "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(), "passed": True,
        "hostname": socket.gethostname(), "actual_uid": os.getuid(), "actual_euid": os.geteuid(),
        "actual_user": pwd.getpwuid(os.getuid()).pw_name,
        "actual_author_child_thread_id": binding["actual_author_child_thread_id"],
        "root_owner_provenance": owner, "runtime_root": ROOT, "runtime_code_commit": head["stdout"].strip(),
        "binding_sha256": sha(args.binding), "real_exec_lock_proof": inherited, "routing": routing,
        "normal_CPU_passthrough": json.loads(normal["stdout"]), "three_locks_released_after_CPU_exit": True,
        "original_conda_source_unchanged": True, "GPU_or_model_or_training_execution": False,
        "signals_or_background_guardian": False, "SERVERS_queue_source_checkpoint_or_oldstage_changed": False,
        "independent_review": "PENDING_ROOT_PEER_REVIEW"
    }
    with (stage / "actual_cpu_proof.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
