"""Root-only exact BCR GPU1 read-only observer. Default performs no connection."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import json
import os
import re
import subprocess
import time

ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
TOKEN='64ac844e35434422a64b1eea3d01cfa8'
THREAD='01a159c5-29ab-7a22-ba7f-e79174757253'
COMMIT='11a811618179ab1ddc0cee299194667413b7fdb9'
CONFIG='configs/Quard/ctf_hcg_csort_bcr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bcr.yaml'
REMOTE_ROOT='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
UUID='GPU-7f82edb9-f620-8045-caea-a75232265cd1'
ORIGINAL_CONFIG_SHA='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
DEPLOYED_CONFIG_SHA='77eac419317cb7d7f5d4688337597a966b27d2f920484c1e2323d279240289ea'
OWNER_FIELDS=('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')
EXPECTED_OWNER={'token': '64ac844e35434422a64b1eea3d01cfa8', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-10-25T06:05:55.178822+00:00', 'deadline_at': '2026-10-25T07:05:55.178822+00:00', 'context_sha256': 'f39ebddbb1545dae791003234a7f3baa976dfec99bf713af325c83db840853be', 'pending_sha256': '87e84dfad9553bfb31c0f77d6d3f7fd445bf86d452489622364d64dd31cde5ca'}


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def need(value,message):
    if not value:raise ValueError(message)
def save_new(path,value):
    with Path(path).open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
def owner_guard(expected=None):
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json');mode=read(ROOT/'pipeline/execution_mode.json')
    need({k:owner.get(k) for k in OWNER_FIELDS}==EXPECTED_OWNER,'Original exact six-field owner binding changed')
    need(owner['token']==TOKEN and owner['thread_id']==mode['target_thread_id']==os.environ.get('CODEX_THREAD_ID')==THREAD and mode['mode']=='foreground','Actual original owning root/environment required; never override identity')
    need(owner['generated_at']=='2026-10-25T06:05:55.178822+00:00' and owner['deadline_at']=='2026-10-25T07:05:55.178822+00:00','Original owner deadline window changed')
    need(datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at']),'Original deadline expired')
    need(sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256'],'Original context/pending changed')
    if expected is not None:need({k:owner[k] for k in OWNER_FIELDS}==expected,'Owner changed during observation')
    return {k:owner[k] for k in OWNER_FIELDS}


PROGRAM=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
# No subprocess, /proc or NVML access precedes the pinned hostname assertion.
import json,os,re,time,subprocess,hashlib
from pathlib import Path
p=Path('/proc')/str(PARAMS['pid'])
stat=(p/'stat').read_text().rsplit(')',1)[1].split()
args=[part.decode() for part in (p/'cmdline').read_bytes().split(b'\0') if part]
expected=['python','tools/train.py',PARAMS['config'],'--gpu_ids','1','--num_gpus','1']
assert args==expected and stat[0] not in ('Z','X','x')
assert os.readlink(p/'cwd')==REMOTE_ROOT and os.readlink(p/'fd/1')==PARAMS['log']
head=subprocess.check_output(['git','-C',REMOTE_ROOT,'rev-parse','HEAD'],text=True).strip()
assert head==COMMIT
actual_sources={name:hashlib.sha256((Path(REMOTE_ROOT)/name).read_bytes()).hexdigest() for name in SOURCE_HASHES}
assert actual_sources==SOURCE_HASHES
config_sha=hashlib.sha256((Path(REMOTE_ROOT)/PARAMS['config']).read_bytes()).hexdigest()
assert config_sha==DEPLOYED_CONFIG_SHA
log=Path(PARAMS['log'])
with log.open('rb') as stream:
 stream.seek(max(0,log.stat().st_size-600000));text=stream.read().decode(errors='replace')
trains=list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',text))
assert trains,'Original native TRAIN progress absent'
row=subprocess.check_output(['nvidia-smi','-i','1','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert [part.strip() for part in row.split(',')][:2]==['1',UUID]
contexts=subprocess.check_output(['nvidia-smi','-i','1','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
context_pids=[int(line.split(',')[0]) for line in contexts.splitlines() if line.strip()]
assert PARAMS['pid'] in context_pids
lines=text.replace('\r','\n').splitlines()
errors=[line[-600:] for line in lines if any(word in line for word in ('Traceback','AttributeError','RuntimeError','Early stopping'))]
vals=list(re.finditer(r'Val\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',text))
print(json.dumps({'pid':PARAMS['pid'],'start_ticks':stat[19],'state':stat[0],'argv':args,'cwd':REMOTE_ROOT,'fd1':os.readlink(p/'fd/1'),
 'runtime_HEAD':head,'source_commit':COMMIT,'actual_source_hashes':actual_sources,'source8_match_manifest':True,
 'original_local_CONFIG_sha256':ORIGINAL_CONFIG_SHA,'expected_mapped_CONFIG_sha256':DEPLOYED_CONFIG_SHA,'actual_deployed_CONFIG_sha256':config_sha,
 'deployed_YAML_equals_deterministic_mapped_expected':True,'mapped_values_sha256':MAPPED_VALUES_SHA,
 'train_progress':[int(trains[-1][i]) for i in (1,2,3,4)],'val_progress':([int(vals[-1][i]) for i in (1,2,3,4)] if vals else None),
 'log':str(log),'log_bytes':log.stat().st_size,'log_age_seconds':time.time()-log.stat().st_mtime,
 'gpu1':row,'gpu1_contexts':contexts,'other_GPU1_context_pids':[pid for pid in context_pids if pid!=PARAMS['pid']],
 'errors':errors,'last_nonempty_lines':[line[-400:] for line in lines if line.strip()][-6:],
 'GPU0':'NOT_QUERIED_NOT_USED','read_only':True,'signals_sent':False}))
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute-root',action='store_true');args=parser.parse_args()
    if not args.execute_root:
        print(json.dumps({'status':'DRAFT_NOT_RUN','SSH_or_GPU_queries':False,'proof_written':False}));return 0
    owner=owner_guard();observations=[];failure_path=HERE/'bcr_progress_observation_failure.json';output=HERE/'bcr_progress_observation.json'
    need(not output.exists() and not failure_path.exists(),'Existing observation requires read-only reconciliation; no overwrite/retry')
    try:
        task=next(t for t in read(ROOT/'pipeline/queue.json')['gpu_queues']['server-4'] if t['id']=='M212-BCR')
        need(task['status']=='running' and task['launch_verified'] is True and type(task['pid']) is int and task['pid']>0 and str(task['gpu'])=='1' and task['config']==CONFIG and task['code_commit']==COMMIT,'Exact actually verified BCR GPU1 task required')
        params={k:task[k] for k in ('pid','config','log')}
        need(re.fullmatch(re.escape(REMOTE_ROOT+'/logs/train_'+Path(CONFIG).stem+'_')+r'\d{8}_\d{6}\.log',params['log']) is not None,'Canonical unique BCR log path required')
        binding=read(ROOT/'pipeline/diagnostic_bundles/tick_7526f819/bcr_gpu1_execution/execution_binding.json');manifest=read(ROOT/'pipeline/diagnostic_bundles/tick_7526f819/bcr_gpu1_execution/native_manifest.json')
        need(binding['code_commit']==manifest['code_commit']==COMMIT and binding['physical_gpu']==manifest['physical_gpu']==1 and sha(ROOT/'pipeline/diagnostic_bundles/tick_7526f819/bcr_gpu1_execution/native_manifest.json')==binding['native_manifest_sha256'],'Actual source/GPU1 native manifest binding mismatch')
        need(manifest['candidate_config_sha256']==ORIGINAL_CONFIG_SHA and sha(ROOT/'Cluster'/CONFIG)==ORIGINAL_CONFIG_SHA,'Original byte-identical native YAML must be verified before any remote query')
        need(len(manifest['candidate_source_hashes'])==8,'Expected eight exact BCR source files')
        sources={'framework/model/Quard_model/'+manifest['candidate_name']+'/'+name:expected for name,expected in manifest['candidate_source_hashes'].items()}
        need(all(sha(ROOT/'Cluster'/name)==expected for name,expected in sources.items()),'Local BCR source differs from actual manifest')
        import yaml
        server=yaml.safe_load((ROOT/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']['server-4']
        need(server['host']=='192.168.1.115' and server['user']=='songcl' and server['expected_hostname']=='dl04-MS-7E06' and server['remote_code_root']==REMOTE_ROOT and 1 in server['allowed_gpus'],'Current pinned server/GPU1 eligibility changed')
        mappings=[(entry['source'],server[entry['server_key']].rstrip('/')) for entry in read(ROOT/'pipeline/closure_policy.json')['path_mappings']]
        def adapt(value):
            if isinstance(value,dict):return {key:adapt(item) for key,item in value.items()}
            if isinstance(value,list):return [adapt(item) for item in value]
            if isinstance(value,str):
                for source,destination in mappings:value=value.replace(source,destination)
            return value
        original=yaml.safe_load((ROOT/'Cluster'/CONFIG).read_text(encoding='utf-8'));mapped=adapt(original)
        expected_text=yaml.safe_dump(mapped,sort_keys=False)
        need(hashlib.sha256(expected_text.encode('utf-8')).hexdigest()==DEPLOYED_CONFIG_SHA,'Deterministic mapped original YAML bytes do not match the known native deployment hash')
        mapped_sha=hashlib.sha256(json.dumps(mapped,sort_keys=True,allow_nan=False).encode()).hexdigest()
        values={'PARAMS':params,'SOURCE_HASHES':sources,'REMOTE_ROOT':REMOTE_ROOT,'COMMIT':COMMIT,'UUID':UUID,'ORIGINAL_CONFIG_SHA':ORIGINAL_CONFIG_SHA,'DEPLOYED_CONFIG_SHA':DEPLOYED_CONFIG_SHA,'MAPPED_VALUES_SHA':mapped_sha}
        payload='\n'.join(key+'='+repr(value) for key,value in values.items())+'\n'+PROGRAM
        command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -']
        for index in range(2):
            if index:time.sleep(3)
            owner_guard(owner)
            done=subprocess.run(command,input=payload,capture_output=True,text=True,encoding='utf-8',timeout=40)
            need(done.returncode==0,'Exact remote observer failed rc='+str(done.returncode)+': '+done.stderr[-4000:])
            observations.append({'observed_at':datetime.now(timezone.utc).isoformat(),'data':json.loads(done.stdout)})
        first,second=[entry['data'] for entry in observations]
        need(first['start_ticks']==second['start_ticks']=='51717921' and first['start_ticks'].isdigit() and first['argv']==second['argv'] and first['fd1']==second['fd1'] and not first['errors'] and not second['errors'],'Original postlaunch PID/start/argv/log or native error observation changed')
        growth=(second['train_progress'][0],second['train_progress'][2])>(first['train_progress'][0],first['train_progress'][2])
        need(growth,'Native TRAIN growth not observed in this3second window; phase/identity evidence retained, not a training-failure or restart decision')
        owner_guard(owner)
        current=next(t for t in read(ROOT/'pipeline/queue.json')['gpu_queues']['server-4'] if t['id']=='M212-BCR')
        need(all(current.get(k)==task.get(k) for k in ('pid','config','log','gpu','code_commit','launch_verified')),'Registered task changed during observation')
        result={'recorded_at':datetime.now(timezone.utc).isoformat(),'experiment':'M212-BCR','code_commit':COMMIT,'physical_gpu':1,'owner':owner,'observations':observations,'same_exact_registered_process_and_native_TRAIN_growth':True,
                'first_postlaunch_start_ticks':first['start_ticks'],'start_identity_scope':'Original start51717921 captured after native launch in tick7526; now unchanged across both exact current samples. Historical source manifest is read-only provenance, never an execution lease for this tick.',
                'original_config_sha256':ORIGINAL_CONFIG_SHA,'deterministic_mapped_config_sha256':DEPLOYED_CONFIG_SHA,'mapped_values_sha256':mapped_sha,'GPU0':'NOT_QUERIED_NOT_USED','signals_sent':False,'restart_or_relaunch':False,'native_accuracy_efficacy':'UNKNOWN'}
        save_new(output,result)
        print(json.dumps({'status':'ACTUAL_EXACT_BCR_GPU1_TRAIN_GROWTH_OBSERVED','path':str(output),'sha256':sha(output),'pid':task['pid'],'start_ticks':first['start_ticks'],'progress':[first['train_progress'],second['train_progress']],'GPU0':'NOT_QUERIED_NOT_USED'}));return 0
    except Exception as error:
        failure={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'READONLY_PROGRESS_OBSERVER_DID_NOT_ESTABLISH_REQUIRED_PROOF','error_type':type(error).__name__,'error':str(error),'observations':observations,'signals_sent':False,'restart_or_relaunch':False,'training_failure_inferred':False,'GPU0':'NOT_QUERIED_NOT_USED'}
        save_new(failure_path,failure)
        print(json.dumps({'status':failure['status'],'failure_path':str(failure_path),'sha256':sha(failure_path),'reason':str(error),'training_failure_inferred':False}));return 2


if __name__=='__main__':raise SystemExit(main())
