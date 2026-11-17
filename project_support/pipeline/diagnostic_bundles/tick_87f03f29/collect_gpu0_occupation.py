"""Canonical occupation collector with pinned, GPU0-only read transport."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,ast,copy,json,shlex,subprocess,sys
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent;CALLS=[];EXPECTED_RUNNING_PID=None

def pinned(host,user,command,timeout=75):
 guard();assert (host,user)==('192.168.1.115','songcl')
 args=shlex.split(command);assert len(args)==4 and args[1:3]==['-B','-c']
 program=args[3];tree=ast.parse(program)
 stmt=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='commands' for t in n.targets))
 commands=ast.literal_eval(stmt.value);assert set(commands)=={'hostname','gpu','compute'} and commands['hostname']==['hostname']
 assert commands['gpu']==['nvidia-smi','--query-gpu=index,uuid,utilization.gpu,memory.used,memory.total','--format=csv,noheader,nounits']
 assert commands['compute']==['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits']
 scoped=copy.deepcopy(commands)
 for key in ('gpu','compute'):scoped[key][1:1]=['-i','0']
 literal='commands='+repr(commands);assert program.count(literal)==1
 program="import socket\nassert socket.gethostname()=='dl04-MS-7E06'\n"+program.replace(literal,'commands='+repr(scoped),1)
 remote='export PYTHONDONTWRITEBYTECODE=1 && '+shlex.quote(args[0])+' -B -c '+shlex.quote(program)
 cli=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',user+'@'+host,remote]
 r=subprocess.run(cli,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=timeout)
 CALLS.append({'recorded_at':datetime.now(timezone.utc).isoformat(),'command':cli,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'read_only':True,'only_physical_gpu':0})
 assert r.returncode==0,r.stderr
 queries=json.loads(r.stdout);assert queries['hostname']['stdout'].strip()=='dl04-MS-7E06'
 row=[x.strip() for x in queries['gpu']['stdout'].strip().split(',')]
 assert row[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'] and all(q['rc']==0 for q in queries.values())
 assert all(q['command']==scoped[k] for k,q in queries.items())
 if EXPECTED_RUNNING_PID is not None:
  pids=[x.split(',')[-1].strip() for x in queries['compute']['stdout'].splitlines() if x.strip()]
  assert str(EXPECTED_RUNNING_PID) in pids,'Original AOC compute PID no longer present: reconcile before using a queue-only reservation as physical busy evidence'
 return r.stdout.strip()

def main():
 global EXPECTED_RUNNING_PID
 ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');ap.add_argument('--candidate-id');ap.add_argument('--label',required=True);ap.add_argument('--expect-running-pid',type=int);a=ap.parse_args()
 if not a.execute_root:print('DEFAULT_READ_ONLY_NO_QUERY_OR_RECORD');return
 guard();assert not (HERE/('gpu0_occupation_'+a.label+'_intent.json')).exists()
 EXPECTED_RUNNING_PID=a.expect_running_pid
 assert EXPECTED_RUNNING_PID is None or EXPECTED_RUNNING_PID==3437349
 w=u.read(ROOT/'pipeline/research_work.json');targets=[c for c in w['candidates'] if c.get('stage')=='blocked' and c.get('blocker_kind')=='exclusive_gpu_slot' and c.get('required_server')=='server-4']
 assert len(targets)==1 and targets[0]['id']==a.candidate_id
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon;import gpu_occupation
 original=mon.ssh
 u.save(HERE/('gpu0_occupation_'+a.label+'_intent.json'),{'owner':EXPECTED,'candidate_id':a.candidate_id,'canonical_collector_source_sha256':sha(Path(gpu_occupation.__file__)),'scope':'Unmodified canonical collect/validation/persistence with only transport pinned to hostname/keys and its two nvidia-smi queries narrowed to physical0. No compute, signals or scheduler change.'})
 try:
  mon.ssh=pinned;result=gpu_occupation.collect(ROOT,EXPECTED['token'],'server-4',a.label)
 except Exception as error:
  u.save(HERE/('gpu0_occupation_'+a.label+'_error.json'),{'owner':EXPECTED,'calls':CALLS,'error_type':type(error).__name__,'error':str(error),'scope':'Read-only resource observation failure; no idle/busy assertion, native replay or launch authorized.'})
  raise
 finally:mon.ssh=original
 guard();assert result['candidate_ids']==[a.candidate_id] and len(CALLS)==1
 u.save(HERE/('gpu0_occupation_'+a.label+'_transport.json'),{'owner':EXPECTED,'calls':CALLS,'scope':'GPU0-only actual transport for canonical collector; queries/raw hash proof in canonical output.'})
 u.save(HERE/('gpu0_occupation_'+a.label+'_result.json'),{'owner':EXPECTED,'result':result,'canonical_proof':result['evidence']})
 print(json.dumps({'evidence':result['evidence'],'busy_gpu_ids':result['state']['busy_gpu_ids'],'idle_gpu_ids':result['state']['idle_gpu_ids']}))
if __name__=='__main__':main()
