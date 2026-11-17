"""Execute the preregistered same-checkpoint TRAIN intervention after VAL."""
from datetime import datetime,timezone
import json
import shlex
import subprocess
from audit_terminal import guard,save,ROOT,OUT,tick

owner=guard()
assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>780
paired=tick.load(OUT/'paired_capture_index.json')
assert paired['passed'] and paired['optimizer_steps']==0
cpu=tick.load(OUT/'trained_feature_cpu_controls.json');assert cpu['passed'] and len(cpu['controls'])==4
audit=tick.load(OUT/'terminal_observation.json')
checkpoint=tick.load(OUT/'checkpoint_metadata.json')['checkpoints']['best.pth']
name='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1'
source=(OUT/'trained_feature_suffix_native.py').read_text(encoding='utf-8')
compile(source,'trained_feature_suffix_native.py','exec')
manifest={'root':'/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b','deadline_at':owner['deadline_at'],
    'model':name,'config':'configs/Quard/ctf_hcg_csort_hds_canon_r1/'+name+'.yaml',
    'checkpoint':checkpoint['path'],'checkpoint_sha256':checkpoint['sha256'],
    'source_hashes':audit['source_hashes'],
    'producer_hashes':{filename:tick.digest(OUT/filename) for filename in ('trained_feature_suffix_native.py','aligned_evidence.py')}}
save('trained_suffix_manifest.json',manifest)
work=tick.load(ROOT/'pipeline/research_work.json')
candidate=next(c for c in work['candidates'] if c['id']=='m202-trained-mask-feature-contribution')
assert candidate['stage']=='validation'
candidate['stage']='validation'
candidate['next_action']='Run4full TRAIN captures+8same-prefix native ILA/decoder replays, strict1e-6 injection/head/replay controls and frozen-query cross-feature readout; retain failed full-forward repeat and do not claim independent repeat/noise, generalization or admission.'
for filename in ('trained_feature_suffix_native.py','trained_suffix_manifest.json'):
    path=OUT/filename
    candidate['evidence'].append({'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)})
guard();tick.save(ROOT/'pipeline/research_work.json',work)
stage='/data/songcl/Project/Cluster_project/pipeline/evidence_producer_21500d1a'
for filename in ('trained_feature_suffix_native.py','trained_suffix_manifest.json','trained_suffix_prereg.md'):
    response=subprocess.run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10',
        str(OUT/filename),'songcl@192.168.1.115:'+stage+'/'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45)
    assert response.returncode==0,response.stderr
guard()
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; '+shlex.join([
    'env','PYTHONDONTWRITEBYTECODE=1','python','-B',stage+'/trained_feature_suffix_native.py'])
response=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10',
    '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=3','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],
    capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=660)
save('trained_suffix_execution_attempt.json',{'observed_at':datetime.now(timezone.utc).isoformat(),
    'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr})
assert response.returncode==0,response.stderr[-4000:]
markers=[line for line in response.stdout.splitlines() if line.startswith('TRAINED_FEATURE_RESULT=')]
assert len(markers)==1
result=json.loads(markers[0].split('=',1)[1]);assert result['passed_controls'] and result['native_forwards']==4
response=subprocess.run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10',
    'songcl@192.168.1.115:'+stage+'/trained_suffix_result.json',str(OUT/'trained_suffix_result.json')],
    capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45)
assert response.returncode==0,response.stderr
print(json.dumps(result,indent=2))
