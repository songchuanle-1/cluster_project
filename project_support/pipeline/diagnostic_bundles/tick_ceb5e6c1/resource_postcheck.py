"""Resume only the final resource observation after a Python3.6 API failure."""
from datetime import datetime,timezone
import json
from ops import guard,save,ssh,OUT,ROOT
import foreground_tick as tick
guard()
if not (OUT/'resource_probe_initial_failure.json').exists():
    save('resource_probe_initial_failure.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'error':"Remote Python3.6 subprocess rejected text=True before resource query;independent statistics audit already persisted;server4 resource result already saved before server3 failure",'repair':'universal_newlines=True;resume existing saved evidence,no scientific protocol change'})
probe=r'''
import json,socket,subprocess,fcntl
from datetime import datetime,timezone
assert socket.gethostname()==HOSTNAME
row=subprocess.check_output(['nvidia-smi','-i',GPU,'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],universal_newlines=True).strip()
assert row.split(',')[1].strip()==UUID
contexts=subprocess.check_output(['nvidia-smi','-i',GPU,'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],universal_newlines=True).strip()
locks={}
if GPU=='0':
    for kind in ['training','diagnostic','exclusive']:
        with open('/tmp/cluster_project_gpu0_'+kind+'.lock','rb') as h:
            try:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]='released_at_probe'
            except BlockingIOError:locks[kind]='busy_preserved'
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'gpu':row,'contexts':contexts,'lifetime_locks':locks}))
'''
for label,host,hostname,gpu,uuid in [('server4','192.168.1.115','dl04-MS-7E06','0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),('server3','192.168.1.120','sysu311-MS-7C59','1','GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0')]:
    code=probe.replace('HOSTNAME',repr(hostname)).replace('GPU',repr(gpu)).replace('UUID',repr(uuid))
    path=OUT/(label+'_final_resources.json')
    if path.exists():value=tick.load(path)
    else:
        value=ssh(code,host);save(label+'_final_resources.json',value)
    print(json.dumps({label:value}))
source=tick.load(ROOT/'pipeline/diagnostic_bundles/tick_b4174e26/manifest.json')
name='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fle_r1'
local={relative:tick.digest(ROOT/'Cluster/framework/model/Quard_model'/name/relative) for relative in source['source_hashes']}
assert local==source['source_hashes']
save('production_source_postcheck.json',{'unchanged':True,'source_hashes':local,'goal_sha256':tick.digest(ROOT/'pipeline/goal.json')})
