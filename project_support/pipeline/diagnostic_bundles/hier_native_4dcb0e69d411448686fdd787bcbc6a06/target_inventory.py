"""Read-only pinned address/GPU identity and diagnostic-release observation."""
from datetime import datetime,timezone
import fcntl
import json
import subprocess
def command(args):return subprocess.check_output(args,text=True,timeout=8).strip()
hostname=command(['hostname'])
assert hostname=='sysu311-MS-7C59'
addresses=command(['hostname','-I']).split()
assert '192.168.1.120' in addresses
gpu=command(['nvidia-smi','-i','1','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'])
assert gpu.split(',')[1].strip()=='GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0'
contexts=command(['nvidia-smi','-i','1','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'])
flocks={}
for name in ('/tmp/cluster_project_gpu1_m201_migration.lock','/tmp/cluster_project_gpu1_exclusive.lock','/tmp/cluster_project_gpu1_parameter_transport.lock'):
    with open(name,'a+b') as stream:
        try:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            flocks[name]='acquired_and_released'
        except BlockingIOError:flocks[name]='held_preserve'
print('HIER_NATIVE_RESULT='+json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),
    'hostname':hostname,'verified_current_ip':'192.168.1.120','gpu':gpu,'contexts':contexts,'flocks':flocks,
    'cuda_allocations':0,'old_registered_address':'192.168.1.194',
    'scope':'Current interface plus pinned host and GPU identity; no allocation, process signal, reset or lock deletion.'}))
