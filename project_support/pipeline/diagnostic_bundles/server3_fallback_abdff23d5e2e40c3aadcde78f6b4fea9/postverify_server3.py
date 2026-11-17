"""Observe only the authorized target and verify diagnostic lock release."""
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path('/sdc1/songcl/Project/Cluster_project/Cluster_hier_feature_abdff23d')
assert subprocess.check_output(['hostname'],universal_newlines=True,timeout=5).strip()=='sysu311-MS-7C59'
def command(args):return subprocess.check_output(args,universal_newlines=True,timeout=10).strip()
gpu=command(['nvidia-smi','-i','1','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'])
cells=[c.strip() for c in gpu.split(',')]
assert cells[:2]==['1','GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0']
processes=command(['nvidia-smi','-i','1','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'])
locks={}
for name in ('/tmp/cluster_project_gpu1_m201_migration.lock','/tmp/cluster_project_gpu1_exclusive.lock','/tmp/cluster_project_gpu1_parameter_transport.lock'):
    with open(name,'a+b') as stream:
        try:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            locks[name]='acquired_and_released'
        except BlockingIOError:locks[name]='held_do_not_touch'
capture=ROOT.parent/'pipeline/server3_fallback_abdff23d/native_capture.pt'
result={'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':gpu,'compute_contexts':processes,
    'flocks':locks,'commit':command(['git','-C',str(ROOT),'rev-parse','HEAD']),
    'tracked_changes':command(['git','-C',str(ROOT),'diff','--name-only']),
    'capture_exists':capture.is_file(),'training_started_by_this_tick':False}
if capture.is_file():
    h=hashlib.sha256()
    with capture.open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
    result.update(capture_bytes=capture.stat().st_size,capture_sha256=h.hexdigest())
print('SERVER3_POSTVERIFY_JSON='+json.dumps(result))
