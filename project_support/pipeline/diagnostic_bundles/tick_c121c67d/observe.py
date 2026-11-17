"""Fresh authorized resource evidence and precise terminal registry extract."""
import json
from ops import ROOT,OUT,guard,tick,save,evidence,remote
guard(120)
code=r'''
import json,subprocess,fcntl
from datetime import datetime,timezone
cards={}
for index,uuid in ((0,'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),(1,'GPU-7f82edb9-f620-8045-caea-a75232265cd1')):
 row=subprocess.check_output(['nvidia-smi','-i',str(index),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
 assert [s.strip() for s in row.split(',')][:2]==[str(index),uuid]
 contexts=subprocess.check_output(['nvidia-smi','-i',str(index),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
 locks={}
 for kind in ('training','diagnostic','exclusive'):
  with open('/tmp/cluster_project_gpu'+str(index)+'_'+kind+'.lock','a+b') as handle:
   try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True
   except BlockingIOError:locks[kind]=False
 cards[str(index)]={'gpu':row,'contexts':contexts,'locks_available':locks}
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'cards':cards,'new_training':0}))
'''
server4=remote(code)
queue=tick.load(ROOT/'pipeline/queue.json')
active=[dict(server=server,**row) for server,rows in queue['gpu_queues'].items() for row in rows if row.get('id')=='M204-CPA']
terminal=tick.load(ROOT/'pipeline/experiments/M204-CPA.json')
assert not active and terminal['status']=='done_earlystop'
terminal_summary={key:terminal.get(key) for key in ('id','candidate_id','status','final_best','epochs_final','finished_at','archive_id','automatic_restart')}
path=save('current_resources_and_terminal.json',{'server4':server4,'M204_registry':terminal_summary,
    'registry_evidence':evidence(ROOT/'pipeline/experiments/M204-CPA.json'),
    'local_observer_failure':'First observer assumedM204stillinactivequeue;assertlenfailedafterread-onlyresourceprobe. Correctedtoofficialexperimentarchive;no scientific/GPUtest or remote fault inferred.',
    'server3':'This tick canonical preflight reports unreachable;GPU1 occupation UNKNOWN,not separatelyrepolled or assumed idle/occupied.',
    'scope':'Live authorized resources and canonical terminal metadata only;no restart/migration/foreignjob/scheduler changes.'})
print(json.dumps({'evidence':evidence(path),'server4':server4,'M204_registry':terminal_summary},ensure_ascii=False,indent=2))
