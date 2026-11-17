"""Reuse immutable compatible CRE tools; exercise only current local busy refusal."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,json
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent;OLD=ROOT/'pipeline/diagnostic_bundles/tick_d08825b5';PK=OLD/'cre_compatible_tooling'
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 guard();assert sha(PK/'preparation.json')=='dd7f12b3b3aa884caf90b4c5b1b8c02fce3791621677d9e0eb1541d227ac601b'
 before={n:sha(ROOT/'pipeline'/n) for n in json.loads((HERE/'protected_assets_before.json').read_text())['protected_ledgers']}
 assert not (HERE/'cre_execution').exists()
 spec=importlib.util.spec_from_file_location('cre_972a_original_adapter',PK/'adapter.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 class NoTransport:
  def __init__(self):self.calls=[]
  def call(self,*a,**kw):self.calls.append([a,kw]);raise AssertionError('Busy guard must not reach transport')
 t=NoTransport();adapter=m.Adapter(transport=t);calls=[]
 for gpu in [0,1]:
  try:adapter.prepare(gpu)
  except m.Refused as e:calls.append({'physical_gpu':gpu,'result':'refused','reason':str(e)})
  else:raise AssertionError('Busy/unauthorized prepare unexpectedly succeeded')
 assert ('registered running task' in calls[0]['reason'] or 'reserved by active' in calls[0]['reason']) and 'Explicit physical GPU0' in calls[1]['reason']
 assert not t.calls and not (HERE/'cre_execution').exists() and all(sha(ROOT/'pipeline'/n)==h for n,h in before.items())
 record={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'candidate_id':m.CANDIDATE,'code_commit':m.COMMIT,'native_op_preparation':ref(PK/'preparation.json'),'adapter_release':ref(PK/'adapter_release.json'),'actual_calls':calls,'transport_calls':0,'active_binding_manifest_lease_created':False,'native_or_resources_executed':False,'hardware_evidence':ref(HERE/'aef_training_progress_observation.json'),'scope':'Actual current root immutable compatible CRE local refusal before transport. Original AEF registered0 remains reserved. Separate physical readback has its own timestamp; no future idle/lease/native PASS.'}
 guard()
 with (HERE/'cre_actual_current_guard.json').open('x',encoding='utf8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'calls':calls,'transport_calls':0,'active':False,'sha256':sha(HERE/'cre_actual_current_guard.json')},ensure_ascii=False))
if __name__=='__main__':main()
