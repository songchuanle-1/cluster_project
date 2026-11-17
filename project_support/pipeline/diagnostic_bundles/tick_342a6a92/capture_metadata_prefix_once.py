"""Capture bounded data.pkl metadata prefixes for a non-executing local parser."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
from reconcile_existing_once import guard, sha, save, HERE

PROGRAM = r'''
from pathlib import Path
import os,socket,zipfile,base64,hashlib,json,stat
assert socket.gethostname()=="dl04-MS-7E06" and os.getuid()==1001
root=Path("/data/songcl/Project/Cluster_project/Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rvec/20261109_175800")
rows=[]
for name in ("last.pth","best.pth"):
 path=root/name;fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  before=os.fstat(fd);assert stat.S_ISREG(before.st_mode) and before.st_uid==1001
  with os.fdopen(os.dup(fd),"rb") as stream:
   with zipfile.ZipFile(stream) as archive:
    matches=[x for x in archive.infolist() if x.filename.endswith("/data.pkl")]
    assert len(matches)==1 and 0<matches[0].file_size<=8388608
    with archive.open(matches[0]) as member:raw=member.read(65536)
  after=os.fstat(fd);assert (before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns)
  rows.append({"name":name,"path":str(path),"bytes":after.st_size,"mtime_ns":after.st_mtime_ns,
   "prefix_bytes":len(raw),"prefix_sha256":hashlib.sha256(raw).hexdigest(),
   "prefix_base64":base64.b64encode(raw).decode(),"tensor_storage_read":False})
 finally:os.close(fd)
print(json.dumps({"checkpoints":rows,"read_only":True,"Torch_imported":False,
 "GPU_compute":False,"unpickling_or_code_execution":False,"signals_sent":False}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP"}))
        return
    owner = guard()
    intent, output = HERE / "metadata_prefix.intent.json", HERE / "metadata_prefix.actual.json"
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
              "kind": "CURRENT_BOUNDED_PICKLE_METADATA_PREFIX_CAPTURE_NO_EXECUTION"}
    try:
        stdout, stderr = process.communicate(timeout=35)
        result.update(returncode=process.returncode, certainty="terminal", stderr=stderr[:2000])
        assert process.returncode == 0, stderr[:2000]
        assert len(stdout.encode()) < 190000
        result["observation"] = json.loads(stdout)
        for row in result["observation"]["checkpoints"]:
            raw = base64.b64decode(row["prefix_base64"], validate=True)
            assert len(raw) == row["prefix_bytes"] <= 65536
            assert hashlib.sha256(raw).hexdigest() == row["prefix_sha256"]
            target = HERE / (row["name"] + ".data.pkl.prefix")
            with target.open("xb") as stream:
                stream.write(raw)
            row["local_prefix_path"] = str(target)
        guard()
        result["passed"] = True
    except BaseException as error:
        result.update(passed=False, error_type=type(error).__name__, error=str(error))
        save(output, result)
        raise
    save(output, result)
    print(json.dumps({"path": str(output), "sha256": sha(output),
                      "prefixes": [{"name": row["name"], "bytes": row["prefix_bytes"],
                                    "sha256": row["prefix_sha256"],
                                    "local_prefix_path": row["local_prefix_path"]}
                                   for row in result["observation"]["checkpoints"]],
                      "tensor_storage_read": False, "unpickling_or_code_execution": False}))


if __name__ == "__main__":
    main()
