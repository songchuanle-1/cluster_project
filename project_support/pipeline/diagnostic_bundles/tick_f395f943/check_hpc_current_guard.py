"""Actual HPC current local registered-busy/unauthorized refusal, with zero transport."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,json
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent;OP=HERE/'hpc_operational_prepare'
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 guard();assert sha(OP/'preparation.json')=='136255da0ba630c73469e7c20234d086776bf219f3e061aa997929ad65f41143'
 before={n:sha(ROOT/'pipeline'/n) for n in json.loads((HERE/'protected_assets_before.json').read_text())['protected_ledgers']}
 assert not (HERE/'hpc_execution').exists()
 spec=importlib.util.spec_from_file_location('hpc_f395_reviewed_adapter',OP/'adapter.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 class NoTransport:
  def __init__(self):self.calls=[]
  def call(self,*a,**kw):self.calls.append([a,kw]);raise AssertionError('No transport allowed while original AEF owns registered slot')
 t=NoTransport();adapter=m.Adapter(transport=t);calls=[]
 for gpu in [0,1]:
  try:adapter.prepare(gpu)
  except m.Refused as e:calls.append({'physical_gpu':gpu,'result':'refused','reason':str(e)})
  else:raise AssertionError('Busy/unauthorized prepare unexpectedly succeeded')
 assert ('registered running task' in calls[0]['reason'] or 'reserved by active' in calls[0]['reason']) and 'Explicit physical GPU0' in calls[1]['reason']
 assert not t.calls and not (HERE/'hpc_execution').exists() and all(sha(ROOT/'pipeline'/n)==h for n,h in before.items())
 record={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'candidate_id':m.CANDIDATE,'code_commit':m.COMMIT,'native_op_preparation':ref(OP/'preparation.json'),'adapter_release':ref(OP/'adapter_release.json'),'actual_calls':calls,'transport_calls':0,'active_binding_manifest_lease_created':False,'native_or_resources_executed':False,'registered_GPU0_task':'M216-AEF','separately_dated_physical_observation':ref(HERE/'aef_training_progress_observation.json'),'scope':'Actual reviewed HPC preparation guards reached current candidate/version/external anchors/current owner/grant and refused locally before transport. Not a native smoke, resource measurement or future GPU idle grant.'}
 guard()
 with (HERE/'hpc_actual_current_guard.json').open('x',encoding='utf8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'calls':calls,'transport_calls':0,'active':False,'sha256':sha(HERE/'hpc_actual_current_guard.json')},ensure_ascii=False))
if __name__=='__main__':main()
