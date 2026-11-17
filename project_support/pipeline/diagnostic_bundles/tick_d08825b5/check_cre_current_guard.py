"""Exercise actual compatible CRE local refusal before any transport or active binding."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,json,os,sys
from anchor import guard,ROOT,EXPECTED,sha
HERE=Path(__file__).resolve().parent;PK=HERE/'cre_compatible_tooling'
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 guard();before={n:sha(ROOT/'pipeline'/n) for n in json.loads((HERE/'protected_assets_before.json').read_text())['protected_ledgers']}
 assert not (HERE/'cre_execution').exists()
 spec=importlib.util.spec_from_file_location('cre_d088_reviewed_adapter',PK/'adapter.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 class NoTransport:
  def __init__(self):self.calls=[]
  def call(self,*a,**k):self.calls.append([a,k]);raise AssertionError('No network or remote action allowed in busy guard check')
 transport=NoTransport();adapter=module.Adapter(transport=transport);results=[]
 for gpu in [0,1]:
  try:adapter.prepare(gpu)
  except module.Refused as e:results.append({'physical_gpu':gpu,'result':'refused','reason':str(e)})
  else:raise AssertionError('Busy or unauthorized preparation unexpectedly succeeded')
 assert 'registered running task' in results[0]['reason'] or 'reserved by active' in results[0]['reason']
 assert 'Explicit physical GPU0' in results[1]['reason'] and not transport.calls and not (HERE/'cre_execution').exists()
 assert all(sha(ROOT/'pipeline'/n)==h for n,h in before.items())
 record={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'candidate_id':'hierarchy-cross-root-directed-edge-broadcast','code_commit':module.COMMIT,'actual_adapter':ref(PK/'adapter.py'),'actual_source_version':ref(HERE/'cre_version_prepare/isolated_source_version.json'),'native_op_preparation':ref(PK/'preparation.json'),'static_release':ref(PK/'adapter_release.json'),'actual_calls':results,'transport_calls':0,'active_binding_manifest_lease_created':False,'native_or_resources_executed':False,'registered_GPU0_task':'M216-AEF','physical_observation':ref(HERE/'aef_training_progress_observation_v2.json'),'scope':'Current owner/source/external-anchor/current-grant refusal before transport. Physical proof is separately dated AEF readback; this local refusal is not a new idle probe or native test.'}
 guard()
 with (HERE/'cre_actual_current_guard.json').open('x',encoding='utf8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'current_guard':results,'transport_calls':0,'active':False,'sha256':sha(HERE/'cre_actual_current_guard.json')},ensure_ascii=False))
if __name__=='__main__':main()
