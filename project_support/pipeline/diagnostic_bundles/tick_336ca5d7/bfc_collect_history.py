"""Save actual read-only status and exact original-request reconciliations."""
from pathlib import Path
import importlib.util,json
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
PACKET=ROOT/'pipeline/diagnostic_bundles/tick_64ac844e/bfc_operational_prepare'
def save(path,value):
 with path.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def main():
 guard();spec=importlib.util.spec_from_file_location('bfc_actual_history_adapter',PACKET/'adapter.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 a=m.Adapter(execution_dir=HERE/'bfc_execution')
 status_path=HERE/'status_after_four_console.json';assert not status_path.exists()
 status=a.status();save(status_path,status)
 for mode,target in m.PAIRS:
  arm=mode+'_'+target;request=json.loads((HERE/'bfc_execution'/(arm+'_request.json')).read_text('utf8'))
  result=a.reconcile(request['request_id']);save(HERE/('reconcile_'+arm+'_console.json'),result)
  assert result['workers']==[] and not result['compute_contexts'].strip()
 guard();print(json.dumps({'actual_status_and_filtered_reconcile_saved':True,'original_requests':4,'new_native_runs':0,'signals':False,'GPU':0}))
if __name__=='__main__':main()
