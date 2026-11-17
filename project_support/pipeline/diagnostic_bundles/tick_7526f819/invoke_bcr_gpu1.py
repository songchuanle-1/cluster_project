"""Root explicit CLI operation, exclusive intent and bounded console capture."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,subprocess,sys
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
PACKET=ROOT/'pipeline/diagnostic_bundles/manual_gpu1_20261025/bcr_gpu1_operational_prepare'
TOKEN='7526f819f16e4f688566119d347cd198'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text('utf-8'))
def main():
 p=argparse.ArgumentParser();p.add_argument('operation',choices=['probe','prepare','stage','run','status','reconcile']);p.add_argument('--mode');p.add_argument('--target');p.add_argument('--request-id');p.add_argument('--label');a=p.parse_args()
 owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json');assert owner['token']==TOKEN and owner['thread_id']==os.environ.get('CODEX_THREAD_ID')=='01a159c5-29ab-7a22-ba7f-e79174757253'
 assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
 assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
 review=read(ROOT/'pipeline/diagnostic_bundles/manual_gpu1_20261025/bcr_gpu1_operational_final_review.json')
 assert review['status']=='STATIC_OPERATIONAL_BCR_PACKET_REVIEWED_NOT_NATIVE_PASS' and review['material_concerns']==[]
 assert sha(PACKET/'adapter_release.json')==sha(PACKET/'release_template.json')
 assert review['anchors']['outer_preparation']['sha256']==sha(PACKET/'preparation.json')
 cmd=[sys.executable,'-B','-X','utf8',str(PACKET/'adapter.py'),a.operation,'--execution-dir',str(HERE/'bcr_gpu1_execution')]
 if a.operation in ('probe','prepare'):cmd+=['--gpu','1']
 if a.mode:cmd+=['--mode',a.mode]
 if a.target:cmd+=['--target',a.target]
 if a.request_id:cmd+=['--request-id',a.request_id]
 label=a.label or '_'.join(x for x in [a.operation,a.mode,a.target] if x)
 assert label.replace('_','').isalnum();out=HERE/(label+'_console.json');err=HERE/(label+'_stderr.txt');intent=HERE/(label+'_cli_intent.json')
 assert not any(x.exists() for x in [out,err,intent]),'Existing operation console or intent: reconcile original request, never replay'
 with intent.open('x',encoding='utf-8') as f:json.dump({'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'command':cmd,'original_deadline':owner['deadline_at']},f,indent=2)
 with out.open('xb') as f,err.open('xb') as e:r=subprocess.run(cmd,stdout=f,stderr=e,timeout=980)
 print(json.dumps({'operation':label,'returncode':r.returncode,'console_path':str(out),'console_bytes':out.stat().st_size,'stderr_bytes':err.stat().st_size,'stderr_tail':err.read_text('utf-8',errors='replace')[-2200:] if r.returncode else ''}))
 if r.returncode:raise SystemExit(r.returncode)
if __name__=='__main__':main()
