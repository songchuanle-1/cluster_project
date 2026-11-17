"""Exercise current real local BFC guards with process/network/transport forbidden."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,os,sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent;PACKET=ROOT/'pipeline/diagnostic_bundles/tick_64ac844e/bfc_operational_prepare'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 owner=guard();paths=[ROOT/'pipeline/queue.json',ROOT/'pipeline/running.json',ROOT/'pipeline/research_work.json',ROOT/'SERVERS.yaml',ROOT/'pipeline/goal.json'];before={str(p):sha(p) for p in paths}
 execution=HERE/'bfc_execution';assert not execution.exists();transport=[];events=[]
 class NoTransport:
  def call(self,*args,**kwargs):transport.append(str(args[:1]));raise AssertionError('No actual transport allowed for busy local guard integration')
 def audit(event,args):
  if event=='subprocess.Popen' or event.startswith('socket.'):events.append(event);raise AssertionError('No process/network allowed: '+event)
 sys.addaudithook(audit)
 spec=importlib.util.spec_from_file_location('bfc_real_local_guard',PACKET/'adapter.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 a=m.Adapter(transport=NoTransport(),execution_dir=execution);refusals={}
 for gpu in [0,1]:
  actual=a.guard(gpu=gpu,mutation=True);assert actual['owner']==owner
  try:a.prepare(gpu)
  except m.Refused as e:refusals['registered_gpu'+str(gpu)+'_busy']=str(e)
  else:raise AssertionError('Busy registered card was not refused before probe/materialization')
  assert refusals['registered_gpu'+str(gpu)+'_busy']=='Selected GPU has registered running task'
 for value in [None,True,False,'0','1',2,-1]:
  for op in ['prepare','probe']:
   try:getattr(a,op)(value)
   except m.Refused as e:refusals['invalid_'+op+'_'+repr(value)]=str(e)
   else:raise AssertionError('Invalid explicit physical GPU reached operation: '+repr(value))
 try:a.guard(required_seconds=999999,gpu=0,mutation=True)
 except m.Refused as e:refusals['original_deadline_unchanged']=str(e)
 else:raise AssertionError('Insufficient unchanged deadline accepted')
 assert refusals['original_deadline_unchanged']=='Insufficient unchanged owner deadline'
 after={str(p):sha(p) for p in paths};assert before==after and not execution.exists() and not transport and not events and 'torch' not in sys.modules;guard()
 out={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'REAL_CURRENT_LOCAL_GUARDS_AND_BUSY_ZERO_TRANSPORT_REFUSALS_VALIDATED','candidate_id':m.CANDIDATE,'code_commit':m.COMMIT,'current_owner_token':owner['token'],'original_deadline_at':owner['deadline_at'],'refusals':refusals,'actual_transport_calls':0,'subprocess_or_network_audit_events':events,'torch_imported':False,'active_binding_manifest_lease_or_execution_directory_created':False,'goal_servers_queue_running_research_work_unchanged':True,'protected_hashes':after,'native_execution':'NOT_RUN','resources':'NOT_RUN','scope':'Actual current owner/context/externally anchored packet passed local guards. Both actual registered GPU0/BTC andGPU1/BCR refuse before any probe/directory/manifest/lease. This is not live GPU idle/assets verification or native PASS, and it never authorizes future compute.'}
 p=HERE/'bfc_actual_local_guard_integration.json'
 with p.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'status':out['status'],'transport_calls':0,'active_binding_created':False,'busy_cards':[0,1],'invalid_entry_cases':14,'native':'NOT_RUN'}))
if __name__=='__main__':main()
