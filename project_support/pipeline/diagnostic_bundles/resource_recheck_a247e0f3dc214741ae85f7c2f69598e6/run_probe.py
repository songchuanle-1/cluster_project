"""One fresh identity-pinned resource probe under the current foreground lease."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick

ROOT = Path('D:/project/cluster_project')
TOKEN = 'a247e0f3dc214741ae85f7c2f69598e6'
BUNDLE = Path(__file__).resolve().parent


def guard():
    owner = tick.load(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token'] == TOKEN and owner['thread_id'] == os.environ['CODEX_THREAD_ID']
    assert tick.digest(ROOT / 'pipeline/goal.json') == '6a11a897c8378c48934590d7603b5cbd18cac2d43da40690e0a7c72080f5478c'
    assert (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds() > 180


REMOTE = r'''
import datetime,fcntl,json,subprocess
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
rows=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,name,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip().splitlines()
assert len(rows)==1,rows
cells=[s.strip() for s in rows[0].split(',')]
assert cells[0]=='0' and cells[1]=='GPU-7f82edb9-f620-8045-caea-a75232265cd1',cells
raw=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
processes=[]
for row in raw.splitlines():
    pid,memory=[s.strip() for s in row.split(',')]
    processes.append({'pid':int(pid),'used_memory_mib':int(memory)})
locks=[]
handles=[]
try:
    for path in ('/tmp/cluster_project_gpu0_m201_migration.lock','/tmp/cluster_project_gpu0_exclusive.lock','/tmp/cluster_project_gpu0_parameter_transport.lock'):
        try:
            handle=open(path,'rb')
        except FileNotFoundError:
            locks.append({'path':path,'status':'missing_not_recreated'})
            continue
        handles.append(handle)
        try:
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            locks.append({'path':path,'status':'acquired_for_probe'})
        except BlockingIOError:
            locks.append({'path':path,'status':'held_by_existing_owner'})
    result={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'hostname':'dl04-MS-7E06','gpu':{'index':0,'uuid':cells[1],'name':cells[2],
            'total_mib':int(cells[3]),'used_mib':int(cells[4]),'free_mib':int(cells[5]),'utilization_percent':int(cells[6])},
            'nvml_compute_processes':processes,'flocks':locks,
            'guards':{'no_other_nvml_context':not processes,'idle_equivalent_free_at_least_30000_mib':int(cells[5])>=30000,
                      'all_three_original_flocks_acquired':all(x['status']=='acquired_for_probe' for x in locks)},
            'cuda_allocations':0,'native_network_forwards':0,'optimizer_steps':0,
            'foreign_process_signals':0,'gpu_resets':0,'lock_deletions':0}
finally:
    for handle in reversed(handles):handle.close()
result['probe_flocks_released']=True
print(json.dumps(result))
'''


def main():
    guard()
    for name, source in (('work_before.json', ROOT / 'pipeline/research_work.json'),
                         ('memory_before.md', ROOT / 'pipeline/codex_memory.md')):
        target = BUNDLE / name
        assert not target.exists()
        target.write_bytes(source.read_bytes())
    path = BUNDLE / 'remote_probe.py'
    assert not path.exists()
    path.write_text(REMOTE, encoding='utf-8')
    run = subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12',
                          'server-4','/home/songcl/.conda/envs/project_cluster/bin/python','-B','-'],
                         input=REMOTE,text=True,encoding='utf-8',capture_output=True,timeout=90)
    guard()
    tick.save(BUNDLE / 'attempt.json', {'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),
              'script_sha256':tick.digest(path),'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
    if run.returncode:
        raise RuntimeError(run.stderr)
    result = {'token':TOKEN, **json.loads(run.stdout)}
    result['ready_for_original_capture_guards'] = all(result['guards'].values())
    tick.save(BUNDLE / 'resource_result.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
