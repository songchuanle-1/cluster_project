"""Bind the original frozen post-training plan to this tick and unique M203best."""
from datetime import datetime,timezone
import copy,json
from ops import guard,save,run,ssh,evidence,ROOT,OUT,TOKEN,NAME,REMOTE_ROOT
import foreground_tick as tick
owner=guard();assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>720
old=tick.load(ROOT/'pipeline/diagnostic_bundles/tick_21500d1a/paired_manifest_isolated.json')
manifest=copy.deepcopy(old);manifest['deadline_at']=owner['deadline_at'];manifest['owner_token']=TOKEN
manifest['source_hashes']={k:v for k,v in old['source_hashes'].items() if 'hds_canon_r1' not in k}
source=tick.load(ROOT/'pipeline/diagnostic_bundles/tick_b4174e26/manifest.json')
for name,value in source['source_hashes'].items():manifest['source_hashes']['framework/model/Quard_model/'+NAME+'/'+name]=value
relative='configs/Quard/ctf_hcg_csort_fle_r1/'+NAME+'.yaml';manifest['source_hashes'][relative]=source['config_sha256']
best=tick.load(OUT/'exit_result.json')['checkpoint_metadata']['best.pth']
assert best['meta']['epoch']==13
manifest['conditions']={'reference_m95_epoch16':old['conditions']['reference_m95_epoch16'],
    'candidate_fle_epoch13':{'model':NAME,'config':relative,'checkpoint':best['path'],'checkpoint_sha256':best['sha256'],'epoch':13}}
manifest['producer_hashes']={name:tick.digest(OUT/'fullval'/name) for name in ('paired_validation_isolated.py','aligned_evidence.py')}
reference=ROOT/'pipeline/diagnostic_bundles/tick_21500d1a/reference_m95_epoch16.json'
manifest['reference_export_sha256']=tick.digest(reference)
manifest['scope']='OriginalfrozenM203posttrainingfullVALplan;onebestepoch13;referenceM95epoch16notverifiedhistoricalchampionweights;notrainingormodelselection.'
save('fullval/paired_manifest_isolated.json',manifest)
lease={'project':'cluster_project','thread_id':owner['thread_id'],'token':TOKEN,'deadline_at':owner['deadline_at'],
    'native_manifest_sha256':tick.digest(OUT/'fullval/paired_manifest_isolated.json')}
save('fullval/execution_lease.json',lease)
stage='/data/songcl/Project/Cluster_project/pipeline/fle_fullval_ceb5e6c1'
probe='''import json,socket
from pathlib import Path
assert socket.gethostname()=='dl04-MS-7E06'
Path(%r).mkdir(parents=True,exist_ok=False)
print(json.dumps({'created':True}))
'''%stage
save('fullval_stage_created.json',ssh(probe))
files=[str(OUT/'fullval'/name) for name in [*manifest['producer_hashes'],'paired_manifest_isolated.json','execution_lease.json']]
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',*files,str(reference),'songcl@192.168.1.115:'+stage+'/'])
save('fullval_upload.json',dict(returncode=upload.returncode,stderr=upload.stderr));assert upload.returncode==0
work=tick.load(ROOT/'pipeline/research_work.json');candidate=next(c for c in work['candidates'] if c['id']=='fine-leaf-local-point-exchange')
candidate.update(stage='validation',failure_scope='implementation',next_action='Execute original frozen fullVAL/bestepoch13pairedplan andpredeclaredmixed-fineleafsubgroups now,then reportfailure/uncertaintywithoutnewmodelorrestart.')
candidate['evidence'] += [evidence(OUT/'exit_result.json'),evidence(OUT/'terminal_reconciliation.json'),evidence(OUT/'fullval_prereg.md'),evidence(OUT/'fullval/paired_manifest_isolated.json')]
guard();tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'prepared':'M203-FLE_fullVAL','epoch':13,'expressions':9508,'stage':stage}))
