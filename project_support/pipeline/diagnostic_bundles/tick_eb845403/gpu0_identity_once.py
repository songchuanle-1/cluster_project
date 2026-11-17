"""Read physical GPU0 identity only; never initialize a CUDA context."""
import argparse
from datetime import datetime, timezone
import json
import shlex
import subprocess

from run_kernel_suffix_once import HERE, guard, save, sha

BODY = r'''
import json,os,socket,subprocess,time
assert socket.gethostname()=="dl04-MS-7E06" and os.getuid()==os.geteuid()==1001
payload=json.load(__import__("sys").stdin)
assert payload["owner"]["token"]=="eb84540382834ffd88f5a83a0b797ee3"
from datetime import datetime,timezone
assert datetime.now(timezone.utc)<datetime.fromisoformat(payload["owner"]["deadline_at"])
out=os.memfd_create("gpu0_identity_out",os.MFD_CLOEXEC)
err=os.memfd_create("gpu0_identity_err",os.MFD_CLOEXEC)
p=subprocess.Popen(["/usr/bin/nvidia-smi","-i","0","--query-gpu=index,uuid,memory.free",
                    "--format=csv,noheader,nounits"],stdin=subprocess.DEVNULL,stdout=out,stderr=err)
start=(__import__("pathlib").Path("/proc")/str(p.pid)/"stat").read_text().rsplit(")",1)[1].split()[19]
stop=time.monotonic()+5
while p.poll() is None and time.monotonic()<stop:time.sleep(.02)
rc=p.poll()
raw=os.pread(out,1024,0).decode("utf-8","replace")
error=os.pread(err,1024,0).decode("utf-8","replace")
r={"owner":payload["owner"],"observed_at":datetime.now(timezone.utc).isoformat(),
   "hostname":socket.gethostname(),"uid":os.getuid(),"pid":p.pid,"start_ticks":start,
   "certainty":"terminal" if rc is not None else "uncertain","returncode":rc,
   "stdout":raw,"stderr":error,"physical_device_requested":0,
   "CUDA_context_or_training_started":False,"signals_sent":False,
   "GPU_resource_gate_or_budget_pass_claimed":False}
if rc==0:
 fields=[x.strip() for x in raw.strip().split(",")]
 assert len(fields)==3 and fields[0]=="0" and fields[1]=="GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
 r.update(index=0,uuid=fields[1],free_memory_mib=int(fields[2]),identity_matched=True)
print(json.dumps(r))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP"}))
        return
    owner = guard()
    intent, actual = HERE / "gpu0_identity.intent.json", HERE / "gpu0_identity.actual.json"
    assert not intent.exists() and not actual.exists(), "Reconcile; never replay."
    save(intent, {
        "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "wrapper_sha256": sha(__file__), "body": BODY,
        "kind": "READONLY_PHYSICAL_GPU0_IDENTITY_FOR_CPU_PROBE_BINDING",
        "no_CUDA_context_or_training": True, "no_replay": True,
    })
    process = subprocess.Popen(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
         "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
         "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -B -c " + shlex.quote(BODY)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace")
    result = {"owner": owner, "local_ssh_pid": process.pid, "certainty": "uncertain",
              "wrapper_sha256": sha(__file__), "signals_sent": False}
    try:
        stdout, stderr = process.communicate(
            json.dumps({"owner": owner}), timeout=18)
        result.update(certainty="terminal", returncode=process.returncode,
                      stderr=stderr[:1024])
        assert process.returncode == 0 and len(stdout.encode()) <= 8192
        result["observation"] = json.loads(stdout)
        assert result["observation"]["owner"] == owner
        assert result["observation"].get("identity_matched") is True
        guard()
        result["transport_passed"] = True
    except BaseException as error:
        result.update(transport_passed=False, error_type=type(error).__name__,
                      error=str(error)[:800])
        save(actual, result)
        raise
    save(actual, result)
    print(json.dumps({"path": str(actual), "sha256": sha(actual),
                      "uuid": result["observation"]["uuid"],
                      "free_memory_mib": result["observation"]["free_memory_mib"],
                      "CUDA_context_or_training_started": False}))


if __name__ == "__main__":
    main()
