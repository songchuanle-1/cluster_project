"""Run frozen diagnostics on newly released, explicitly authorized GPU0."""
import argparse
import ast
from datetime import datetime,timezone
import difflib
import json
from pathlib import Path
import shutil
import subprocess
from ops import ROOT,OUT,TOKEN,THREAD,GOAL,IDS,SSH,guard,tick,now,evidence,save,remote

OLD_UUID='GPU-7f82edb9-f620-8045-caea-a75232265cd1'
NEW_UUID='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
SOURCES={
    'resolution':ROOT/'pipeline/diagnostic_bundles/tick_4e35c1ce/native',
    'relabel':ROOT/'pipeline/diagnostic_bundles/tick_ae419db5',
}

def prepare():
    owner,_=guard(900)
    resources=tick.load(OUT/'current_resources_and_training.json')['server4']['data']
    gpu=resources['cards']['0']
    assert not gpu['contexts'] and all(gpu['locks_available'].values())
    assert gpu['gpu'].split(',')[-2:]==[' 41',' 0']
    assert resources['M204_pid_probe']['returncode']==1
    assert 'Early stopping at epoch 28: no improvement for 10 epochs (best=0.4993)' in resources['M204_log_tail']
    records=[]
    for kind,source in SOURCES.items():
        original=tick.load(source/'native_manifest.json')
        assert original['physical_gpu']==1 and original['gpu_uuid']==OLD_UUID
        assert original['tolerance']==1e-6 and not original['scientific_admission']
        for name,sha in original['diagnostic_files'].items():
            assert tick.digest(source/name)==sha,name
        folder=OUT/('native_'+kind)
        folder.mkdir(exist_ok=False)
        text=(source/'native_runtime.py').read_text(encoding='utf-8')
        substitutions=[("'nvidia-smi', '-i', '1'","'nvidia-smi', '-i', '0'",2),
                       ("['1', 'GPU-","['0', 'GPU-",1),
                       ('/tmp/cluster_project_gpu1_','/tmp/cluster_project_gpu0_',1),
                       (OLD_UUID,NEW_UUID,2)]
        changed=text
        for old,new,count in substitutions:
            assert changed.count(old)==count,(old,changed.count(old))
            changed=changed.replace(old,new)
        restored=changed
        for old,new,count in reversed(substitutions):
            assert restored.count(new)==count,(new,restored.count(new))
            restored=restored.replace(new,old)
        assert restored==text
        ast.parse(changed)
        (folder/'native_runtime.py').write_text(changed,encoding='utf-8')
        for name in original['diagnostic_files']:
            if name!='native_runtime.py':
                shutil.copyfile(source/name,folder/name)
                assert tick.digest(source/name)==tick.digest(folder/name)
                ast.parse((folder/name).read_text(encoding='utf-8'))
        if kind=='relabel':
            shutil.copyfile(source/'native_geometry.json',folder/'native_geometry.json')
            assert tick.digest(folder/'native_geometry.json')==original['geometry_sha256']
        manifest=json.loads(json.dumps(original))
        manifest.update(stage='/data/songcl/Project/Cluster_project/pipeline/native_a1b2de4f_'+kind+'_gpu0',
            physical_gpu=0,gpu_uuid=NEW_UUID,
            diagnostic_files={name:tick.digest(folder/name) for name in original['diagnostic_files']})
        with (folder/'native_manifest.json').open('x',encoding='utf-8') as stream:
            json.dump(manifest,stream,ensure_ascii=False,indent=2)
        records.append({'kind':kind,'source_manifest':evidence(source/'native_manifest.json'),
            'new_manifest':evidence(folder/'native_manifest.json'),
            'runtime_diff':list(difflib.unified_diff(text.splitlines(),changed.splitlines(),lineterm='')),
            'unchanged_task_sha256':{name:tick.digest(folder/name) for name in original['diagnostic_files'] if name!='native_runtime.py'},
            'protocol_unchanged':original['protocol'],'assets_unchanged':manifest['assets']==original['assets'],
            'cohort_unchanged':manifest.get('cohort')==original.get('cohort'),
            'scientific_change':False,'implementation_revision':False})
    plan=save('gpu0_resource_binding.json',{'preregistered_at':now(),'token':TOKEN,'goal_sha256':GOAL,
        'reason':'M204 natural patience earlystop at28;PIDabsent,authorizedGPU0idle/contextsnone/threefreelocks. Preserve all train/checkpoint evidence;no restart or migration.',
        'physical_gpu':0,'gpu_uuid':NEW_UUID,'records':records,
        'order':'Original resolution pair0;continue original remaining pairs only with controls passing,then original native relabel geometry.',
        'unchanged':'Original model/config/checkpoint/annotations/cohorts/controls1e-6/seed1999/targets/readouts/protocols. Resource mapping only;not new candidate/mechanism or revision.',
        'frozen_stop':'Retain any failed control. No task-effect interpretation if controls fail;no automatic scientificadmission or training.'})
    work=tick.load(ROOT/'pipeline/research_work.json')
    for row in work['candidates']:
        if row['id'] in IDS:
            row.update(stage='validation',updated_at=now(),failure_scope='inconclusive',scientific_admission=False)
            for field in ('blocker','blocker_kind','retry_after','unblock_condition','required_server','physical_gpu'):
                row.pop(field,None)
            row['next_action']='Run original frozen native test under current lease on actuallyidle/exclusivelylocked authorizedserver4GPU0;resource-only binding recorded. No model/protocol changes or automatic training.'
            row['evidence'].append(evidence(plan))
            row['evidence'].append(evidence(OUT/('native_resolution' if row['id']==IDS[0] else 'native_relabel')/'native_manifest.json'))
    guard()
    tick.save(ROOT/'pipeline/research_work.json',work)
    print(json.dumps({'binding':evidence(plan),'prepared':list(SOURCES),'scientific_changes':0},indent=2))

def run(kind,pair):
    owner,servers=guard(600)
    folder=OUT/('native_'+kind)
    manifest=tick.load(folder/'native_manifest.json')
    assert manifest['physical_gpu']==0 and manifest['gpu_uuid']==NEW_UUID
    paired=kind in ('resolution','relabel_mask')
    label=kind+('_pair_'+str(pair) if paired else '')
    lease=folder/('execution_lease_'+label+'.json')
    with lease.open('x',encoding='utf-8') as stream:
        json.dump({'project':'cluster_project','thread_id':THREAD,'token':TOKEN,
            'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(folder/'native_manifest.json')},stream,indent=2)
    stage=manifest['stage']
    program="from pathlib import Path\nimport json\np=Path("+repr(stage)+")\nassert p.parent==Path('/data/songcl/Project/Cluster_project/pipeline')\np.mkdir(exist_ok=True)\nprint(json.dumps({'stage':str(p)}))"
    made=remote('server-4',program)
    assert made['returncode']==0,made
    names=list(manifest['diagnostic_files'])+['native_manifest.json',lease.name]
    if kind=='relabel':
        names.append('native_geometry.json')
    cfg=servers['server-4']
    copied=subprocess.run(['scp',*SSH,*[str(folder/name) for name in names],cfg['user']+'@'+cfg['host']+':'+stage+'/'],capture_output=True,text=True,timeout=90)
    assert copied.returncode==0,copied.stderr
    runner={'resolution':'native_resolution_task.py','relabel':'native_geometry_probe.py','relabel_mask':'native_relabel_mask_task.py'}[kind]
    result_name=('native_resolution_pair_'+str(pair)+'.json' if kind=='resolution' else
                 'native_relabel_mask_pair_'+str(pair)+'.json' if kind=='relabel_mask' else 'native_relabel_geometry_result.json')
    command=['python','-B',runner,'--lease',lease.name]
    if paired:
        command+=['--pair',str(pair)]
    remaining=int((datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds())
    timeout=min(1250,remaining-180)
    program='''import json,subprocess,hashlib,os,fcntl
from pathlib import Path
from datetime import datetime,timezone
stage=Path(STAGE)
manifest=json.loads((stage/'native_manifest.json').read_text())
assert hashlib.sha256((stage/'native_manifest.json').read_bytes()).hexdigest()==MANIFEST_SHA
for name,sha in manifest['diagnostic_files'].items():
 assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==sha
started=datetime.now(timezone.utc).isoformat()
process=subprocess.run(COMMAND,cwd=stage,capture_output=True,text=True,timeout=TIMEOUT)
result_path=stage/RESULT_NAME
result=json.loads(result_path.read_text()) if result_path.is_file() else None
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
locks={}
for kind in ('training','diagnostic','exclusive'):
 with open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b') as handle:
  try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True
  except BlockingIOError:locks[kind]=False
print(json.dumps({'started_at':started,'ended_at':datetime.now(timezone.utc).isoformat(),'child_returncode':process.returncode,'stdout_tail':process.stdout[-4000:],'stderr_tail':process.stderr[-14000:],'result':result,'after':{'gpu':row,'contexts':contexts,'locks_available':locks},'new_training':0}))
'''
    replacements={'STAGE':repr(stage),'MANIFEST_SHA':repr(tick.digest(folder/'native_manifest.json')),
        'COMMAND':repr(command),'TIMEOUT':str(timeout),'RESULT_NAME':repr(result_name)}
    for key,value in replacements.items():
        program=program.replace(key,value)
    result=remote('server-4',program,timeout=timeout+50,conda=True)
    execution=save(label+'_execution.json',result)
    data=result.get('data',{})
    outcome=data.get('result')
    result_path=save(label+'_result.json',outcome) if outcome is not None else None
    work=tick.load(ROOT/'pipeline/research_work.json')
    row=next(row for row in work['candidates'] if row['id']==(IDS[0] if kind=='resolution' else IDS[1]))
    row['evidence'].append(evidence(execution))
    if result_path:
        row['evidence'].append(evidence(result_path))
    row.update(updated_at=now(),stage='validation',scientific_admission=False,
        gate_result='Actual currentlease GPU0native execution recorded;control failures and task limitations retained. Interpretation required;no automatic scientificadmission.')
    guard()
    tick.save(ROOT/'pipeline/research_work.json',work)
    summary={k:v for k,v in outcome.items() if k not in ('records','before')} if outcome else None
    print(json.dumps({'execution':evidence(execution),'remote_returncode':result['returncode'],
        'child_returncode':data.get('child_returncode'),'result':summary,'after':data.get('after'),
        'stderr_tail':data.get('stderr_tail',result['stderr'])[-5000:]},ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('prepare','run'))
    parser.add_argument('--kind',choices=('resolution','relabel','relabel_mask'))
    parser.add_argument('--pair',type=int,choices=range(4),default=0)
    args=parser.parse_args()
    if args.action=='prepare':
        prepare()
    else:
        assert args.kind
        run(args.kind,args.pair)
