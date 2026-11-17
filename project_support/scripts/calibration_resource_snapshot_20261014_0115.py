"""Read only the authorized card and preserve local and remote timestamps."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "3aabc8207fea49ffb20003340e9bdfb9"
owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
program = """
import csv,datetime,io,json,socket,subprocess
def query(args):
    result=subprocess.run(args,capture_output=True,text=True,timeout=20)
    if result.returncode: raise RuntimeError(result.stderr)
    return result.stdout.strip()
gpu=list(csv.reader(io.StringIO(query(['nvidia-smi','-i','7',
    '--query-gpu=uuid,memory.used,memory.free,memory.total,utilization.gpu',
    '--format=csv,noheader,nounits']))))[0]
processes=list(csv.reader(io.StringIO(query(['nvidia-smi','-i','7',
    '--query-compute-apps=pid,process_name,used_memory',
    '--format=csv,noheader,nounits']))))
locks={}
for name in ('cluster_project_gpu7_diagnostic.lock','cluster_project_gpu7_slot2_diagnostic.lock'):
    locks[name]=subprocess.run(['flock','-n','/tmp/'+name,'true'],
        capture_output=True,timeout=10).returncode==0
print(json.dumps({'remote_observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'hostname':socket.gethostname(),'gpu':7,'uuid':gpu[0].strip(),
    'used_mib':int(gpu[1]),'free_mib':int(gpu[2]),'total_mib':int(gpu[3]),
    'utilization_percent':int(gpu[4]),'processes':[{'pid':int(row[0]),
        'name':row[1].strip(),'used_mib':int(row[2])} for row in processes if row],
    'project_locks_reacquirable':locks}))
"""
import shlex
result = subprocess.run(
    ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "songcl@100.64.3.28",
     "/data3/songcl/miniconda3/envs/project_cluster/bin/python -B -c " + shlex.quote(program)],
    capture_output=True, text=True, timeout=60, check=True)
record = json.loads(result.stdout)
record["local_verified_at"] = datetime.now(timezone.utc).astimezone().isoformat()
record["tick_token"] = TOKEN
assert record["hostname"] == "das"
assert record["uuid"] == "GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a"
assert all(record["project_locks_reacquirable"].values())
path = ROOT / "pipeline/reports/native_calibration_resource_20261014_0115.json"
with path.open("x") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
print(json.dumps(record, indent=2))
