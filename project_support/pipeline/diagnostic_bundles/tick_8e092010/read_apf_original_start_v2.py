"""Read-only bind exact already-launched canonical APF PID start identity."""
from pathlib import Path
import json,shlex,subprocess
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
guard();assert sha(HERE/'apf_dispatch_result.json')=='ec469a7af9fe6dd422b57b0cf708a0bd5fc344dd1548add51dd54f223769176a'
e=u.read(ROOT/'pipeline/experiments/M219-APF.json');assert e['pid']==793277 and e['status']=='running' and e['code_commit']=='d0e2f95712ed16446907706fbf6a65d34996a9ad' and e['launch_verified']
assert not (HERE/'apf_original_process_start.json').exists()
p={'pid':e['pid'],'config':e['config'],'log':e['log'],'root':'/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'}
s=r'''import socket,json,os
from pathlib import Path
assert socket.gethostname()=='dl04-MS-7E06'
p=json.loads(PAYLOAD);q=Path('/proc')/str(p['pid']);assert q.exists() and q.stat().st_uid==os.getuid()
cmd=(q/'cmdline').read_bytes().replace(b'\0',b' ').decode()
assert 'tools/train.py' in cmd and p['config'] in cmd and str((q/'cwd').resolve())==p['root'] and str((q/'fd/1').resolve())==p['log']
start=(q/'stat').read_text().rsplit(') ',1)[1].split()[19]
print(json.dumps({'pid':p['pid'],'start_ticks':start,'log':p['log'],'hostname':socket.gethostname(),'signals_sent':False}))
'''.replace('PAYLOAD',repr(json.dumps(p)))
args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','export PYTHONDONTWRITEBYTECODE=1 && /usr/bin/python3 -B -c '+shlex.quote(s)]
run=subprocess.run(args,capture_output=True,text=True,encoding='utf8',timeout=30)
r={'owner':EXPECTED,'returncode':run.returncode,'stderr':run.stderr,'observation':json.loads(run.stdout) if run.returncode==0 else None}
u.save(HERE/'apf_original_process_start.json',r);assert run.returncode==0,run.stderr
print(json.dumps(r['observation']))
