"""Current-tick bounded authorization and live training/resource observations."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

os.environ.update(PROJECT_ROOT='D:/project',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
sys.path.insert(0,str(SKILL))
import foreground_tick as tick
ROOT=Path('D:/project/cluster_project');OUT=Path(__file__).resolve().parent
TOKEN='d7d79d6ab0c44cddac82381d94b21364'
GOAL='42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec'
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fle_r1'

def guard():
    owner=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert tick.digest(ROOT/'pipeline/goal.json')==GOAL
    return owner

def save(name,value):guard();tick.save(OUT/name,value)
def evidence(path):return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
def run(args,timeout=45):return subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
def ssh(program,host):
    result=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','songcl@'+host,
        shlex.join(['/usr/bin/python3','-B','-c',program])])
    assert result.returncode==0,result.stderr
    return json.loads(result.stdout)

def main():
    owner=guard();view=tick.load(ROOT/'pipeline/headless/.tick_model_view.json')
    assert view['mode']=='design' and view['research']['omitted_due_count']==0
    rows=[]
    for item in view['research']['shown']:
        result=run([sys.executable,'-B',str(SKILL/'foreground_tick.py'),'cluster_project','candidate','--id',item['id']])
        assert result.returncode==0,result.stderr
        candidate=json.loads(result.stdout)
        assert candidate['stage']=='blocked' and 'auxiliary' in candidate['blocker']
        rows.append({k:candidate.get(k) for k in ('id','stage','blocker_kind','blocker','retry_after','unblock_condition','next_action','wake_paths')})
    save('authorization_recheck.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'goal_sha256':GOAL,
        'servers_sha256':tick.digest(ROOT/'SERVERS.yaml'),'execution_mode_sha256':tick.digest(ROOT/'pipeline/execution_mode.json'),
        'scope':'four due existing auxiliary supervision holds only;current user mainline remains point-feature update;no new human authorization/evidence supplied',
        'new_authorization':False,'scientific_falsification':False,'new_native_calls':0,'new_candidates':0,'candidates':rows})
    experiment=tick.load(ROOT/'pipeline/experiments/M203-FLE.json')
    for label,host,gpu,hostname,uuid in (
        ('server4','192.168.1.115',0,'dl04-MS-7E06','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),
        ('server3','192.168.1.120',1,'sysu311-MS-7C59','GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0')):
        program=r'''import os,json,socket,subprocess,re
from pathlib import Path
from datetime import datetime,timezone
assert socket.gethostname()==%r
def output(args):return subprocess.check_output(args,universal_newlines=True,timeout=10).strip()
gpu=output(['nvidia-smi','-i',%r,'--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'])
assert gpu.split(',')[1].strip()==%r
contexts=output(['nvidia-smi','-i',%r,'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'])
record={'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'gpu':gpu,'contexts':contexts,'occupied':bool(contexts),'diagnostic_cuda_calls':0}
if %r=='server4':
 pid=%r
 record['training_pid_alive']=Path('/proc/'+str(pid)).exists()
 if record['training_pid_alive']:
  record['training_command']=Path('/proc/'+str(pid)+'/cmdline').read_bytes().replace(b'\0',b' ').decode()
  assert %r in record['training_command']
  paths=[]
  for fd in Path('/proc/'+str(pid)+'/fd').iterdir():
   try:
    target=os.readlink(str(fd))
    if 'Cluster_checkpoints' in target and target.endswith('.log'):paths.append(target)
   except OSError:pass
  assert len(paths)==1,paths
  log=Path(paths[0]);text=log.read_text(errors='replace')
  record['native_log_path']=str(log);record['log_mtime_ns']=log.stat().st_mtime_ns
  record['validation_miou']=[float(v) for v in re.findall(r'mIoU\s*:\s*([0-9.]+)',text)]
  record['epoch_steps']=re.findall(r'Epoch \[(\d+)/(\d+)\]\[(\d+)/(\d+)\]',text)[-2:]
  record['last_metric_lines']=[line for line in text.splitlines() if 'mIoU' in line][-4:]
 locks=Path('/proc/locks').read_text().splitlines();held={}
 for kind in ('training','diagnostic','exclusive'):
  p=Path('/tmp/cluster_project_gpu0_'+kind+'.lock')
  held[kind]=[int(line.split()[4]) for line in locks if line.split()[5].split(':')[-1]==str(p.stat().st_ino)] if p.exists() else []
 record['lock_owner_pids']=held
print(json.dumps(record))
'''%(hostname,str(gpu),uuid,str(gpu),label,experiment['pid'],NAME)
        value=ssh(program,host);save(label+'_live.json',value)
        print(json.dumps({'server':label,'at':value['observed_at'],'occupied':value['occupied'],
            'pid_alive':value.get('training_pid_alive'),'epoch_steps':value.get('epoch_steps'),'validation_miou':value.get('validation_miou')}))
    print(json.dumps({'due_authorization_holds_rechecked':len(rows),'new_candidates':0,'mode':view['mode'],'snapshot':view['generated_at'],'deadline':owner['deadline_at']}))

if __name__=='__main__':main()
