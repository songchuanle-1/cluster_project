"""Read-only exact canonical DCE PID start, no launch or GPU computation."""
from pathlib import Path
import argparse,json,shlex,subprocess
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent

def main():
 a=argparse.ArgumentParser();a.add_argument('--execute-root',action='store_true');a.add_argument('--dispatch-sha256');args=a.parse_args()
 if not args.execute_root:print('DEFAULT_READ_ONLY_NO_TRANSPORT');return
 guard();assert sha(HERE/'dce_dispatch_result.json')==args.dispatch_sha256
 ds=u.read(HERE/'dce_dispatch_result.json');assert ds['token']==EXPECTED['token'] and ds['verified_native_progress'] and ds['canonical_dispatch_invoked_once']
 e=u.read(ROOT/'pipeline/experiments/M220-DCE.json');assert e['pid']==ds['task_after']['pid'] and e['status']=='running' and e['code_commit']=='5c0c211c8ecc9479ecb34dbb8118a95f4b20e391' and e['launch_verified']
 assert not (HERE/'dce_original_process_start.json').exists()
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
 command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','export PYTHONDONTWRITEBYTECODE=1 && /usr/bin/python3 -B -c '+shlex.quote(s)]
 r=subprocess.run(command,capture_output=True,text=True,encoding='utf8',timeout=30)
 record={'owner':EXPECTED,'returncode':r.returncode,'stderr':r.stderr,'observation':json.loads(r.stdout) if r.returncode==0 else None}
 u.save(HERE/'dce_original_process_start.json',record);assert r.returncode==0,r.stderr
 print(json.dumps(record['observation']))
if __name__=='__main__':main()
