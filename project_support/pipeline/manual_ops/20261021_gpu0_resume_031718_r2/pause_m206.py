"""User-authorized exact-process pause and full-checkpoint resume queue transaction."""
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import msvcrt
import os
from pathlib import Path
import shlex
import subprocess
import sys

import yaml

ROOT = Path('D:/project/cluster_project')
OUT = Path(__file__).resolve().parent
THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
REQUEST = '断开一张卡的实验 先只使用GPU0 将断开的这一个任务给resume到训练队列中'
RID = OUT.name
RC = '/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
CID = 'hierarchy-coarse-conditioned-fine-channel-attention'
CONFIG = 'configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml'
COMMIT = '898ff63a2cf63d3895a9e86c0ee3d1e5b672b335'
ORIGINAL = '/data/songcl/Project/Cluster_project/Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca/20261021_051530/last.pth'
SNAPSHOT = '/data/songcl/Project/Cluster_project/pipeline/resume_snapshots/' + RID + '/20261021_051530/last.pth'


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, data, exclusive=False):
    path = Path(path)
    if exclusive:
        with path.open('x', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        return
    temporary = path.with_name(path.name + '.' + RID + '.tmp')
    with temporary.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
    os.replace(temporary, path)


def evidence(path):
    return {'path': Path(path).relative_to(ROOT).as_posix(), 'sha256': digest(path)}


def guard():
    assert os.environ['CODEX_THREAD_ID'] == THREAD
    execution = load(ROOT / 'pipeline/execution_mode.json')
    assert execution['target_thread_id'] == THREAD and execution['mode'] == 'foreground'
    assert not (ROOT / 'pipeline/headless/.foreground.lockdir').exists(), 'Foreground writer active'
    assert digest(ROOT / 'pipeline/goal.json') == GOAL


def remote(code, name, timeout=120, conda=False):
    guard()
    command = shlex.join(['/usr/bin/python3' if not conda else 'python', '-B', '-'])
    if conda:
        command = shlex.join(['bash', '-lc', 'source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && ' + command])
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
        '-o', 'ConnectTimeout=10', 'songcl@192.168.1.115', command],
        input="import socket\nassert socket.gethostname() == 'dl04-MS-7E06'\n" + code,
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
    data = {'observed_at': now(), 'returncode': result.returncode, 'stdout': result.stdout,
        'stderr': result.stderr, 'strict_pinned_ssh': True}
    if result.returncode == 0:
        data['data'] = json.loads(result.stdout)
    save(OUT / name, data, exclusive=True)
    assert result.returncode == 0, result.stderr[-3000:]
    return data['data']


def checkpoint():
    return remote('ORIGINAL='+repr(ORIGINAL)+'\nSNAPSHOT='+repr(SNAPSHOT)+'\n'+r'''
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
import hashlib,json,shutil,time,math,subprocess
from pathlib import Path
source=Path(ORIGINAL);destination=Path(SNAPSHOT)
base=Path('/data/songcl/Project/Cluster_project/pipeline/resume_snapshots').resolve()
assert destination.resolve().is_relative_to(base)
assert source.is_file() and not destination.exists()
assert shutil.disk_usage(destination.parent.parent.parent.parent).free > source.stat().st_size*2
destination.parent.mkdir(parents=True,exist_ok=False)
def info(path):
 s=path.stat();return (s.st_ino,s.st_size,s.st_mtime_ns)
attempts=[]
for attempt in range(3):
 candidate=destination.parent/('copy_'+str(attempt)+'.pth')
 before=info(source)
 with source.open('rb') as src,candidate.open('xb') as dst:
  shutil.copyfileobj(src,dst,8*1024*1024);dst.flush();os.fsync(dst.fileno())
 after=info(source)
 attempts.append({'before':before,'after':after,'stable':before==after})
 if before==after:
  candidate.rename(destination);break
else:raise RuntimeError('Checkpoint changed during every copy; no process stopped')
h=hashlib.sha256()
with destination.open('rb') as f:
 for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
import torch
assert not torch.cuda.is_initialized()
value=torch.load(str(destination),map_location='cpu',weights_only=False,mmap=True)
assert isinstance(value,dict)
assert all(key in value for key in ('model','optimizer','scheduler','meta')),list(value)
model=value['model'];optimizer=value['optimizer'];scheduler=value['scheduler'];meta=value['meta']
assert isinstance(model,dict) and model and isinstance(optimizer,dict) and optimizer
assert optimizer.get('state') and optimizer.get('param_groups')
assert isinstance(scheduler,dict) and scheduler and isinstance(meta,dict)
assert isinstance(meta.get('epoch'),int) and meta['epoch']>=1
assert isinstance(meta.get('epochs_no_improve'),int) and meta['epochs_no_improve']>=0
assert not torch.is_tensor(meta.get('best_miou')) or meta['best_miou'].numel()==1
best_value=float(meta['best_miou'])
assert math.isfinite(best_value)
assert all(not torch.is_tensor(v) or v.device.type=='cpu' for v in model.values())
assert not torch.cuda.is_initialized()
r={'source':str(source),'resume_from':str(destination),'checkpoint_sha256':h.hexdigest(),
 'bytes':destination.stat().st_size,'copy_attempts':attempts,'top_level_keys':list(value),
 'cpu_inspection':{'map_location':'cpu','load_succeeded':True,
 'model_state_present':True,'optimizer_state_present':True,'scheduler_state_present':True,
 'model_state_nonempty':True,'optimizer_state_nonempty':True,'scheduler_state_nonempty':True,
 'meta':{'epoch':int(meta['epoch']),'best_miou':best_value,'epochs_no_improve':int(meta['epochs_no_improve'])},
 'original_meta_scalar_types':{k:type(meta[k]).__name__ for k in ('epoch','best_miou','epochs_no_improve')},
 'optimizer_state_count':len(optimizer['state']),'optimizer_parameter_groups':len(optimizer['param_groups']),
 'scheduler_keys':list(scheduler),'cuda_initialized':False},
 'remote_code_commit':subprocess.check_output(['git','-C','/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1','rev-parse','HEAD'],text=True).strip()}
print(json.dumps(r))
''', 'checkpoint_capture.json', timeout=180, conda=True)


def stop_exact():
    return remote('ROOT='+repr(RC)+'\nCFG='+repr(CONFIG)+'\n'+r'''
import os,json,signal,time,subprocess,re
from pathlib import Path
target=3873690;protected=3842306
def proc(pid):
 p=Path('/proc')/str(pid)
 raw=(p/'stat').read_text();tail=raw[raw.rfind(')')+2:].split()
 return {'pid':pid,'state':tail[0],'ppid':int(tail[1]),'pgid':int(tail[2]),'sid':int(tail[3]),
  'starttime':tail[19],'cwd':os.readlink(p/'cwd'),
  'args':[x.decode() for x in (p/'cmdline').read_bytes().split(b'\0') if x],
  'uid':p.stat().st_uid}
t=proc(target);safe=proc(protected)
assert t['cwd']==safe['cwd']==ROOT and t['uid']==safe['uid']==os.getuid()
assert t['pgid']==t['sid']==target and safe['pgid']!=target
assert t['args']==['python','tools/train.py',CFG,'--gpu_ids','1','--num_gpus','1']
assert 'ctf_hcg_csort_mdc.yaml' in ' '.join(safe['args'])
inventory=subprocess.check_output(['nvidia-smi','-i','1','--query-gpu=index,uuid','--format=csv,noheader,nounits'],text=True).strip()
assert inventory=='1, GPU-7f82edb9-f620-8045-caea-a75232265cd1'
contexts_before=subprocess.check_output(['nvidia-smi','-i','1','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
assert any(x.split(',')[0].strip()==str(target) for x in contexts_before.splitlines())
members=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  row=proc(int(p.name))
  if row['pgid']==target:members.append(row)
 except (OSError,ValueError):pass
assert members and all(x['uid']==os.getuid() and x['sid']==target and x['cwd']==ROOT for x in members)
assert protected not in {x['pid'] for x in members}
assert proc(target)['starttime']==t['starttime']
os.killpg(target,signal.SIGTERM)
def alive_original(row):
 try:
  current=proc(row['pid'])
  return current['starttime']==row['starttime'] and current['state'] not in ('Z','X')
 except (FileNotFoundError,ProcessLookupError):return False
until=time.monotonic()+12
while any(alive_original(x) for x in members) and time.monotonic()<until:time.sleep(.25)
remaining=[x for x in members if alive_original(x)]
for row in remaining:
 current=proc(row['pid'])
 assert current['uid']==os.getuid() and current['pgid']==target and current['sid']==target
 os.kill(row['pid'],signal.SIGKILL)
until=time.monotonic()+8
while any(alive_original(x) for x in members) and time.monotonic()<until:time.sleep(.25)
assert not any(alive_original(x) for x in members),'Exact stop not confirmed; keep dispatch hold'
after_safe=proc(protected)
assert after_safe['starttime']==safe['starttime'] and after_safe['args']==safe['args'] and after_safe['cwd']==safe['cwd']
contexts_after=subprocess.check_output(['nvidia-smi','-i','1','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
assert not any(x.split(',')[0].strip()==str(target) for x in contexts_after.splitlines())
print(json.dumps({'stopped_pid':target,'stopped_group':target,'group_members':members,
 'sigkill_pids':[x['pid'] for x in remaining],'stop_confirmed':True,'gpu1_contexts_before':contexts_before,
 'gpu1_contexts_after':contexts_after,'protected_pid':protected,'protected_starttime':safe['starttime'],
 'protected_unchanged':True,'gpus_after':subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()}))
''', 'exact_stop_confirmation.json', timeout=45)


def main():
    guard()
    lock = (ROOT / '.pipeline.lock').open('a+b')
    lock.seek(0)
    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    try:
        guard()
        files = ['SERVERS.yaml','pipeline/queue.json','pipeline/running.json',
                 'pipeline/experiments/M206-CGCA.json','pipeline/research_work.json','pipeline/codex_memory.md']
        for relative in files:
            target = OUT / ('before_' + relative.replace('/','__'))
            with target.open('xb') as stream:
                stream.write((ROOT / relative).read_bytes())
        queue = load(ROOT / 'pipeline/queue.json')
        matches = [(srv,t) for srv,items in queue['gpu_queues'].items() for t in items if t.get('id')=='M206-CGCA']
        assert len(matches)==1 and matches[0][0]=='server-4'
        task = matches[0][1]
        assert task['status']=='running' and task['pid']==3873690 and str(task['gpu'])=='1'
        m205_before = copy.deepcopy(next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M205-MDC'))
        print('Capturing and CPU-validating complete checkpoint before stopping...',flush=True)
        captured = checkpoint()
        assert captured['remote_code_commit']==COMMIT
        common = dict(schema_version=1,purpose='cluster_native_resume',id='M206-CGCA',config=CONFIG,
            code_commit=COMMIT,server='server-4',gpu='0',remote_code_root=RC,
            resume_from=SNAPSHOT,checkpoint_sha256=captured['checkpoint_sha256'])
        auth_path = ROOT / ('pipeline/authorizations/gpu0_only_resume_' + RID + '.json')
        save(auth_path,{**common,'authorization_granted':True,'source':'human','human_request':REQUEST,
            'recorded_at':now(),'resource_scope':'Temporarily only server-4 physical GPU0; no server-3/GPU1 or server-4/GPU1 dispatch/diagnostics.',
            'preserve_existing_gpu0':'M205-MDC PID3842306 continues unchanged; M206 waits for GPU0.',
            'cold_start_allowed':False},exclusive=True)
        checkpoint_path = OUT / 'checkpoint_evidence.json'
        save(checkpoint_path,{**common,'cpu_inspection':captured['cpu_inspection'],
            'source_checkpoint':ORIGINAL,'frozen_checkpoint_bytes':captured['bytes'],
            'capture':evidence(OUT/'checkpoint_capture.json'),'recorded_at':now()},exclusive=True)
        old = copy.deepcopy(task)
        paused = {k:old.get(k) for k in ('gpu','pid','log','launched','launch_verified','launch_verification','claimed_gpu')}
        paused.update(paused_at=now(),reason=REQUEST,checkpoint=SNAPSHOT,
            checkpoint_sha256=captured['checkpoint_sha256'],meta=captured['cpu_inspection']['meta'])
        task.update(status='waiting',server='server-4',gpu='0',dispatch_phase='pause_stop_pending',
            dispatch_hold='User pause transaction: full-checkpoint native resume only; verify exact stop and resume launcher before dispatch.',
            resume_from=SNAPSHOT,resume_authorization=evidence(auth_path),
            resume_checkpoint_evidence=evidence(checkpoint_path),paused_run=paused,
            launch_verified=False,launch_verification='paused_pending_resume')
        for key in ('pid','log','launched','claimed_gpu'):
            task.pop(key,None)
        save(ROOT/'pipeline/queue.json',queue)
        servers_path=ROOT/'SERVERS.yaml'
        original=servers_path.read_text(encoding='utf-8')
        updated=original.replace('allowed_gpus: [1]   # Latest user: retain GPU1 alongside server-4 GPU0.',
            'allowed_gpus: []   # User 2026-10-21: temporarily only server-4 GPU0.')
        updated=updated.replace('allowed_gpus: [0, 1]   # User 2026-10-19: GPU1 experiments authorized; preserve GPU0 M204.',
            'allowed_gpus: [0]   # User 2026-10-21: GPU0 only; M206 full-state resume waits here.')
        parsed=yaml.safe_load(updated)
        assert parsed['servers']['server-4']['allowed_gpus']==[0]
        assert parsed['servers']['server-3']['allowed_gpus']==[]
        # Keep the previously authorized server-3 inventory but disable its dispatch.
        section=updated.index('  server-3:')
        end=updated.index('  server-4:',section)
        block=updated[section:end]
        assert block.count('dispatch_enabled: true')==1
        updated=updated[:section]+block.replace('dispatch_enabled: true','dispatch_enabled: false',1)+updated[end:]
        temporary=servers_path.with_name('SERVERS.'+RID+'.tmp')
        with temporary.open('x',encoding='utf-8',newline='\n') as stream:stream.write(updated)
        os.replace(temporary,servers_path)
        print('Checkpoint verified; exact M206 process-group SIGTERM next. GPU0 protected.',flush=True)
        stopped=stop_exact()
        assert stopped['stop_confirmed'] and stopped['protected_unchanged']
        task.update(dispatch_phase='resume_waiting',paused_at=now())
        task['paused_run']['stop_confirmation']=evidence(OUT/'exact_stop_confirmation.json')
        task['dispatch_hold']='Resume launcher verification pending; never cold-start this waiting task.'
        assert next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M205-MDC')==m205_before
        save(ROOT/'pipeline/queue.json',queue)
        running=load(ROOT/'pipeline/running.json')
        assert running['server-4']['1']=='M206-CGCA' and running['server-4']['0']=='M205-MDC'
        del running['server-4']['1']
        save(ROOT/'pipeline/running.json',running)
        exp_path=ROOT/'pipeline/experiments/M206-CGCA.json'
        exp=load(exp_path)
        exp.update(status='waiting',server='server-4',gpu='0',paused_run=task['paused_run'],
            resume_from=SNAPSHOT,resume_authorization=task['resume_authorization'],
            resume_checkpoint_evidence=task['resume_checkpoint_evidence'],
            launch_verified=False,launch_verification='paused_pending_resume')
        for key in ('pid','log','launched'):
            exp.pop(key,None)
        exp.setdefault('history',[]).append({'ts':now(),'action':'user_paused_for_gpu0_resume',
            'from_gpu':'1','to_gpu':'0','checkpoint':SNAPSHOT,'meta':captured['cpu_inspection']['meta'],
            'stop_confirmation':evidence(OUT/'exact_stop_confirmation.json')})
        save(exp_path,exp)
        work=load(ROOT/'pipeline/research_work.json')
        candidate=next(x for x in work['candidates'] if x['id']==CID)
        assert candidate['stage']=='training'
        candidate['training_status']='paused_waiting_resume'
        candidate['next_action']='User paused M206 on GPU1. Resume SAME admitted source/full frozen checkpoint on server4 GPU0 only after M205 releases it; preserve optimizer/scheduler/epoch/best/patience. Do not cold-start.'
        for artifact in (auth_path,checkpoint_path,OUT/'exact_stop_confirmation.json'):
            candidate['evidence'].append(evidence(artifact))
        save(ROOT/'pipeline/research_work.json',work)
        save(OUT/'pause_transaction.json',{'recorded_at':now(),'user_request':REQUEST,
            'status':'STOPPED_AND_QUEUED_WITH_RESUME_HOLD','same_experiment':'M206-CGCA',
            'resume_from':SNAPSHOT,'checkpoint_meta':captured['cpu_inspection']['meta'],
            'authorization':evidence(auth_path),'checkpoint_evidence':evidence(checkpoint_path),
            'stop_confirmation':evidence(OUT/'exact_stop_confirmation.json'),
            'gpu0_m205_preserved':True,'goal_unchanged':digest(ROOT/'pipeline/goal.json')==GOAL},exclusive=True)
        print(json.dumps({'status':'STOPPED_AND_QUEUED_WITH_RESUME_HOLD','checkpoint_meta':captured['cpu_inspection']['meta'],
            'resume_authorization':evidence(auth_path),'resume_checkpoint_evidence':evidence(checkpoint_path),
            'gpu1_released':True,'gpu0_m205_preserved':True},ensure_ascii=False),flush=True)
    finally:
        lock.close()


if __name__=='__main__':
    main()
