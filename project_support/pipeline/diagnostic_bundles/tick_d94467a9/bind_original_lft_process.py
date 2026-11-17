"""Read-only pinned SSH identity to bind the one original canonical LFT process."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,subprocess,shlex
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
def main():
    if sys.argv[1:]!=['--execute-root']:print('DEFAULT_NOP');return
    guard()
    dispatch=HERE/'lft_dispatch_result.json'
    assert sha(dispatch)=='0b568512bb16ddaf6aefa20db459b25b6f781d5cabc1a3a774c80aafc91c73d6'
    d=u.read(dispatch);t=d['task_after'];calls=u.read(HERE/'lft_dispatch_transport_calls.json')
    assert d['verified_native_progress'] is True and d['canonical_dispatch_invoked_once'] is True
    assert sum(x['canonical_native_launch_request'] for x in calls)==1
    e=u.read(ROOT/'pipeline/experiments/M227-LFT.json')
    for k in ('pid','log','code_commit','config'):assert e[k]==t[k]
    assert t['pid']==2685912 and str(t['gpu'])=='1' and t['status']=='running' and t['launch_verified'] is True
    program='p='+repr({k:t[k] for k in ['pid','log','code_commit','config']})+'\n'+'''from pathlib import Path
import os,json,socket,subprocess
assert socket.gethostname()=='dl04-MS-7E06'
proc=Path('/proc')/str(p['pid']);assert proc.stat().st_uid==os.getuid()
root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
start=(proc/'stat').read_text().rsplit(') ',1)[1].split()[19]
argv=(proc/'cmdline').read_bytes().replace(b'\\0',b' ').decode()
assert 'tools/train.py' in argv and p['config'] in argv and str((proc/'cwd').resolve())==root and str((proc/'fd/1').resolve())==p['log']
env=(proc/'environ').read_bytes().split(b'\\0');assert b'PYTHONDONTWRITEBYTECODE=1' in env
assert subprocess.check_output(['git','--no-optional-locks','-C',root,'rev-parse','HEAD'],text=True).strip()==p['code_commit']
print(json.dumps({'pid':p['pid'],'start_ticks':start,'argv':argv,'cwd':root,'stdout':p['log'],'PYTHONDONTWRITEBYTECODE':'1'}))
'''
    argv=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','export PYTHONDONTWRITEBYTECODE=1 && /usr/bin/python3 -B -c '+shlex.quote(program)]
    guard();r=subprocess.run(argv,capture_output=True,text=True,encoding='utf8',timeout=35)
    u.save(HERE/'lft_original_identity_collection.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'command':argv,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'canonical_dispatch':u.ref(dispatch)})
    assert r.returncode==0,r.stderr
    value=json.loads(r.stdout);b=u.read(HERE/'dual_original_run_observer/lft_binding_template.json')
    b.update(owner=EXPECTED,pid=t['pid'],start_ticks=value['start_ticks'],log=t['log'],original_identity_collection=u.ref(HERE/'lft_original_identity_collection.json'),canonical_dispatch=u.ref(dispatch))
    u.save(HERE/'lft_original_process_binding.json',b)
    print(json.dumps(u.ref(HERE/'lft_original_process_binding.json')))
if __name__=='__main__':main()
