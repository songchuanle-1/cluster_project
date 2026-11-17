"""Owning-root single-request executor of the frozen reviewed BFC adapter."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
PACKET=ROOT/'pipeline/diagnostic_bundles/tick_64ac844e/bfc_operational_prepare'
def main():
 p=argparse.ArgumentParser();p.add_argument('operation',choices=['probe','prepare','stage','run','status','reconcile']);p.add_argument('--mode',choices=['smoke','resources']);p.add_argument('--target',choices=['champion','candidate']);p.add_argument('--request-id');a=p.parse_args()
 owner=guard();spec=importlib.util.spec_from_file_location('reviewed_bfc_actual',PACKET/'adapter.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 adapter=m.Adapter(execution_dir=HERE/'bfc_execution');name=a.operation+('_'+a.mode+'_'+a.target if a.operation=='run' else '')
 if a.operation=='reconcile':name+='_'+str(a.request_id)
 output=HERE/('bfc_'+name+'_console.json');assert not output.exists(),'Original result exists: reconcile, never replay'
 try:
  if a.operation in ['probe','prepare']:result=getattr(adapter,a.operation)(0)
  elif a.operation=='run':result=adapter.run(a.mode,a.target)
  elif a.operation=='reconcile':result=adapter.reconcile(a.request_id)
  else:result=getattr(adapter,a.operation)()
  with output.open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
  guard();raw=result.get('result',{}) if isinstance(result,dict) else {}
  print(json.dumps({'operation':name,'console':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'certainty':result.get('certainty'),'returncode':result.get('returncode'),'verified':result.get('verified'),'idle':result.get('idle'),'execution_completed':raw.get('execution_completed'),'losses':raw.get('losses'),'status':raw.get('status'),'GPU':0,'original_owner_token':owner['token']},ensure_ascii=False))
 except Exception as error:
  failure=HERE/('bfc_'+name+'_failure.json')
  with failure.open('x',encoding='utf8') as f:json.dump({'recorded_at':datetime.now(timezone.utc).isoformat(),'operation':name,'type':type(error).__name__,'error':str(error),'retry_or_replay':False,'next_action':'Read-only reconcile exact original request and preserve all output before any further action'},f,ensure_ascii=False,indent=2);f.write('\n')
  raise
if __name__=='__main__':main()
