"""Root anchor of reviewed static BFC modules, never native evidence."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,sys,copy
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent;PACKET=ROOT/'pipeline/diagnostic_bundles/tick_64ac844e/bfc_operational_prepare';ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_ab7e46d4/bfc_native_prepare'
TOKEN='6bdbcf775b4b4239933ce966f98664d2';CID='hierarchy-parent-butterfly-token-composition';COMMIT='48fc302c3c02ffef0b241be3593c386b6b65a72e';SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
def read(p):return json.loads(Path(p).read_text('utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def guard():
 o=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json');e={'token':TOKEN,'thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':'2026-10-25T18:06:28.721162+00:00','deadline_at':'2026-10-25T19:06:28.721162+00:00','context_sha256':'723e5dea136798a6fc12574293a524f1df9859e17a0f4f57832076b58ff98d15','pending_sha256':'e4f95c6f88fa7e8b18770f03fda93e8ad143d3d863950df3b53332f1df8e53e3'}
 assert {k:o.get(k) for k in e}==e and read(ROOT/'pipeline/execution_mode.json')['target_thread_id']==os.environ['CODEX_THREAD_ID']==e['thread_id']
 assert read(ROOT/'pipeline/execution_mode.json')['mode']=='foreground' and datetime.now(timezone.utc)<datetime.fromisoformat(e['deadline_at'])
 assert sha(ROOT/'pipeline/headless/.tick_context.json')==e['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==e['pending_sha256']
 assert sha(ROOT/'pipeline/goal.json')=='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85' and sha(ROOT/'SERVERS.yaml')=='d5277972e80b6fe184a3e07f0fff34f7e1e7950b558d60905416ced302b206a2'
 assert sha(ROOT/'pipeline/authorizations/server4_gpu1_20261025.json')=='90f8820a60ef4d4e277904815b025658f7b8b457b0711a4d0ef5f7395fdd23f8'
 return o
if __name__=="__main__": raise SystemExit("READONLY_OWNER_GUARD_ONLY")
