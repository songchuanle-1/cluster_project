"""Run an unchanged frozen diagnostic with a fresh current-tick execution lease."""
from datetime import datetime,timezone
import json,shlex,sys
from ops import guard,save,run,ssh,ROOT,OUT,TOKEN
import foreground_tick as tick
kind=sys.argv[1];assert kind in ('self','metric','capture','repair')
owner=guard()
if kind in ('self','capture','repair'):
    local=OUT/('norm_'+('repair' if kind=='repair' else 'capture')+'/native_manifest.json') if kind!='self' else ROOT/'pipeline/diagnostic_bundles/tick_dbeca5d6/native_manifest.json'
    manifest_name='native_manifest.json';runner='native_diagnostic.py';result_name='native_diagnostic_result.json'
    stage=tick.load(local)['stage']
else:
    local=ROOT/'pipeline/diagnostic_bundles/tick_b4174e26/native_metric_manifest.json'
    manifest_name='native_metric_manifest.json';runner='native_metric.py';result_name='native_metric_result.json'
    stage='/data/songcl/Project/Cluster_project/pipeline/metric_geometry_b4174e26'
assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>600
remote_lease=stage+'/execution_'+TOKEN+'.json'
lease={'project':'cluster_project','thread_id':owner['thread_id'],'token':TOKEN,'deadline_at':owner['deadline_at'],
    'native_manifest_sha256':tick.digest(local),'created_at':datetime.now(timezone.utc).isoformat(),
    'scope':'Original frozen diagnostic only,physical server4GPU0,all3lifetimeflocks;no training/restart/GPU1'}
save('native_lease_'+kind+'.json',lease)
probe='''import json,hashlib,socket
from pathlib import Path
assert socket.gethostname()=='dl04-MS-7E06'
stage=Path(%r);manifest=stage/%r
assert hashlib.sha256(manifest.read_bytes()).hexdigest()==%r
assert not (stage/%r).exists(),'Preserve prior result'
assert not Path(%r).exists(),'Executionleasealreadyexists'
print(json.dumps({'manifest_matches':True,'prior_result_absent':True,'runner':str(stage/%r)}))
'''%(stage,manifest_name,lease['native_manifest_sha256'],result_name,remote_lease,runner)
save('native_preexecution_'+kind+'.json',ssh(probe))
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',str(OUT/('native_lease_'+kind+'.json')),'songcl@192.168.1.115:'+remote_lease])
save('native_lease_upload_'+kind+'.json',dict(returncode=upload.returncode,stdout=upload.stdout,stderr=upload.stderr));assert upload.returncode==0
guard()
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B '+shlex.quote(stage+'/'+runner)+' --lease '+shlex.quote(remote_lease)
started=datetime.now(timezone.utc).isoformat()
execution=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],1300)
save('native_execution_'+kind+'.json',dict(returncode=execution.returncode,stdout=execution.stdout,stderr=execution.stderr,started_at=started,finished_at=datetime.now(timezone.utc).isoformat()))
local_result=OUT/('norm_'+('repair' if kind=='repair' else 'capture')+'/'+result_name if kind in ('capture','repair') else result_name)
assert not local_result.exists()
fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+stage+'/'+result_name,str(local_result)])
save('native_fetch_'+kind+'.json',dict(returncode=fetch.returncode,stdout=fetch.stdout,stderr=fetch.stderr))
if fetch.returncode:
    print(json.dumps({'kind':kind,'execution_returncode':execution.returncode,'fetch_returncode':fetch.returncode,'stderr_tail':execution.stderr[-2500:]}))
    raise SystemExit(2)
result=tick.load(local_result)
if kind in ('capture','repair') and any('failure_capture' in attempt for attempt in result.get('control_attempts',[])):
    fetch_capture=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+stage+'/failed_norm_input.npz',str(local_result.parent/'failed_norm_input.npz')])
    save('native_fetch_'+kind+'_inputs.json',dict(returncode=fetch_capture.returncode,stdout=fetch_capture.stdout,stderr=fetch_capture.stderr));assert fetch_capture.returncode==0
print(json.dumps({'kind':kind,'execution_returncode':execution.returncode,'passed':result.get('passed',result.get('execution_passed')),
    'scene_count':len(result.get('scenes',[])),'native_forwards':result.get('native_forwards',0),'native_fps_layer_calls':result.get('native_fps_layer_calls',0),
    'error_type':result.get('error_type'),'error':result.get('error'),'stderr_tail':execution.stderr[-1600:] if execution.returncode else None}))
