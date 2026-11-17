"""One explicit reviewed DCE adapter operation. Never repeats an existing request."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,importlib.util,json,os
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent;OP=HERE/'dce_operational_prepare';NATIVE=HERE/'dce_native_prepare'

def save(path,value):
 guard()
 with path.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())

def main():
 p=argparse.ArgumentParser();p.add_argument('operation',choices=['prepare','stage','run']);p.add_argument('--mode',choices=['smoke','resources']);p.add_argument('--target',choices=['champion','candidate']);a=p.parse_args();guard()
 reg=u.read(HERE/'dce_registration_result.json');assert reg['owner']==EXPECTED and reg['status']=='ONE_NEW_DCE_STATIC_CAPABILITY_REGISTERED_NATIVE_NOT_RUN' and reg['code_commit']=='5c0c211c8ecc9479ecb34dbb8118a95f4b20e391'
 for key,path in [('native_preparation',NATIVE/'preparation.json'),('operational_preparation',OP/'preparation.json'),('release',OP/'adapter_release.json')]:assert u.ref(path)==reg[key]
 c=next(c for c in u.read(ROOT/'pipeline/research_work.json')['candidates'] if c['id']=='hierarchy-directed-cavity-edge-composition')
 assert c['code_commit']==reg['code_commit'] and c['worker_preparation']['preparation']==reg['native_preparation'] and c['execution_adapter']['preparation']==reg['operational_preparation'] and c['execution_adapter']['release']==reg['release']
 if a.operation=='run':assert a.mode and a.target;label=a.mode+'_'+a.target
 else:assert a.mode is None and a.target is None;label=a.operation
 intent=HERE/('dce_'+label+'_controller_intent.json');output=HERE/('dce_'+label+'_controller_result.json')
 assert not intent.exists() and not output.exists(),'Existing/partial operation requires exact read-only reconciliation; no replay'
 spec=importlib.util.spec_from_file_location('reviewed_current_dce_adapter',OP/'adapter.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);adapter=m.Adapter();adapter.guard()
 save(intent,{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'operation':a.operation,'mode':a.mode,'target':a.target,'registration':u.ref(HERE/'dce_registration_result.json'),'scope':'One explicit reviewed method. Any uncertainty preserves original request; no retry.'})
 try:
  if a.operation=='prepare':result=adapter.prepare(0)
  elif a.operation=='stage':result=adapter.stage()
  else:result=adapter.run(a.mode,a.target)
 except Exception as error:
  save(output,{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'operation':a.operation,'mode':a.mode,'target':a.target,'error_type':type(error).__name__,'error':str(error),'result':'ERROR_RECONCILE_ORIGINAL_REQUEST_NO_RETRY'});raise
 save(output,{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'operation':a.operation,'mode':a.mode,'target':a.target,'result':result})
 print(json.dumps({'operation':a.operation,'mode':a.mode,'target':a.target,'controller_result':u.ref(output)}))
if __name__=='__main__':main()
