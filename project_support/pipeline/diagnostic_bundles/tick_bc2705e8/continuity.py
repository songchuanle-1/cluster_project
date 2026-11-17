"""Bounded read-only native continuity sampling; no GPU computation or dispatch."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from datetime import datetime, timezone, timedelta

os.environ['PROJECT_ROOT']='D:/project'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
sys.path.insert(0,str(SKILL))
import foreground_tick as tick

ROOT=Path('D:/project/cluster_project')
OUT=Path(__file__).resolve().parent
TOKEN='bc2705e843ce4b60aa71fe326f14ff0d'
THREAD='01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
CID='m95-hierarchical-mask-feature-path-audit'

def guard():
    owner=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==THREAD==os.environ['CODEX_THREAD_ID']
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    return owner

def save(path,value):
    guard()
    tick.save(path,value)

def ev(path):
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}

guard()
experiment=tick.load(ROOT/'pipeline/experiments/M202-HDS.json')
assert experiment['status']=='running' and experiment['server']=='server-4' and str(experiment['gpu'])=='0'
assert experiment['pid']==1592337 and experiment['native_resume_verified']
old=tick.load(ROOT/'pipeline/diagnostic_bundles/m202_recovery_fded20f5/failure_snapshot.json')
constants={'PID':experiment['pid'],'LOG':experiment['log'],'CONFIG':experiment['config'],
    'REMOTE_ROOT':'/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b',
    'WORK':'/data/songcl/Project/Cluster_project/Cluster_checkpoints',
    'UUID':'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',
    'EXPECTED_HASHES':old['source_hashes']}
program='\n'.join(f'{key}={value!r}' for key,value in constants.items())+'\n'+r'''
import csv,datetime,hashlib,json,pathlib,re,socket,subprocess,time
assert socket.gethostname()=='dl04-MS-7E06'
root=pathlib.Path(REMOTE_ROOT)
proc=pathlib.Path('/proc')/str(PID)
def sample():
    args=proc.joinpath('cmdline').read_bytes().split(b'\0') if proc.exists() else []
    alive=bool(args and b'tools/train.py' in args and CONFIG.encode() in args)
    path=pathlib.Path(LOG)
    with path.open('rb') as handle:
        head=handle.read(16384)
        handle.seek(max(0,path.stat().st_size-131072))
        tail=handle.read(131072)
    text=tail.decode('utf-8',errors='replace')
    headtext=head.decode('utf-8',errors='replace')
    steps=re.findall(r'(Train|Val)\[(\d+)/(\d+)\]:[^\r\n]*?\|\s*(\d+)/(\d+)',text)
    fds=[]
    native_logs=[]
    if proc.exists():
        for item in (proc/'fd').iterdir():
            try:target=str(item.resolve(strict=True))
            except OSError:continue
            if target.startswith('/tmp/cluster_project_gpu0_') and target.endswith('.lock'):fds.append(target)
            if target.startswith(WORK+'/') and target.endswith('.log'):native_logs.append(target)
    return {'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'alive':alive,'args':[value.decode(errors='replace') for value in args if value],
        'native_steps':steps[-12:],'tail_bytes':len(tail),'tail_sha256':hashlib.sha256(tail).hexdigest(),
        'native_log_bytes':path.stat().st_size,'lifetime_lock_fds':sorted(set(fds)),
        'native_logs':sorted(set(native_logs)),
        'resume_lineage':re.findall(r'resume start_epoch:(\d+),best_miou:([0-9.eE+-]+),epochs_no_improve:(\d+)!',headtext),
        'crash_markers':[value for value in ('Traceback','CUDA out of memory','TypeError:','RuntimeError:') if value in text],
        'runtime_guard_present':'HDS_RUNTIME_READY=' in headtext}
first=sample()
time.sleep(7)
second=sample()
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=20)
gpu=next(csv.reader(row.splitlines()))
assert gpu[1].strip()==UUID
contexts=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=20)
contexts=[{'gpu_uuid':r[0].strip(),'pid':int(r[1]),'used_mib':int(r[2])} for r in csv.reader(contexts.splitlines()) if r and r[0].strip()==UUID]
hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in EXPECTED_HASHES}
source_matches=hashes==EXPECTED_HASHES
metrics=[]
for log in second['native_logs']:
    value=pathlib.Path(log).read_text(errors='replace')
    metrics.append({'path':log,'sha256':hashlib.sha256(value.encode()).hexdigest(),
        'miou':[float(x) for x in re.findall(r'(?<![A-Za-z])mIoU\s*:\s*([0-9.eE+-]+)',value)],
        'expression_counts':[int(x) for x in re.findall(r'Evaluate referring segmentation:\s*(\d+)',value)]})
def last(sample):
    if not sample['native_steps']:return None
    phase,epoch,total,step,count=sample['native_steps'][-1]
    return (int(epoch),1 if phase=='Train' else 2,int(step))
progress=bool(first['alive'] and second['alive'] and last(first) and last(second) and last(second)>last(first))
result={'observed_at':second['observed_at'],'hostname':socket.gethostname(),'pid':PID,
    'server':'server-4','physical_gpu':0,'gpu_uuid':UUID,'log':LOG,'samples':[first,second],
    'native_progress_increased':progress,'gpu0':{'used_mib':int(gpu[2]),'free_mib':int(gpu[3]),'util_percent':int(gpu[4])},
    'gpu0_contexts':contexts,'frozen_sources_match':source_matches,'source_file_count':len(hashes),
    'source_hashes':hashes,'current_native_scalar_logs':metrics,
    'remote_code_commit':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),
    'no_gpu_computation':True,'no_launch_or_restart':True}
print(json.dumps(result))
'''
command=shlex.join(['env','PYTHONDONTWRITEBYTECODE=1','/usr/bin/python3','-B','-c',program])
result=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
    '-o','ConnectTimeout=10','server-4',command],capture_output=True,text=True,
    encoding='utf-8',errors='replace',timeout=65)
assert result.returncode==0,result.stderr
data=json.loads(result.stdout)
last=data['samples'][-1]
data['healthy']=bool(data['native_progress_increased'] and data['frozen_sources_match']
    and len(last['lifetime_lock_fds'])==3 and not last['crash_markers'] and last['runtime_guard_present']
    and data['gpu0_contexts'] and all(row['pid']==1592337 for row in data['gpu0_contexts']))
save(OUT/'native_continuity.json',data)
assert data['healthy'],'New actionable continuity fault: inspect preserved native_continuity.json; do not relaunch.'
work=tick.load(ROOT/'pipeline/research_work.json')
candidate=next(c for c in work['candidates'] if c['id']==CID)
assert candidate['stage']=='training' and len(candidate['revision_history'])==2
candidate['evidence'].append(ev(OUT/'native_continuity.json'))
save(ROOT/'pipeline/research_work.json',work)
precise=[value for log in data['current_native_scalar_logs'] for value in log['miou']]
best=max([0.47346487641334534,*precise])
shanghai=datetime.fromisoformat(data['observed_at']).astimezone(timezone(timedelta(hours=8))).isoformat()
notes={'actions':[
    '本轮event由ledger_changed触发，begin快照'+guard()['generated_at']+'；无新终态、无到期候选。四个human scope holds尚未到期，未重复审查；储备4/2，准备预算0。',
    '后续只读采样时间'+shanghai+'，同一M202/PID1592337/server4物理GPU0两次间隔7秒采样，原生'+str(data['samples'][0]['native_steps'][-1])+'→'+str(last['native_steps'][-1])+'，确认实际进度增长。正确UUID、原三把生命周期flock及运行守卫保持，采样尾部无新异常。',
    '同一模型9个Python文件、1个部署YAML及native train/utils共'+str(data['source_file_count'])+'项哈希与恢复前冻结值一致；无源码/config/优化器/seed/schedule/修订/准入变更。',
    '当前run原生scalar日志精确mIoU序列'+str(precise)+'，继承epoch7的best后当前best='+str(best)+'。表达分母仅引用原生日志：'+str([log['expression_counts'] for log in data['current_native_scalar_logs']])+'；重复VAL不是独立场景样本，场景级置信区间/泛化和最终效益仍未知。',
    '本轮实际产出为1份当前native连续性及scalar记录；没有新候选、新模型、结构修订、GPU诊断、重新启动或恢复测试。上一轮48次CUDA与反向测试仅作历史背景，不重复计入本轮成果。TypeError历史根因及全程峰值显存仍未知。',
    '用量窗口仅为本轮begin至收据的本地可见记录，先前读取及最终回复不在内；当前最终值未知，以收据原始值为准，cache已含于input、reasoning已含于output，不重复相加，不当作账单。'
    ],'decisions':[
    '继续同一已准入主线训练及冻结评估方案，不因单轮VAL未刷新best而调参、停分支或把机制科学否定；早停仍按原协议。',
    '未出现需用户处置的新故障、完成或实质状态变化，按既有心跳规则保持安静。保留原TypeError及所有失败证据，不宣称根治。',
    '完整六段留档；写入时postflight尚未运行，必须finish成功并核实租约释放后才称本轮执行完成。不修改调度、通知策略、其他项目或恢复M201。'
    ]}
save(OUT/'report_notes.json',notes)
print(json.dumps({'observed_at':data['observed_at'],'healthy':data['healthy'],
    'samples_last':[sample['native_steps'][-1] for sample in data['samples']],
    'gpu0':data['gpu0'],'best_miou':best,'precise_current_run_miou':precise,
    'expression_counts':[log['expression_counts'] for log in data['current_native_scalar_logs']],
    'frozen_source_files':data['source_file_count'],'new_launches':0,'new_candidates':0},ensure_ascii=False,indent=2))
