"""Remote operations sent on stdin by the guarded adapter, never run on import.

No scheduling, killing, cleanup, lease renewal, checkout or shared-source edits.
Reconcile only reads an exact existing stage, request identities and /proc.
"""
import base64
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys

PARENT=Path('/data/songcl/Project/Cluster_project/pipeline')
ROOT=Path('/data/songcl/Project/Cluster_project/Cluster_psc_20261106')
GPU_UUIDS={0:'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'}
GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
CANDIDATE='hierarchy-native-spatial-dirichlet-composition'
COMMIT='f6257de79148581334ee495e6e2d60ccb525457c'
RESOURCE_AUTHORIZATION={'path': 'pipeline/authorizations/server4_gpu0_overlay_20261104.json', 'sha256': '783ffc27d48872940c2e15adcb85f6bb5f9b94492a8abd88694799f483d20e88'}
RESOURCE_MEMORY_POLICY={'allow_external_overlay': True, 'minimum_free_mib_before_launch': 20000, 'max_project_tasks_per_gpu': 1, 'cooperative_lock_kinds': ['training', 'diagnostic', 'exclusive'], 'external_contexts': 'record_preserve_no_signals', 'measurement_scope': 'authorized_overlay_potentially_contended_not_exclusive'}


def check(condition,message):
    if not condition: raise RuntimeError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()


def write(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False)


def read(path):return json.loads(Path(path).read_text())


def identity(binding,request):
    return {'project':'cluster_project','candidate_id':CANDIDATE,'code_commit':COMMIT,
        'stage':binding['stage'],'token':binding['owner']['token'],'request_id':request['request_id'],
        'operation':request['operation'],'physical_gpu':binding['physical_gpu'],
        'gpu_uuid':binding['gpu_uuid'],'native_manifest_sha256':binding['native_manifest_sha256']}


def binding_stage(binding):
    check(binding['project']=='cluster_project' and binding['candidate_id']==CANDIDATE and binding['code_commit']==COMMIT,'Foreign binding')
    token=binding['owner']['token'];check(re.fullmatch(r'[0-9a-f]{32}',token) is not None,'Token unknown')
    stage=Path(binding['stage']);check(stage==PARENT/('nsd_'+token[:8]+'_gpu'+str(binding['physical_gpu'])),'Unexpected stage')
    check(type(binding['physical_gpu']) is int and binding['physical_gpu'] in GPU_UUIDS,'Only physical GPU0 is permitted')
    check(binding['gpu_uuid']==GPU_UUIDS[binding['physical_gpu']],'UUID mismatch')
    check(binding.get('resource_authorization')==RESOURCE_AUTHORIZATION and binding.get('resource_memory_policy')==RESOURCE_MEMORY_POLICY,'Overlay binding policy mismatch')
    check(not stage.exists() or stage.resolve().parent==PARENT.resolve(),'Stage is an unexpected symlink/foreign path')
    return stage


def probe(gpu):
    check(type(gpu) is int and gpu in GPU_UUIDS,'Only physical GPU0 is permitted')
    index=str(gpu)
    row=subprocess.check_output(['nvidia-smi','-i',index,'--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
    values=[x.strip() for x in row.split(',')];check(len(values)==5 and values[:2]==[index,GPU_UUIDS[gpu]],'GPU inventory identity mismatch')
    used,total,utilization=int(values[2]),int(values[3]),int(values[4]);check(0<=used<=total,'GPU memory inventory unavailable')
    raw=subprocess.check_output(['nvidia-smi','-i',index,'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
    contexts=[]
    for line in raw.splitlines():
        fields=[x.strip() for x in line.split(',')]
        contexts.append({'pid':int(fields[0]),'used_memory_mib':fields[1]})
    locks={}
    for kind in ('training','diagnostic','exclusive'):
        with open('/tmp/cluster_project_gpu'+index+'_'+kind+'.lock','a+b') as handle:
            try:
                fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]='available'
            except BlockingIOError:locks[kind]='busy'
    commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True,timeout=10).strip()
    free=total-used
    return {'server_id':'server-4','hostname':socket.gethostname(),'root':str(ROOT),
        'runtime_code_commit':commit,'physical_gpu':gpu,'gpu_uuid':GPU_UUIDS[gpu],
        'memory_used_mib':used,'memory_total_mib':total,'memory_free_mib':free,
        'utilization_percent':utilization,'contexts':contexts,'locks':locks,
        'idle':not contexts and used<1024 and utilization<10,
        'usable_under_current_overlay_policy':free>=RESOURCE_MEMORY_POLICY['minimum_free_mib_before_launch'] and all(v=='available' for v in locks.values()),
        'resource_authorization':RESOURCE_AUTHORIZATION,'resource_memory_policy':RESOURCE_MEMORY_POLICY,
        'measurement_scope':RESOURCE_MEMORY_POLICY['measurement_scope'],'exclusive_measurement_claimed':False,
        'observed_at':datetime.now(timezone.utc).isoformat()}


def require_fresh(binding,minimum=300):
    owner=binding['owner'];generated=datetime.fromisoformat(owner['generated_at']);deadline=datetime.fromisoformat(owner['deadline_at'])
    now=datetime.now(timezone.utc)
    check(generated.tzinfo is not None and deadline.tzinfo is not None and generated<=now<deadline,'Execution binding expired/future')
    check(0<(deadline-generated).total_seconds()<=3600 and (deadline-now).total_seconds()>minimum,'Insufficient unchanged execution deadline')


def require_usable(binding):
    found=probe(binding['physical_gpu'])
    check(binding.get('resource_authorization')==RESOURCE_AUTHORIZATION and binding.get('resource_memory_policy')==RESOURCE_MEMORY_POLICY,'Overlay authorization/memory policy mismatch')
    check(found['usable_under_current_overlay_policy'] and found['memory_free_mib']>=RESOURCE_MEMORY_POLICY['minimum_free_mib_before_launch'] and all(v=='available' for v in found['locks'].values()),'GPU0 available memory/project cooperative locks are insufficient; external tasks remain untouched')
    check(found['runtime_code_commit']==binding['runtime_code_commit'],'Runtime checkout changed')
    return found


def native_verify(stage,binding):
    check(sha(stage/'native_manifest.json')==binding['native_manifest_sha256'],'Manifest SHA mismatch')
    check(sha(stage/'execution_lease.json')==binding['execution_lease_sha256'],'Lease SHA mismatch')
    # Verify frozen native runtime via manifest before importing any stage code.
    manifest=read(stage/'native_manifest.json')
    check(manifest.get('resource_authorization')==binding['resource_authorization']==RESOURCE_AUTHORIZATION and manifest.get('resource_memory_policy')==binding['resource_memory_policy']==RESOURCE_MEMORY_POLICY,'Manifest overlay/memory policy mismatch')
    for name,expected in manifest['diagnostic_files'].items():
        path=(stage/name).resolve();check(path.is_relative_to(stage.resolve()),'Diagnostic path escape')
        check(sha(path)==expected,'Diagnostic asset mismatch: '+name)
    check(manifest['current_token']==binding['owner']['token'] and manifest['stage']==str(stage),'Manifest identity mismatch')
    sys.path.insert(0,str(stage))
    runtime=importlib.import_module('native_runtime')
    runtime.verify()


def stage_operation(payload):
    binding=payload['binding'];request=payload['request'];stage=binding_stage(binding)
    check(request==identity(binding,request),'Stage request identity mismatch')
    require_fresh(binding);require_usable(binding)
    check(not stage.exists(),'Stage exists; reconcile original request, never replay/delete')
    stage.mkdir(exist_ok=False)
    write(stage/'stage_request.json',request)
    for name,entry in payload['files'].items():
        path=(stage/name).resolve();check(path.is_relative_to(stage.resolve()),'Stage path escape')
        check(name not in ('stage_request.json','stage_completed.json'),'Reserved stage file')
        data=base64.b64decode(entry['base64'],validate=True)
        check(hashlib.sha256(data).hexdigest()==entry['sha256'],'Payload hash mismatch')
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(data)
    native_verify(stage,binding)
    result={'identity':identity(binding,request),'certainty':'terminal','verified':True,
        'stage':str(stage),'native_manifest_sha256':sha(stage/'native_manifest.json'),
        'gpu_execution':False,'native_execution':False}
    write(stage/'stage_completed.json',result)
    return result


def process_info(pid):
    path=Path('/proc')/str(pid)
    try:
        command=(path/'cmdline').read_bytes().split(b'\0')
        command=[part.decode(errors='replace') for part in command if part]
        # stat comm can contain spaces; fields after its final ')' start at field3.
        fields=(path/'stat').read_text().rsplit(')',1)[1].split()
        return {'pid':int(pid),'start_ticks':fields[19],'state':fields[0],'argv':command}
    except (FileNotFoundError,ProcessLookupError,PermissionError):return None


def exact_workers(stage,mode=None,target=None):
    matches=[]
    worker=str(stage/'worker.py');lease=str(stage/'execution_lease.json')
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():continue
        info=process_info(int(path.name))
        if not info:continue
        argv=info['argv']
        if worker not in argv or lease not in argv:continue
        if mode is not None and not any(argv[i:i+2]==['--mode',mode] for i in range(len(argv)-1)):continue
        if target is not None and not any(argv[i:i+2]==['--target',target] for i in range(len(argv)-1)):continue
        matches.append(info)
    return matches


def run_operation(payload):
    binding=payload['binding'];request=payload['request'];stage=binding_stage(binding)
    mode=request['mode'];target=request['target']
    check((mode,target) in [('smoke','champion'),('smoke','candidate'),('resources','champion'),('resources','candidate')],'Unsupported worker request')
    for key,value in identity(binding,request).items():check(request[key]==value,'Worker request identity mismatch')
    check(read(stage/'stage_completed.json')['verified'] is True,'Stage was not verified')
    require_fresh(binding);require_usable(binding);native_verify(stage,binding)
    require_fresh(binding)
    prefix=mode+'_'+target
    request_path=stage/(prefix+'_request.json')
    check(not request_path.exists(),'Worker request already exists; no replay')
    check(not exact_workers(stage),'An exact-stage worker is already running')
    write(request_path,request)
    command=[sys.executable,'-B',str(stage/'worker.py'),'--lease',str(stage/'execution_lease.json'),'--mode',mode,'--target',target]
    stdout=stage/(prefix+'_stdout.log');stderr=stage/(prefix+'_stderr.log')
    with stdout.open('xb') as out,stderr.open('xb') as err:
        process=subprocess.Popen(command,stdout=out,stderr=err,cwd=str(stage),start_new_session=False)
        started={'identity':identity(binding,request),'mode':mode,'target':target,'pid':process.pid,
            'process_identity':process_info(process.pid),'command':command,'stdout':str(stdout),'stderr':str(stderr)}
        write(stage/(prefix+'_started.json'),started)
        try:returncode=process.wait(timeout=660)
        except subprocess.TimeoutExpired:
            # Do not kill or relaunch. The frozen worker retains its own alarm.
            return {'identity':identity(binding,request),'certainty':'uncertain','wait_timed_out':True,
                'pid':process.pid,'process_identity':process_info(process.pid),'stage':str(stage)}
    result_path=stage/(prefix+'_result.json')
    result={'identity':identity(binding,request),'certainty':'terminal','returncode':returncode,
        'pid':process.pid,'original_process_identity':started['process_identity'],'command':command,
        'result_sha256':sha(result_path) if result_path.exists() else None,
        'result':read(result_path) if result_path.exists() else None,
        'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr)}
    write(stage/(prefix+'_completed.json'),result)
    return result


def command_matches(command,stage,mode,target):
    expected=['-B',str(stage/'worker.py'),'--lease',str(stage/'execution_lease.json'),'--mode',mode,'--target',target]
    return (isinstance(command,list) and len(command)==len(expected)+1
        and re.fullmatch(r'python(?:\d+(?:\.\d+)*)?',Path(command[0]).name) is not None and command[1:]==expected)


def result_matches(result,mode,target):
    package='framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'+('_nsd' if target=='candidate' else '')
    expected={'candidate_id':CANDIDATE,'code_commit':COMMIT,'goal_sha256':GOAL,'mode':mode,'target':target,'model_package':package}
    return isinstance(result,dict) and all(result.get(k)==v for k,v in expected.items())


def reconcile_operation(payload):
    binding=payload['binding'];stage=binding_stage(binding);request_id=payload.get('request_id')
    found={'stage':str(stage),'exists':stage.exists(),'native_manifest_sha256':None,
        'binding_token':binding['owner']['token'],'read_only':True,'requests':[],'workers':exact_workers(stage)}
    if not stage.exists():return found
    manifest=stage/'native_manifest.json'
    if manifest.exists():found['native_manifest_sha256']=sha(manifest)
    for name in ['stage_request.json']+[m+'_'+t+'_request.json' for m in ('smoke','resources') for t in ('champion','candidate')]:
        path=stage/name
        if not path.exists():continue
        try:request=read(path)
        except (ValueError,OSError) as error:
            found['requests'].append({'file':name,'read_error':str(error),'identity_matches':False});continue
        if request_id is not None and request.get('request_id')!=request_id:continue
        prefix=name[:-len('_request.json')]
        mode,target=(None,None) if prefix=='stage' else tuple(prefix.split('_',1))
        try:expected=identity(binding,request)
        except (KeyError,TypeError) as error:
            found['requests'].append({'file':name,'request':request,'read_error':str(error),'identity_matches':False});continue
        identity_ok=all(request.get(k)==v for k,v in expected.items())
        if prefix=='stage':identity_ok=identity_ok and request.get('operation')=='stage'
        else:identity_ok=identity_ok and request.get('operation')=='run' and request.get('mode')==mode and request.get('target')==target
        item={'file':name,'request':request,'request_sha256':sha(path),'identity_matches':identity_ok}
        completed=stage/('stage_completed.json' if prefix=='stage' else prefix+'_completed.json')
        started=stage/(prefix+'_started.json');result=stage/(prefix+'_result.json')
        if started.exists():
            info=read(started);item['started']=info
            original=info.get('process_identity');current=process_info(info['pid'])
            item['current_pid_identity']=current
            item['started_identity_matches']=info.get('identity')==expected and info.get('mode')==mode and info.get('target')==target
            item['started_command_matches']=command_matches(info.get('command'),stage,mode,target)
            item['original_pid_still_same']=bool(original and current and original['start_ticks']==current['start_ticks']
                and original['argv']==current['argv'] and command_matches(current['argv'],stage,mode,target)
                and item['started_identity_matches'] and item['started_command_matches'])
        if completed.exists():
            value=read(completed);item['completed']=value;item['completed_sha256']=sha(completed)
            item['completed_identity_matches']=value.get('identity')==expected
            if prefix!='stage':
                item['completed_command_matches']=command_matches(value.get('command'),stage,mode,target)
                item['completed_result_identity_matches']=result_matches(value.get('result'),mode,target)
        if result.exists():
            item['result']=read(result);item['result_sha256']=sha(result)
            item['result_identity_matches']=result_matches(item['result'],mode,target)
        found['requests'].append(item)
    index=str(binding['physical_gpu'])
    inventory=subprocess.check_output(['nvidia-smi','-i',index,'--query-gpu=index,uuid','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
    found['gpu_inventory']=inventory
    found['gpu_identity_matches']=[x.strip() for x in inventory.split(',')]==[index,GPU_UUIDS[binding['physical_gpu']]]
    found['compute_contexts']=subprocess.check_output(['nvidia-smi','-i',index,
        '--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
    return found


def dispatch(operation,payload):
    check(socket.gethostname()=='dl04-MS-7E06','Pinned server hostname mismatch')
    if operation=='probe':return probe(payload['physical_gpu'])
    if operation=='stage':return stage_operation(payload)
    if operation=='run':return run_operation(payload)
    if operation=='reconcile':return reconcile_operation(payload)
    raise RuntimeError('Unsupported operation')
