"""Root-owned single actual R1 arm; canonical requests prevent replay."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
OWNER={'token':'94f8ddb8a6e049c48c8e6237f4c737e8','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':'2026-10-26T14:57:12.614254+00:00','deadline_at':'2026-10-26T15:57:12.614254+00:00','context_sha256':'0104947a1b56f553572b7cddc0fa2f5ab0edbee9ba33f161af61e6990c234793','pending_sha256':'95a698a880ff7b5655a002531c1e3b5704e0f9c34ed4e1093f2c6ad72dba2331'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def guard():
 o=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'));assert {k:o.get(k) for k in OWNER}==OWNER
 assert os.environ.get('CODEX_THREAD_ID')==OWNER['thread_id']==json.loads((ROOT/'pipeline/execution_mode.json').read_text('utf8'))['target_thread_id']
 assert datetime.now(timezone.utc)<datetime.fromisoformat(OWNER['deadline_at'])
 assert sha(ROOT/'pipeline/headless/.tick_context.json')==OWNER['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==OWNER['pending_sha256']
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['smoke','resources']);p.add_argument('target',choices=['champion','candidate']);a=p.parse_args();guard()
 name=a.mode+'_'+a.target;ex=HERE/'bec_r1_execution';marker=HERE/(name+'_cli_capture.json')
 assert not marker.exists() and not (ex/(name+'_request.json')).exists() and not (ex/(name+'_execution.json')).exists(),'Existing arm: reconcile original request, never replay'
 cmd=[sys.executable,'-B','-X','utf8',str(ROOT/'pipeline/diagnostic_bundles/tick_faccbed6/bec_r1_operational_prepare/adapter.py'),'run','--mode',a.mode,'--target',a.target,'--execution-dir',str(ex)]
 r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=940)
 with marker.open('x',encoding='utf8') as f:json.dump({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},f,ensure_ascii=False,indent=2)
 path=ex/(name+'_execution.json');v=json.loads(path.read_text('utf8')) if path.exists() else {};raw=v.get('result',{})
 print(json.dumps({'arm':name,'cli_returncode':r.returncode,'execution_path':str(path) if path.exists() else None,'execution_sha256':sha(path) if path.exists() else None,'certainty':v.get('certainty'),'returncode':v.get('returncode'),'execution_completed':raw.get('execution_completed'),'losses':raw.get('losses'),'native_smoke_checks_passed':raw.get('native_smoke_checks_passed'),'resources_keys':list(raw.get('resources',{})) if isinstance(raw.get('resources'),dict) else None,'error':r.stderr[-1800:] if r.returncode else None},ensure_ascii=False))
 if r.returncode:raise SystemExit(r.returncode)
 assert v.get('certainty')=='terminal' and v.get('returncode')==0 and raw.get('execution_completed') is True
if __name__=='__main__':main()
