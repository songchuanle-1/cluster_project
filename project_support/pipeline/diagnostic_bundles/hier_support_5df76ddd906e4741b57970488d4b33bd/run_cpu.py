"""Run only isolated constructed controls on the authorized host CPU."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick

ROOT = Path('D:/project/cluster_project')
TOKEN = '5df76ddd906e4741b57970488d4b33bd'
BUNDLE = Path(__file__).resolve().parent


def guard():
    owner = tick.load(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token'] == TOKEN and owner['thread_id'] == os.environ['CODEX_THREAD_ID']
    assert tick.digest(ROOT / 'pipeline/goal.json') == '6a11a897c8378c48934590d7603b5cbd18cac2d43da40690e0a7c72080f5478c'
    assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds() > 180


def main():
    guard()
    for name, source in (('goal_snapshot.json', ROOT / 'pipeline/goal.json'),
                         ('work_before.json', ROOT / 'pipeline/research_work.json'),
                         ('memory_before.md', ROOT / 'pipeline/codex_memory.md')):
        destination = BUNDLE / name
        assert not destination.exists()
        destination.write_bytes(source.read_bytes())
    paths = [BUNDLE / name for name in ('hier_support.py', 'test_cpu.py', 'prereg.md')]
    for path in paths[:2]:
        compile(path.read_text(encoding='utf-8'), str(path), 'exec')
    prototype, tests = [path.read_text(encoding='utf-8') for path in paths[:2]]
    program = '''
import datetime,hashlib,json,os,pathlib,subprocess,sys,types
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
source=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/hier_postprocess.py')
assert hashlib.sha256(source.read_bytes()).hexdigest()=='7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
module=types.ModuleType('hier_support')
sys.modules['hier_support']=module
exec(compile(PROTOTYPE,'<isolated-hierarchy-support>','exec'),module.__dict__)
exec(compile(TESTS,'<frozen-constructed-controls>','exec'),{'__name__':'__main__'})
'''
    program = 'PROTOTYPE=' + repr(prototype) + '\nTESTS=' + repr(tests) + '\n' + program
    remote = BUNDLE / 'remote_cpu.py'
    assert not remote.exists()
    remote.write_text(program, encoding='utf-8')
    tick.save(BUNDLE / 'frozen_sources.json', {'token':TOKEN,'frozen_at':datetime.now(timezone.utc).isoformat(),
              'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':tick.digest(p)} for p in paths]})
    run = subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12',
        'server-4','/home/songcl/.conda/envs/project_cluster/bin/python','-B','-'],
        input=program,text=True,encoding='utf-8',capture_output=True,timeout=300)
    guard()
    tick.save(BUNDLE / 'attempt.json', {'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),
        'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'script_sha256':tick.digest(remote)})
    lines = [line for line in run.stdout.splitlines() if line.startswith('HIER_SUPPORT_JSON=')]
    if not lines:
        print(run.stderr[-5000:])
        raise SystemExit(run.returncode or 2)
    result = {'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),**json.loads(lines[-1].split('=',1)[1])}
    tick.save(BUNDLE / 'result.json', result)
    print(json.dumps({key:result[key] for key in ('status','torch_version','check_count','failures','native_network_forwards','optimizer_steps','cuda_initialized')}, indent=2))
    print(json.dumps(result['metrics']['cpu_saved_tensor_storage'], indent=2))
    raise SystemExit(run.returncode)


if __name__ == '__main__':
    main()
