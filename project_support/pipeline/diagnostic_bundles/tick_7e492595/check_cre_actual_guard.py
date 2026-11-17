"""Actual current CRE busy0/unauthorized1 refusal with impossible transport."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 assert sys.argv[1:]==['--execute-root'];owner=guard();assert not (HERE/'cre_execution').exists()
 spec=importlib.util.spec_from_file_location('current_cre_adapter',HERE/'cre_operational_prepare/adapter.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 class NoTransport:
  calls=0
  def call(self,*args,**kwargs):self.calls+=1;raise AssertionError('Actual local guard forbids transport')
 t=NoTransport();adapter=module.Adapter(transport=t);adapter.guard(0,0,mutation=True)
 def audit(event,args):
  if event in ('subprocess.Popen','os.system','socket.connect','socket.__new__'):raise AssertionError('No process/network: '+event)
  if event=='import' and args[0].split('.')[0]=='torch':raise AssertionError('No Torch')
 sys.addaudithook(audit);events=[]
 for gpu,expected in [(0,'Selected GPU has registered running task'),(1,'Explicit physical GPU0 is required')]:
  try:adapter.prepare(gpu)
  except module.Refused as e:assert str(e)==expected;events.append({'physical_gpu':gpu,'refused':True,'reason':str(e)})
  else:raise AssertionError('Current refusal missing')
 assert t.calls==0 and not (HERE/'cre_execution').exists() and 'torch' not in sys.modules
 obs=HERE/'bec_training_progress_observation.json';assert sha(obs)=='d40c8f3e1c23082103b2a54b61b4459f844082fc98e552cf08e89148ff91d760'
 assert json.loads(obs.read_text('utf8'))['owner_token']==owner['token'];guard()
 result={'kind':'resource_check','result':'blocked','candidate_id':module.CANDIDATE,'experiment_id':'M217-CRE','recorded_at':datetime.now(timezone.utc).isoformat(),'owner':{k:owner[k] for k in ('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')},'actual_local_guard_events':events,'hardware_evidence':ref(obs),'hardware_scope':'Separate current root original BEC source/process/context/progress samples; this check makes no new hardware query or physical-idle proof.','static_catalogue_result':ref(HERE/'cre_catalogue_result.json'),'transport_calls':0,'Popen_calls':0,'network_calls':0,'GPU_queries':0,'GPU1_queries':0,'Torch_imported':False,'active_execution_created':False,'native_TRAIN2':'NOT_RUN','resources':'NOT_RUN','native_PASS_or_receipt_queue_created':False,'material_concerns':[]}
 p=HERE/'cre_actual_local_guard.json'
 with p.open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps({'result':'blocked','evidence':ref(p),'transport_calls':0,'active_execution_created':False}))
if __name__=='__main__':main()
