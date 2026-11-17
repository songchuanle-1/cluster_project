"""Default NOP. Clear only M235 production hold after current actual render approval."""
import argparse
from datetime import datetime,timezone
import sys
from packet_runtime import *
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute-root',action='store_true');p.add_argument('--production-result');p.add_argument('--production-review');p.add_argument('--production-review-sha256');arguments(p);a=p.parse_args()
 if not a.execute_root:print('{"status":"DEFAULT_NOP_NO_QUEUE_CHANGE"}');return
 require_arguments(a);guard(a);production=actual_production(a.production_result,a.production_review,a.production_review_sha256)
 sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard(a);queue=monitor.load_queue(str(ROOT));tasks=[x for xs in queue['gpu_queues'].values() for x in xs if x.get('id')=='M235-SINC'];assert len(tasks)==1
  task=tasks[0];assert task['status']=='waiting' and task['code_commit']==SOURCE and task['config']==CONFIG and not task.get('pid')
  assert task.get('dispatch_hold'),'Existing cleared/uncertain hold: reconcile, never replay'
  execution=TICK/'m235_pointer_execution';execution.mkdir(exist_ok=True);intent=execution/'clear_hold.intent.json';actual=execution/'clear_hold.actual.json';assert not intent.exists() and not actual.exists()
  old=task['dispatch_hold'];save(intent,{'owner':OWNER,'old_hold':old,'production_result_sha256':sha(a.production_result),'no_replay':True})
  task.pop('dispatch_hold',None);task.update(production_ready=True,production_result={'path':str(a.production_result),'sha256':sha(a.production_result)},production_owner=OWNER['token']);monitor.save_queue(str(ROOT),queue)
  assert sha(ROOT/'SERVERS.yaml')==read(HERE/'baseline.json')['SERVERS_sha256'];save(actual,{'owner':OWNER,'only_M235_hold_cleared':True,'production_ready':True,'old_hold':old,'production_shim':production['shim']});print(json.dumps({'path':str(actual),'sha256':sha(actual)}))
 finally:lock.close()
if __name__=='__main__':main()
