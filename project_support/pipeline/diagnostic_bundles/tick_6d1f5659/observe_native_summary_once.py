"""Read at most 128 KiB from the existing trainer's actual open native logger."""
from datetime import datetime, timezone
import argparse
import json
import shlex
import subprocess
from observe_existing_once import guard, HERE, ROOT, sha, save

PROGRAM = r'''
from pathlib import Path
from datetime import datetime,timezone
import os,socket,json,re,hashlib
assert socket.gethostname()=="dl04-MS-7E06" and os.getuid()==1001
pid=3813109
proc=Path("/proc")/str(pid)
start=lambda:(proc/"stat").read_text().split(")")[-1].split()[19]
assert start()=="183481242"
assert os.readlink(proc/"cwd")=="/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
prefix="/data/songcl/Project/Cluster_project/Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rvec/"
targets=set()
for fd in (proc/"fd").iterdir():
 try:
  target=os.readlink(fd)
  if target.startswith(prefix) and target.endswith(".log"):targets.add(target)
 except (OSError,FileNotFoundError):pass
assert len(targets)==1,sorted(targets)
path=Path(next(iter(targets)));size=path.stat().st_size
with path.open("rb") as stream:
 offset=max(0,size-131072);stream.seek(offset);raw=stream.read(131072)
text=raw.decode("utf-8",errors="replace")
epoch=None;validations=[];saved=[]
for line in text.splitlines():
 match=re.search(r"Epoch \[(\d+)/\d+\]\[(\d+)/(\d+)\]",line)
 if match:epoch=int(match[1])
 match=re.search(r"\bmIoU :\s*([0-9.eE+-]+)",line)
 if match:
  value=float(match[1]);assert 0<=value<=1
  validations.append({"epoch_from_native_training_context":epoch,"exact_miou":value})
 match=re.search(r"save (best|last|epoch) pth to (.+\.pth)",line)
 if match:saved.append({"kind":match[1],"path":match[2]})
checkpoints=[]
for name in ("best.pth","last.pth"):
 f=path.parent/name
 if f.is_file():
  st=f.stat();checkpoints.append({"path":str(f),"bytes":st.st_size,"mtime_ns":st.st_mtime_ns})
assert start()=="183481242"
print(json.dumps({"observed_at":datetime.now(timezone.utc).isoformat(),"hostname":socket.gethostname(),
 "pid":pid,"start_ticks":"183481242","source_commit":"d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e",
 "native_logger_discovered_from_live_open_fd":str(path),"actual_work_dir":str(path.parent),
 "native_log_bytes":size,"offset":offset,"bytes_read":len(raw),"complete_log_observed":offset==0,
 "tail_sha256":hashlib.sha256(raw).hexdigest(),"exact_validations_in_bounded_tail":validations,
 "saved_checkpoint_events_in_bounded_tail":saved,"checkpoint_metadata_only":checkpoints,
 "current_training_epoch_in_tail":epoch,"full_training_complete":False,"checkpoint_content_loaded":False,
 "read_only":True,"GPU_compute":False,"signals_sent":False,"remote_files_written":False}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP"}))
        return
    owner = guard()
    intent, output = HERE / "native_summary.intent.json", HERE / "native_summary.actual.json"
    assert not intent.exists() and not output.exists(), "Reconcile without replay."
    save(intent, {"owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
                  "script_sha256": sha(__file__), "read_only": True, "no_replay": True})
    process = subprocess.Popen(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
         "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
         "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c " + shlex.quote(PROGRAM)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
        errors="replace")
    result = {"owner": owner, "certainty": "uncertain", "local_ssh_pid": process.pid,
              "kind": "CURRENT_BOUNDED_NATIVE_VALIDATION_AND_CHECKPOINT_OBSERVATION",
              "script_sha256": sha(__file__), "read_only": True}
    try:
        stdout, stderr = process.communicate(timeout=35)
        result.update(certainty="terminal", returncode=process.returncode, stderr=stderr[:2000])
        assert process.returncode == 0, stderr[:2000]
        assert len(stdout.encode()) < 24576
        result["observation"] = json.loads(stdout)
        guard()
        result["passed"] = True
    except BaseException as error:
        result.update(passed=False, error_type=type(error).__name__, error=str(error))
        save(output, result)
        raise
    save(output, result)
    observed = result["observation"]
    print(json.dumps({"path": str(output), "sha256": sha(output),
                      "actual_work_dir": observed["actual_work_dir"],
                      "bytes_read": observed["bytes_read"],
                      "exact_validations_in_bounded_tail": observed["exact_validations_in_bounded_tail"],
                      "checkpoint_files": observed["checkpoint_metadata_only"],
                      "full_training_complete": False}))


if __name__ == "__main__":
    main()
