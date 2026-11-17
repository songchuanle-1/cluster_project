"""Post-test exact-source/checkpoint and released-device observations only."""
import json
import shlex
from audit_terminal import guard,save,remote,OUT,tick

guard()
audit=tick.load(OUT/'terminal_observation.json')
checkpoint=tick.load(OUT/'checkpoint_metadata.json')['checkpoints']['best.pth']
constants={'FILES':audit['source_hashes'],'CHECKPOINT':checkpoint['path'],'CHECKPOINT_SHA':checkpoint['sha256']}
program='\n'.join(key+'='+repr(value) for key,value in constants.items())+'\n'+r'''
import datetime,fcntl,hashlib,json,pathlib,socket,subprocess
assert socket.gethostname()=='dl04-MS-7E06'
root=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
def sha(path):
    h=hashlib.sha256()
    with pathlib.Path(path).open('rb') as handle:
        for block in iter(lambda:handle.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
assert row.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
locks={}
for kind in ('training','diagnostic','exclusive'):
    path='/tmp/cluster_project_gpu0_'+kind+'.lock'
    with open(path,'rb') as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:locks[path]='held'
        else:
            locks[path]='acquired_and_released';fcntl.flock(handle,fcntl.LOCK_UN)
hashes={name:sha(root/name) for name in FILES}
checkpoint_sha=sha(CHECKPOINT)
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'gpu':row,'contexts':contexts,'locks':locks,'source_hashes_match':hashes==FILES,
    'source_file_count':len(hashes),'checkpoint_sha256':checkpoint_sha,'checkpoint_unchanged':checkpoint_sha==CHECKPOINT_SHA,
    'old_training_pid_exists':pathlib.Path('/proc/1592337').exists(),'no_signals_or_gpu_computation':True}))
'''
result=json.loads(remote('192.168.1.115',shlex.join(['/usr/bin/python3','-B','-c',program])))
save('postverify_resources.json',result)
assert result['source_hashes_match'] and result['checkpoint_unchanged'] and not result['old_training_pid_exists']
assert not result['contexts'] and all(value=='acquired_and_released' for value in result['locks'].values())
print(json.dumps(result,indent=2))
