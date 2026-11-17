"""Fresh owner binding only; preserve interrupted tick and its artifacts."""
from pathlib import Path
import ast,hashlib,json,os
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'tick_faccbed6'
EXPECTED={'token':'e2e3d058a5274d2db709c77a328b363f','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':'2026-10-26T08:09:05.798203+00:00','deadline_at':'2026-10-26T09:09:05.798203+00:00','context_sha256':'9d1fa21d142fcf5e866dc61276927dab5b9a765a4fe91e8a9ef82ba588ac79fc','pending_sha256':'d180dc399e23074bce692038582e11bd3c5a1298fb46a2638ccc78594fc84d99'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'));assert {k:owner.get(k) for k in EXPECTED}==EXPECTED and os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
 old={'token':'faccbed6c81949f48c88acbf67daf04e','generated_at':'2026-10-26T06:05:16.253788+00:00','deadline_at':'2026-10-26T07:05:16.253788+00:00','context_sha256':'1bfd5fd37311bef6c3633f6519945b766bb30e05273b38cb8db302d8c2724ea5','pending_sha256':'171a2cf1bf8138d0bd23a7f146ac91af2cc9616eb1983d2a02cbf06af8e56664'}
 data=(OLD/'anchor_bfc_packet.py').read_bytes()
 for k,before in old.items():assert data.count(before.encode())==1;data=data.replace(before.encode(),EXPECTED[k].encode())
 ast.parse(data)
 with (HERE/'anchor_bfc_packet.py').open('xb') as f:f.write(data)
 from anchor_bfc_packet import guard
 guard();items=[{'file':'anchor_bfc_packet.py','source_sha256':sha(OLD/'anchor_bfc_packet.py'),'current_sha256':sha(HERE/'anchor_bfc_packet.py'),'change':'Only current owner5 constants; old lease was canonically aborted, never extended.'}]
 for name in ['observe_cts_native_progress.py','verify_protected_assets.py']:
  data=(OLD/name).read_bytes();ast.parse(data)
  with (HERE/name).open('xb') as f:f.write(data)
  items.append({'file':name,'source_sha256':sha(OLD/name),'current_sha256':sha(HERE/name),'change':'Exact readonly byte copy; current guard/private output.'})
 with (HERE/'readonly_helpers_provenance.json').open('x',encoding='utf8') as f:json.dump(items,f,indent=2);f.write('\n')
 print(json.dumps({'current_owner_guard':True,'readonly_helpers':2,'GPU1_queried':False,'old_artifacts_preserved':True}))
if __name__=='__main__':main()
