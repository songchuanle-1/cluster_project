"""Run only source-bound diagnostics under the current foreground lease."""
import argparse
import ast
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import yaml

ROOT=Path('D:/project/cluster_project')
BUNDLE=Path(__file__).resolve().parent
PRIOR=ROOT/'pipeline/diagnostic_bundles/hier_native_4dcb0e69d411448686fdd787bcbc6a06'
TOKEN='cc39552e325049f5b8ac15dd3e055b06'
GOAL_SHA='3b96e04fae2945649ce42ce65674ff5dbf6c7ce24e19123093ecdebc71d4c102'
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick

def guard(reserve=120):
    owner=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']
    assert owner['deadline_at']=='2026-10-16T02:43:30.123361+00:00'
    assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>reserve
    assert tick.digest(ROOT/'pipeline/goal.json')==GOAL_SHA
    servers=yaml.safe_load((ROOT/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']
    assert servers['server-3']['allowed_gpus']==[1] and servers['server-3']['dispatch_enabled']
    assert servers['server-3']['host']=='192.168.1.120'
    assert servers['server-3']['expected_hostname']=='sysu311-MS-7C59'
    assert not servers['server-4']['allowed_gpus'] and not servers['server-6']['allowed_gpus']
    return owner

class Instrument(ast.NodeTransformer):
    def __init__(self):
        self.insertions=0
        self.result_insertions=0
    def visit_Assign(self,node):
        self.generic_visit(node)
        if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='model':
            self.insertions+=1
            return ast.parse((BUNDLE/'trace_setup.py').read_text(encoding='utf-8')).body+[node]
        if any(isinstance(target,ast.Name) and target.id=='result' for target in node.targets) and isinstance(node.value,ast.Dict):
            self.result_insertions+=1
            node.value.keys.extend([ast.Constant('module_trace'),ast.Constant('core_readout_calls')])
            node.value.values.extend([ast.Name('memory_trace',ast.Load()),ast.Name('core_readout_calls',ast.Load())])
        return node

def initialize():
    guard()
    assert not (BUNDLE/'work_before.json').exists()
    for source,name in ((ROOT/'pipeline/research_work.json','work_before.json'),
        (ROOT/'pipeline/codex_memory.md','memory_before.md'),(ROOT/'pipeline/goal.json','goal_snapshot.json'),
        (ROOT/'SERVERS.yaml','servers_snapshot.yaml'),(PRIOR/'native_memory_probe.py','native_memory_frozen.py')):
        shutil.copyfile(source,BUNDLE/name)
    tick.save(BUNDLE/'initialization.json',{'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),
        'goal_sha256':GOAL_SHA,'prereg_sha256':tick.digest(BUNDLE/'prereg.md'),
        'native_memory_source_sha256':tick.digest(BUNDLE/'native_memory_frozen.py'),
        'instrumentation_sha256':tick.digest(BUNDLE/'trace_setup.py'),'new_training':0})
    print('Current lease snapshots and matched trace preregistration saved.')

def run(name,timeout):
    owner=guard()
    attempt=BUNDLE/(name+'_attempt.json')
    assert not attempt.exists(),'Never overwrite an earlier attempt.'
    condition=name.removeprefix('trace_')
    assert condition in ('baseline','canonical')
    source=BUNDLE/'native_memory_frozen.py'
    transform=Instrument()
    tree=transform.visit(ast.parse(source.read_text(encoding='utf-8')))
    assert transform.insertions==transform.result_insertions==1
    payload=ast.unparse(ast.fix_missing_locations(tree))
    compile(payload,'<matched-allocation-trace>','exec')
    timeout=min(timeout,int((datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds())-120)
    assert timeout>20
    prefix='import signal\nsignal.alarm('+str(timeout-15)+')\n'
    prefix+='FOREGROUND_TOKEN='+repr(TOKEN)+'\nFOREGROUND_DEADLINE='+repr(owner['deadline_at'])+'\n'
    prefix+='MEMORY_CONDITION='+repr(condition)+'\n'
    dependencies={'frozen_source':tick.digest(source),'trace_setup':tick.digest(BUNDLE/'trace_setup.py')}
    if condition=='canonical':
        core=PRIOR/'canonical_readout.py'
        assert tick.digest(core)=='18ce8dde33c99f3f4fa7efd037cf38d54b9978f4f996429ec9f9bfcddffa5d93'
        prefix+='CANONICAL_SOURCE='+repr(core.read_text(encoding='utf-8'))+'\n'
        dependencies['canonical_core']=tick.digest(core)
    process=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
        'server-3','/home/songcl/.conda/envs/3d-stmn/bin/python','-B','-'],input=prefix+payload,
        text=True,encoding='utf-8',capture_output=True,timeout=timeout)
    guard()
    tick.save(attempt,{'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),
        'dependencies_sha256':dependencies,'returncode':process.returncode,'stdout':process.stdout,'stderr':process.stderr})
    rows=[json.loads(line.split('=',1)[1]) for line in process.stdout.splitlines() if line.startswith('HIER_NATIVE_RESULT=')]
    if rows:
        assert len(rows)==1
        tick.save(BUNDLE/(name+'_result.json'),{'token':TOKEN,'attempt_sha256':tick.digest(attempt),**rows[0]})
        print(json.dumps({'condition':condition,'outcome':rows[0]['outcome'],
            'core_readout_calls':rows[0]['core_readout_calls'],'trace_rows':len(rows[0]['module_trace']),
            'trace_tail':rows[0]['module_trace'][-14:]},ensure_ascii=False))
    else:
        print(process.stdout[-5000:])
    print(process.stderr[-5000:])
    print('returncode='+str(process.returncode))
    raise SystemExit(process.returncode)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('name',choices=['init','trace_baseline','trace_canonical'])
    parser.add_argument('--timeout',type=int,default=240)
    args=parser.parse_args()
    if args.name=='init':initialize()
    else:run(args.name,args.timeout)
