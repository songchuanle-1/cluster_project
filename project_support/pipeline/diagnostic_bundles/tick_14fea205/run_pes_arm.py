"""Invoke one original PES CLI arm once, retaining output without dumping tensors."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, json, subprocess, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE=Path(__file__).resolve().parent;EXE=HERE/'pes_execution'
ADAPTER=ROOT/'pipeline/diagnostic_bundles/tick_9db8f3be/pes_operational_prepare/adapter.py'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');ap.add_argument('--mode',choices=['smoke','resources'],required=True);ap.add_argument('--target',choices=['champion','candidate'],required=True);a=ap.parse_args()
    if not a.execute_root:print('DEFAULT_NO_ARM_EXECUTION');return
    guard();stem=a.mode+'_'+a.target
    assert not any((EXE/(stem+n)).exists() for n in ('_request.json','_execution.json')),'Existing request must reconcile, never replay'
    command=[sys.executable,'-B','-X','utf8',str(ADAPTER),'run','--mode',a.mode,'--target',a.target]
    u.save(HERE/('cli_'+stem+'_intent.json'),{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'command':command,'scope':'One original guarded CLI arm only; canonical request/result are authoritative, never replay.'})
    r=subprocess.run(command,cwd=str(ROOT),capture_output=True,timeout=950)
    guard()
    for name,data in [('stdout',r.stdout),('stderr',r.stderr)]:
        with (HERE/('cli_'+stem+'.'+name)).open('xb') as f:f.write(data)
    result={'owner':EXPECTED,'returncode':r.returncode,'mode':a.mode,'target':a.target,'stdout':u.ref(HERE/('cli_'+stem+'.stdout')),'stderr':u.ref(HERE/('cli_'+stem+'.stderr'))}
    if (EXE/(stem+'_execution.json')).exists():
        env=u.read(EXE/(stem+'_execution.json'));raw=env.get('result',{})
        result.update(execution=u.ref(EXE/(stem+'_execution.json')),certainty=env.get('certainty'),native_returncode=env.get('returncode'),execution_completed=raw.get('execution_completed'),optimizer_steps=raw.get('optimizer_steps'),losses=raw.get('losses'),native_smoke_checks_passed=raw.get('native_smoke_checks_passed'))
        if a.mode=='resources':result.update(profile=raw.get('profile'),median_ms=raw.get('median_ms'),p90_ms=raw.get('p90_ms'),peak_allocated_bytes=raw.get('peak_allocated_bytes'))
    u.save(HERE/('cli_'+stem+'_result.json'),result)
    shown={k:v for k,v in result.items() if k!='owner'}
    if isinstance(shown.get('profile'),dict):shown['profile']={k:v for k,v in shown['profile'].items() if k in ('flops','within10G','parameters','parameter_count','params')}
    if r.returncode:shown['stderr_tail']=r.stderr.decode('utf8',errors='replace')[-1800:]
    print(json.dumps(shown,ensure_ascii=False));raise SystemExit(r.returncode)

if __name__=='__main__':main()
