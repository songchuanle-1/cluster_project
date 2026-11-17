"""Execute bounded, saved diagnostics under this foreground lease only."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import yaml

ROOT=Path('D:/project/cluster_project')
BUNDLE=Path(__file__).resolve().parent
TOKEN='4dcb0e69d411448686fdd787bcbc6a06'
GOAL_SHA='3b96e04fae2945649ce42ce65674ff5dbf6c7ce24e19123093ecdebc71d4c102'
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick

def guard():
    owner=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']
    assert owner['deadline_at']=='2026-10-16T01:42:18.186501+00:00'
    assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>120
    assert tick.digest(ROOT/'pipeline/goal.json')==GOAL_SHA
    servers=yaml.safe_load((ROOT/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']
    assert servers['server-3']['allowed_gpus']==[1] and servers['server-3']['dispatch_enabled']
    assert not servers['server-4']['allowed_gpus'] and not servers['server-6']['allowed_gpus']
    return owner

def main():
    p=argparse.ArgumentParser()
    p.add_argument('name',choices=['native_support_probe','native_task_probe','runtime_probe','target_inventory','native_suffix_probe','canonical_tests','readout_bench','canonical_suffix_probe','memory_baseline','memory_canonical'])
    p.add_argument('--timeout',type=int,default=300)
    args=p.parse_args()
    owner=guard()
    source=BUNDLE/('native_memory_probe.py' if args.name in ('memory_baseline','memory_canonical') else args.name+'.py')
    text=source.read_text(encoding='utf-8')
    compile(text,str(source),'exec')
    attempt=BUNDLE/(args.name+'_attempt.json')
    assert not attempt.exists(),'Never overwrite prior attempts.'
    timeout=min(args.timeout,int((datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds())-120)
    assert timeout>10
    dependencies={}
    prefix=''
    if args.name in ('canonical_tests','readout_bench','canonical_suffix_probe','memory_canonical'):
        core=BUNDLE/'canonical_readout.py'
        prefix+='CANONICAL_SOURCE='+repr(core.read_text(encoding='utf-8'))+'\n'
        dependencies[core.name]=tick.digest(core)
    if args.name in ('memory_baseline','memory_canonical'):
        prefix+='MEMORY_CONDITION='+repr(args.name.removeprefix('memory_'))+'\n'
    if args.name=='canonical_tests':
        original=ROOT/'pipeline/diagnostic_bundles/hier_support_5df76ddd906e4741b57970488d4b33bd'
        for label,name in (('REFERENCE_SOURCE','hier_support.py'),('FIXTURE_SOURCE','test_cpu.py')):
            path=original/name
            prefix+=label+'='+repr(path.read_text(encoding='utf-8'))+'\n'
            dependencies[name]=tick.digest(path)
    payload='import signal\nsignal.alarm('+str(max(1,timeout-15))+')\nFOREGROUND_TOKEN='+repr(TOKEN)+'\nFOREGROUND_DEADLINE='+repr(owner['deadline_at'])+'\n'+prefix+text
    process=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
        'server-3','/home/songcl/.conda/envs/3d-stmn/bin/python','-B','-'],input=payload,
        text=True,encoding='utf-8',capture_output=True,timeout=timeout)
    guard()
    tick.save(attempt,{'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),
        'source_sha256':tick.digest(source),'dependencies_sha256':dependencies,'returncode':process.returncode,'stdout':process.stdout,'stderr':process.stderr})
    results=[json.loads(line.split('=',1)[1]) for line in process.stdout.splitlines() if line.startswith('HIER_NATIVE_RESULT=')]
    if results:
        assert len(results)==1
        tick.save(BUNDLE/(args.name+'_result.json'),{'token':TOKEN,'attempt_sha256':tick.digest(attempt),**results[0]})
    if results:
        print(json.dumps({k:v for k,v in results[0].items() if k not in ('records','batches','original_captures')},ensure_ascii=False))
    else:
        print(process.stdout[-14000:])
    print(process.stderr[-6000:])
    print('returncode='+str(process.returncode))
    raise SystemExit(process.returncode)

if __name__=='__main__':main()
