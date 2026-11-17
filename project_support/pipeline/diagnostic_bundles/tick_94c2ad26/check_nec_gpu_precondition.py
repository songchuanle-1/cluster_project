"""Read-only physical occupation check; never activates diagnostics or touches original jobs."""
from pathlib import Path
from datetime import datetime,timezone
import sys,subprocess,json,shlex
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
def main():
 if sys.argv[1:]!=['--execute-root']:print('DEFAULT_NOP');return
 guard();b=u.read(HERE/'protected_assets_before.json');u.protect(b)
 program='''import json,socket,subprocess,os
from pathlib import Path
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06'
queries={}
for name,argv in {'gpu':['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],'compute':['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits']}.items():
 r=subprocess.run(argv,capture_output=True,text=True,timeout=15);assert r.returncode==0
 queries[name]={'command':argv,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
originals=[]
for pid,start in [(2085005,'105948793'),(2685912,'106767833')]:
 p=Path('/proc')/str(pid);assert p.stat().st_uid==os.getuid()
 actual=(p/'stat').read_text().rsplit(') ',1)[1].split()[19];assert actual==start
 assert 'tools/train.py' in (p/'cmdline').read_bytes().replace(b'\\0',b' ').decode()
 originals.append({'pid':pid,'start_ticks':actual})
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'queries':queries,'originals':originals,'signals_or_training_entry':False}))
'''
 argv=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','export PYTHONDONTWRITEBYTECODE=1 && /usr/bin/python3 -B -c '+shlex.quote(program)]
 guard();run=subprocess.run(argv,capture_output=True,text=True,encoding='utf8',timeout=50)
 result={'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'command':argv,'returncode':run.returncode,'stderr':run.stderr,'raw_stdout':run.stdout,'candidate_id':'hierarchy-coupled-node-edge-state-composition','scope':'Current actual occupation of authorized physical0/1 only, no new CUDA computation or training; other jobs preserved.'}
 if run.returncode==0:
  data=json.loads(run.stdout);rows={int(x.split(',')[0]):[v.strip() for v in x.split(',')] for x in data['queries']['gpu']['stdout'].splitlines()}
  expected={0:('GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',2085005),1:('GPU-7f82edb9-f620-8045-caea-a75232265cd1',2685912)}
  contexts={(x.split(',')[0].strip(),int(x.split(',')[1])) for x in data['queries']['compute']['stdout'].splitlines() if ',' in x}
  assert set(rows)=={0,1}
  for gpu,(uuid,pid) in expected.items():assert rows[gpu][1]==uuid and (uuid,pid) in contexts
  idle=[g for g,row in rows.items() if int(row[2])<1024 and int(row[3])<10 and not any(uuid==row[1] for uuid,pid in contexts)]
  result.update(observation=data,idle_gpu_ids=idle,busy_gpu_ids=[g for g in rows if g not in idle],result='blocked' if not idle else 'passed',native_executed=False,resource_profile_executed=False)
 u.protect(b);u.save(HERE/'nec_gpu_precondition_observation.json',result)
 assert run.returncode==0,run.stderr
 print(json.dumps({'evidence':u.ref(HERE/'nec_gpu_precondition_observation.json'),'observed_at':data['observed_at'],'idle_gpu_ids':idle,'busy_gpu_ids':result['busy_gpu_ids'],'native_executed':False}))
if __name__=='__main__':main()
