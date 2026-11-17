"""Independent CPU checks and final project-only resources;no more CUDA."""
from datetime import datetime,timezone
import json,shlex
from ops import guard,save,run,ssh,ROOT,OUT
import foreground_tick as tick
guard(240)
stage='/data/songcl/Project/Cluster_project/pipeline/fle_targetmix_0d3bdd38'
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',str(OUT/'analyze_and_qf.py'),'songcl@192.168.1.115:'+stage+'/'])
save('final_analysis_upload.json',{'returncode':upload.returncode,'stderr':upload.stderr});assert upload.returncode==0
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
         'CUDA_VISIBLE_DEVICES= python -B '+shlex.quote(stage+'/analyze_and_qf.py'))
response=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],90)
save('final_analysis_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr});assert response.returncode==0,response.stderr
fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+stage+'/final_analysis.json',str(OUT/'final_analysis.json')])
save('final_analysis_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr});assert fetch.returncode==0
probe=r'''
import json,subprocess,fcntl
from datetime import datetime,timezone
row=subprocess.check_output(['nvidia-smi','-i',%r,'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],universal_newlines=True).strip()
assert row.split(',')[1].strip()==%r
contexts=subprocess.check_output(['nvidia-smi','-i',%r,'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],universal_newlines=True).strip()
locks={}
if %r=='0':
    for kind in ['training','diagnostic','exclusive']:
        with open('/tmp/cluster_project_gpu0_'+kind+'.lock','rb') as h:
            try:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]='released_at_probe'
            except BlockingIOError:locks[kind]='busy_preserved'
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':row,'contexts':contexts,'lifetime_locks':locks}))
'''
for name,host,gpu,uuid in [('server4','192.168.1.115','0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),('server3','192.168.1.120','1','GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0')]:
    save(name+'_final_resources.json',ssh(probe%(gpu,uuid,gpu,gpu),host))
manifest=tick.load(OUT/'norm_revision2/native_manifest.json');a=manifest['assets'];name=manifest['name']
local={f:tick.digest(ROOT/'Cluster/framework/model/Quard_model'/name/f) for f in a['source_hashes']}
assert local==a['source_hashes']
assert tick.digest(OUT/'terminal_content/neighbor_content.py')==tick.digest(OUT/'norm_revision2/neighbor_content.py')
save('source_and_helper_postcheck.json',{'production_source_unchanged':True,'source_files':len(local),'source_hashes':local,'terminal_control_same_revision2':True,'no_model_revision3':True})
print(response.stdout)
