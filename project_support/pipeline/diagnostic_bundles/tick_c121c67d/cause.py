"""Freeze and execute two outcome-blind diagnostic contexts under current lease."""
import argparse
import ast
import json
from pathlib import Path
import shutil
import subprocess
from ops import ROOT,OUT,TOKEN,THREAD,GOAL,IDS,SSH,guard,tick,save,evidence,now,remote

def prepare():
    guard(900)
    prior=ROOT/'pipeline/diagnostic_bundles/tick_a1b2de4f'
    inputs={'resolution':prior/'native_resolution','relabel':prior/'native_relabel_mask'}
    protocol=save('aggregation_cause_protocol.json',{'preregistered_at':now(),'token':TOKEN,'candidate_ids':list(IDS),'goal_sha256':GOAL,
        'question':'Does original input/outputmutation,or exactsourcepointer versus bitwiseclone replay,explain the failed native tokenreaggregation control?',
        'contexts':'Original first resolutionpair(scene0000_00/scene0029_00) and first relabelmaskpair(scene0000_00/scene0001_00);8expressions each. No scene/outcome selection or new seed.',
        'capture':'One instrumented original native lossforward per context. Capture all3actualmean reductions only while nativebuild_cluster_feats runs;freeze source refs,bitwiseinput/outputclones,IDs,versions/strides and native tokens before/aftercluster.',
        'test':'Exactly3serialized originalnative mean reductions for eachsource andclone at eachlevel,plusonezero-input control andonefullcascade per mode. Keepallerrors/maximums;neverrepeatuntilPASS or selectfavorableoutcome.',
        'predictions':'Input/ID mutation or tokenmutation distinguishescapturealiasdefect. Stableexactinputs withnonzero repeatvariation directly show nativefixedinputreduction variation. Onlysourcepassesallstrictcontrols andclonefails supports futurepointerreusehypothesis;doesNOTitselfadmitarepair.',
        'preserved':'Original1e-6threshold,allfailedresults,operator/dtype/model/config/checkpoint/seed/targets/schedule/gates. No alternativeoperator,precision,deterministicmode,canonicalseedrepair,backward,newmodelortraining.',
        'distinction':'Added matchedpointer/input/outputmutation discrimination and reusabletrue-native fixture,NOTunchangedfullmask/census/geometry rerun. Same2stableIDs,0newcandidates or claimedimplementationrevisions.',
        'limits':'Onefixedbatchpercontext;kernelvariationcausalitydoesnotmeasuretaskharm/benefit/novelty. OriginalscientificadmissionstaysFALSE.'})
    for index,(kind,source) in enumerate(inputs.items()):
        base=tick.load(source/'native_manifest.json')
        assert base['physical_gpu']==0 and base['tolerance']==1e-6
        assert tick.digest(source/'native_runtime.py')==base['diagnostic_files']['native_runtime.py']
        folder=OUT/('native_'+kind)
        folder.mkdir(exist_ok=False)
        shutil.copyfile(source/'native_runtime.py',folder/'native_runtime.py')
        shutil.copyfile(OUT/'native_aggregation_cause_task.py',folder/'native_aggregation_cause_task.py')
        ast.parse((folder/'native_aggregation_cause_task.py').read_text())
        manifest={key:base[key] for key in ('schema_version','root','name','assets','expected_epoch','tolerance','physical_gpu','gpu_uuid')}
        manifest.update(candidate_id=IDS[index],cohort=base['cohort'][:2],
            stage='/data/songcl/Project/Cluster_project/pipeline/cause_c121c67d_'+kind,
            protocol=evidence(protocol),scientific_admission=False,
            diagnostic_files={name:tick.digest(folder/name) for name in ('native_runtime.py','native_aggregation_cause_task.py')})
        with (folder/'native_manifest.json').open('x',encoding='utf-8') as stream:json.dump(manifest,stream,indent=2)
    work=tick.load(ROOT/'pipeline/research_work.json')
    for row in work['candidates']:
        if row['id'] not in IDS:continue
        row.update(stage='validation',updated_at=now(),scientific_admission=False,
            next_action='Executepreregisteredsourcepointer/bitwiseclone/mutationdiscrimination on originalfixednativebatch;retainall3repetitionsandoriginal1e-6failures. Thisisdiagnosis,notnewstructure/trainingorautomaticrepair.')
        for key in ('blocker','blocker_kind','retry_after','unblock_condition'):row.pop(key,None)
        row['evidence'].append(evidence(protocol))
    guard()
    tick.save(ROOT/'pipeline/research_work.json',work)
    print(json.dumps({'protocol':evidence(protocol),'contexts':list(inputs),'new_structural_experiments':0},indent=2))

def run(kind):
    owner,servers=guard(600)
    folder=OUT/('native_'+kind)
    manifest=tick.load(folder/'native_manifest.json')
    lease=folder/'execution_lease.json'
    with lease.open('x',encoding='utf-8') as stream:json.dump({'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(folder/'native_manifest.json')},stream,indent=2)
    stage=manifest['stage']
    made=remote("from pathlib import Path\nimport json\np=Path("+repr(stage)+")\nassert p.parent==Path('/data/songcl/Project/Cluster_project/pipeline')\np.mkdir(exist_ok=False)\nprint(json.dumps({'stage':str(p)}))")
    assert made['returncode']==0,made
    cfg=servers['server-4']
    names=list(manifest['diagnostic_files'])+['native_manifest.json','execution_lease.json']
    copied=subprocess.run(['scp',*SSH,*[str(folder/name) for name in names],cfg['user']+'@'+cfg['host']+':'+stage+'/'],capture_output=True,text=True,timeout=90)
    assert copied.returncode==0,copied.stderr
    code='''import json,subprocess,fcntl
from pathlib import Path
from datetime import datetime,timezone
stage=Path(STAGE)
started=datetime.now(timezone.utc).isoformat()
process=subprocess.run(['python','-B','native_aggregation_cause_task.py','--lease','execution_lease.json'],cwd=stage,capture_output=True,text=True,timeout=1250)
p=stage/'native_aggregation_cause_result.json'
result=json.loads(p.read_text()) if p.is_file() else None
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
locks={}
for kind in ('training','diagnostic','exclusive'):
 with open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b') as handle:
  try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True
  except BlockingIOError:locks[kind]=False
print(json.dumps({'started_at':started,'ended_at':datetime.now(timezone.utc).isoformat(),'child_returncode':process.returncode,'result':result,'stdout_tail':process.stdout[-2000:],'stderr_tail':process.stderr[-10000:],'after':{'contexts':contexts,'locks_available':locks},'new_training':0}))
'''.replace('STAGE',repr(stage))
    value=remote(code,timeout=1300,conda=True)
    path=save(kind+'_execution.json',value)
    result=value.get('data',{}).get('result')
    result_path=save(kind+'_result.json',result) if result is not None else None
    work=tick.load(ROOT/'pipeline/research_work.json')
    row=next(row for row in work['candidates'] if row['id']==IDS[0 if kind=='resolution' else 1])
    row['evidence'].append(evidence(path))
    if result_path:row['evidence'].append(evidence(result_path))
    row['updated_at']=now()
    guard()
    tick.save(ROOT/'pipeline/research_work.json',work)
    print(json.dumps({'evidence':evidence(path),'remote_returncode':value['returncode'],'child_returncode':value.get('data',{}).get('child_returncode'),'result':result,'after':value.get('data',{}).get('after'),'stderr':value.get('data',{}).get('stderr_tail',value['stderr'])[-2500:]},ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('prepare','run'))
    parser.add_argument('--kind',choices=('resolution','relabel'))
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    else:
        assert args.kind
        run(args.kind)
