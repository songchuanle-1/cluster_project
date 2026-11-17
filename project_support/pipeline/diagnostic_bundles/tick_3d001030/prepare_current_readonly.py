"""Fresh-owner binding of unchanged reviewed readonly helpers."""
from pathlib import Path
from datetime import datetime, timezone
import ast,hashlib,json,os
ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'tick_e2e3d058'
EXPECTED={'token':'3d001030cda04cddade0810e9d380a22','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':'2026-10-26T10:05:37.308291+00:00','deadline_at':'2026-10-26T11:05:37.308291+00:00','context_sha256':'58907261bcdd1c77799391926782c69573a4c401610de57381fa2571d5cae71d','pending_sha256':'bf6fc5e11ef8e1138972f47cb9bc8275838689ee8165547f194d4b0729abab0e'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 o=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'))
 assert {k:o.get(k) for k in EXPECTED}==EXPECTED and EXPECTED['thread_id']==os.environ.get('CODEX_THREAD_ID')
 assert datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED['deadline_at'])
 data=(OLD/'anchor_bfc_packet.py').read_bytes()
 old={'token':'e2e3d058a5274d2db709c77a328b363f','generated_at':'2026-10-26T08:09:05.798203+00:00','deadline_at':'2026-10-26T09:09:05.798203+00:00','context_sha256':'9d1fa21d142fcf5e866dc61276927dab5b9a765a4fe91e8a9ef82ba588ac79fc','pending_sha256':'d180dc399e23074bce692038582e11bd3c5a1298fb46a2638ccc78594fc84d99'}
 for k,value in old.items():
  assert data.count(value.encode())==1;data=data.replace(value.encode(),EXPECTED[k].encode())
 ast.parse(data)
 with (HERE/'anchor_bfc_packet.py').open('xb') as f:f.write(data)
 items=[{'file':'anchor_bfc_packet.py','source_sha256':sha(OLD/'anchor_bfc_packet.py'),'new_sha256':sha(HERE/'anchor_bfc_packet.py'),'changes':'Only current owner constants in new copy; no prior deadline extension.'}]
 for n in ['observe_cts_native_progress.py','verify_protected_assets.py']:
  data=(OLD/n).read_bytes();ast.parse(data)
  with (HERE/n).open('xb') as f:f.write(data)
  items.append({'file':n,'source_sha256':sha(OLD/n),'new_sha256':sha(HERE/n),'changes':'Byte-exact copy; current guard import and private result directory.'})
 with (HERE/'readonly_helpers_provenance.json').open('x',encoding='utf8') as f:json.dump(items,f,indent=2);f.write('\n')
 from anchor_bfc_packet import guard
 guard();print(json.dumps({'new_owner_bound':True,'files':len(items),'source_files_preserved':True}))
if __name__=='__main__':main()
