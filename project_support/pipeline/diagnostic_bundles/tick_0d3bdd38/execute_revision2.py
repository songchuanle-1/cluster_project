"""One frozen native diagnostic,using current lease and authorized physical GPU0."""
from datetime import datetime,timezone
import json,shlex
from ops import guard,save,run,ssh,evidence,add,ROOT,OUT,STAGE,TOKEN,THREAD,CID
import foreground_tick as tick

owner=guard(900)
local=OUT/'norm_revision2'
for name in ('cpu_contracts_result.json','interval_cpu_result.json'):
    assert tick.load(local/name)['passed']
work=tick.load(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']==CID)
c['gates'].update(diagnostic_revision2_original_CPU='PASS8_CONTRACT_GROUPS',diagnostic_revision2_saved_failures='PASS8_CAPTURED_CONDITIONS_BOTH_1E6')
add(c,[local/'cpu_contracts_result.json',local/'interval_cpu_result.json'])
guard();tick.save(ROOT/'pipeline/research_work.json',work)

probe=r'''
import json,subprocess,fcntl
from datetime import datetime,timezone
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],universal_newlines=True).strip()
cells=[x.strip() for x in row.split(',')]
assert cells[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],universal_newlines=True).strip()
assert not contexts and int(cells[2])<1024 and int(cells[3])<10,'Busy authorized GPU;preserve other job'
locks={}
for kind in ['training','diagnostic','exclusive']:
    with open('/tmp/cluster_project_gpu0_'+kind+'.lock','rb') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]='available_at_probe'
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':row,'contexts':contexts,'locks':locks}))
'''
save('native_initial_resources.json',ssh(probe))
lease={'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],
       'native_manifest_sha256':tick.digest(local/'native_manifest.json'),'created_at':datetime.now(timezone.utc).isoformat(),
       'scope':'Original8TRAINscene diagnostic only;time-selected early checkpoint;no training/restart/GPU1;all3lifetimeflocks'}
save('execution_lease.json',lease)
remote_lease=STAGE+'/execution_lease.json'
precheck='''from pathlib import Path
import hashlib,json
p=Path(%r)
assert hashlib.sha256((p/'native_manifest.json').read_bytes()).hexdigest()==%r
assert not (p/'native_diagnostic_result.json').exists() and not (p/'execution_lease.json').exists()
print(json.dumps({'unchanged_manifest':True,'new_execution':True}))
'''%(STAGE,lease['native_manifest_sha256'])
save('native_preexecution.json',ssh(precheck))
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',str(OUT/'execution_lease.json'),'songcl@192.168.1.115:'+remote_lease])
save('native_lease_upload.json',{'returncode':upload.returncode,'stderr':upload.stderr});assert upload.returncode==0
guard(600)
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
         'python -B '+shlex.quote(STAGE+'/native_diagnostic.py')+' --lease '+shlex.quote(remote_lease))
started=datetime.now(timezone.utc).isoformat()
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
response=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3',
              'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],min(1250,int(remaining)-120))
save('native_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr,'started_at':started,'finished_at':datetime.now(timezone.utc).isoformat()})
fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+STAGE+'/native_diagnostic_result.json',str(local/'native_diagnostic_result.json')])
save('native_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr})
if fetch.returncode:
    print(json.dumps({'failed_fetch':True,'returncode':response.returncode,'stderr_tail':response.stderr[-2500:]}));raise SystemExit(2)
result=tick.load(local/'native_diagnostic_result.json')
if any('failure_capture' in x for x in result.get('control_attempts',[])):
    fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+STAGE+'/failed_norm_input.npz',str(local/'failed_norm_input.npz')])
    save('native_failure_input_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr})
print(json.dumps({'passed':result['passed'],'native_forwards':result['native_forwards'],'suffix_replays':result['suffix_replays'],
    'completed_scenes':len(result['scenes']),'scene_mean_normal_minus_intervention_piou':result.get('scene_mean_normal_minus_intervention_piou'),
    'scene_bootstrap_95ci':result.get('scene_bootstrap_95ci'),'error_type':result.get('error_type'),'error':result.get('error'),
    'stderr_tail':response.stderr[-1800:] if response.returncode else None}))
